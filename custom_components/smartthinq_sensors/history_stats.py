"""Chart LG's server side appliance history in Home Assistant.

The fridge only ever reports what it is doing right now, but LG keeps a few
weeks of daily totals: how often the doors were opened, how long they stood
open and how many times the compressor had to run at full power.

Each series gets a sensor on the device, so it shows up where the rest of the
appliance does. How the history behind that sensor is stored depends on how LG
publishes it, and the two cases are genuinely different:

* The door figures are live. LG's newest row is today's, and it grows as the
  day goes on, so the sensor is a real running total and carries a state class.
  Home Assistant's recorder builds its statistics from then on; all we do is
  backfill, once, the weeks that happened before the sensor existed.
* The cooling figures lag. Today never appears at all, and yesterday's total is
  still being revised, so the sensor cannot claim to be measuring anything right
  now. Recorder statistics would file the wrong day, so its history is kept as
  an external series that we own outright and rewrite on every pass.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
import logging
from typing import Any

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.models import (
    StatisticData,
    StatisticMeanType,
    StatisticMetaData,
)
from homeassistant.components.recorder.statistics import (
    async_add_external_statistics,
    async_import_statistics,
    get_last_statistics,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util, slugify

from .const import DOMAIN, LGE_DEVICES
from .wideq import DeviceType

_LOGGER = logging.getLogger(__name__)

# LG holds about a month of daily door figures and a week of cooling ones.
HISTORY_DAYS = 30
# Two API calls a shot, so this can run often enough that the "today" figures
# stay worth looking at without ever approaching a rate limit.
UPDATE_INTERVAL = timedelta(hours=2)
# async_import_statistics only accepts statistics owned by the recorder.
RECORDER_DOMAIN = "recorder"

SERVICE_UPDATE_HISTORY = "update_history"

ATTR_DOOR_OPENINGS = "door_openings"
ATTR_DOOR_OPEN_TIME = "door_open_time"
ATTR_MAX_COOLING_RUNS = "max_cooling_runs"


@dataclass(frozen=True)
class HistorySeries:
    """One daily series LG keeps and we chart."""

    key: str
    unit: str | None
    # Where to find it in the payload, and what to multiply the raw value by.
    date_key: str
    value_key: str
    scale: float = 1.0
    # True when LG's newest row is today's and still climbing, which is what
    # lets the matching sensor carry a state class and be recorded normally.
    live: bool = True


DOOR_SERIES = (
    HistorySeries(ATTR_DOOR_OPENINGS, None, "month", "openCount"),
    # LG reports the daily total in milliseconds.
    HistorySeries(
        ATTR_DOOR_OPEN_TIME, UnitOfTime.MINUTES, "month", "openTime", 1 / 60000
    ),
)
COOLING_SERIES = HistorySeries(
    ATTR_MAX_COOLING_RUNS, None, "date", "value", live=False
)
ALL_KEYS = (ATTR_DOOR_OPENINGS, ATTR_DOOR_OPEN_TIME, ATTR_MAX_COOLING_RUNS)


def _as_date(value: Any) -> date | None:
    """Read the several date shapes LG uses across these endpoints."""
    text = str(value or "").strip()
    for fmt in ("%Y%m%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _points(items: list, series: HistorySeries) -> list[tuple[date, float]]:
    """Turn one LG history payload into sorted (day, value) pairs."""
    found: dict[date, float] = {}
    for item in items or []:
        if not isinstance(item, dict):
            continue
        if (day := _as_date(item.get(series.date_key))) is None:
            continue
        try:
            found[day] = float(item[series.value_key]) * series.scale
        except (KeyError, TypeError, ValueError):
            continue
    return sorted(found.items())


def _summary(points: list[tuple[date, float]]) -> dict:
    """Describe the newest day against the ones before it."""
    day, value = points[-1]
    summary = {"value": round(value, 2), "date": day.isoformat()}
    if prior := [val for _, val in points[:-1]]:
        summary["previous_day"] = round(prior[-1], 2)
        summary["average"] = round(sum(prior) / len(prior), 2)
        summary["highest"] = round(max(prior + [value]), 2)
    return summary


def _last_day(row: dict) -> date | None:
    """Return the local day a statistics row belongs to."""
    start = row.get("start")
    if isinstance(start, (int, float)):
        start = dt_util.utc_from_timestamp(start)
    if not isinstance(start, datetime):
        return None
    return dt_util.as_local(start).date()


async def _async_last_row(hass: HomeAssistant, statistic_id: str) -> dict | None:
    """Return the newest stored row of one series, if it has any."""
    stored = await get_instance(hass).async_add_executor_job(
        get_last_statistics, hass, 1, statistic_id, True, {"state", "sum"}
    )
    if rows := stored.get(statistic_id):
        return rows[0]
    return None


def _rows(points: list[tuple[date, float]], base: float) -> list[StatisticData]:
    """Lay daily values out as statistics rows on a running total."""
    total = base
    stats: list[StatisticData] = []
    for day, value in points:
        total += value
        stats.append(
            StatisticData(
                start=dt_util.start_of_local_day(day), state=value, sum=total
            )
        )
    return stats


def _metadata(
    statistic_id: str, unit: str | None, source: str, name: str | None
) -> StatisticMetaData:
    """Describe one daily series to the recorder."""
    return StatisticMetaData(
        mean_type=StatisticMeanType.NONE,
        has_sum=True,
        name=name,
        source=source,
        statistic_id=statistic_id,
        unit_class=None,
        unit_of_measurement=unit,
    )


async def _async_backfill(
    hass: HomeAssistant,
    entity_id: str,
    unit: str | None,
    points: list[tuple[date, float]],
) -> int:
    """Give a live sensor the weeks that happened before it existed.

    Only ever runs against an empty series. Once the sensor has a state class
    the recorder owns its statistics, and writing over the top of what it
    compiles would leave two different ideas of the running total.
    """
    today = dt_util.now().date()
    # Today is still climbing and belongs to the recorder, not to us.
    complete = [(day, value) for day, value in points if day < today]
    if not complete:
        return 0

    if await _async_last_row(hass, entity_id) is not None:
        return 0

    stats = _rows(complete, 0.0)
    async_import_statistics(
        hass, _metadata(entity_id, unit, RECORDER_DOMAIN, None), stats
    )
    _LOGGER.debug("Backfilled %s days of history into %s", len(stats), entity_id)
    return len(stats)


async def _async_store_external(
    hass: HomeAssistant,
    statistic_id: str,
    name: str | None,
    unit: str | None,
    points: list[tuple[date, float]],
) -> int:
    """Keep a series LG reports late, which no sensor can be recorded for."""
    if not points:
        return 0

    base = 0.0
    from_day: date | None = None
    if row := await _async_last_row(hass, statistic_id):
        # Rewrite the newest stored day rather than skipping past it: LG goes on
        # revising a day's total well into the day after.
        if (from_day := _last_day(row)) is not None:
            base = (row.get("sum") or 0.0) - (row.get("state") or 0.0)

    fresh = [
        (day, value)
        for day, value in points
        if from_day is None or day >= from_day
    ]
    if not fresh:
        return 0

    async_add_external_statistics(
        hass, _metadata(statistic_id, unit, DOMAIN, name), _rows(fresh, base)
    )
    return len(fresh)


def _entity_id(hass: HomeAssistant, api: Any, key: str) -> str | None:
    """Find the sensor that carries one series, if it has been created yet."""
    return er.async_get(hass).async_get_entity_id(
        "sensor", DOMAIN, f"{api.unique_id}-{key}"
    )


def _external_id(hass: HomeAssistant, api: Any, key: str) -> tuple[str, str | None]:
    """Name the external series that shadows one sensor, and label it."""
    if entity_id := _entity_id(hass, api, key):
        slug = entity_id.split(".", 1)[1]
        state = hass.states.get(entity_id)
        return f"{DOMAIN}:{slug}", state.name if state else None
    return f"{DOMAIN}:{slugify(api.name)}_{key}", None


async def async_update_history(hass: HomeAssistant, api: Any) -> None:
    """Pull LG's daily history for one fridge into its sensors and charts."""
    device = api.device
    end = dt_util.now().date()
    start = end - timedelta(days=HISTORY_DAYS)

    payloads: list[tuple[HistorySeries, list]] = []
    try:
        cooling = await device.get_active_cooling_history()
    except Exception as exc:  # noqa: BLE001 - a chart is never worth an error
        _LOGGER.warning("Active cooling history unavailable: %s", exc)
    else:
        payloads.append((COOLING_SERIES, cooling))

    try:
        doors = await device.get_door_history(
            start.strftime("%Y%m%d"), end.strftime("%Y%m%d")
        )
    except Exception as exc:  # noqa: BLE001
        _LOGGER.warning("Door history unavailable: %s", exc)
    else:
        payloads.extend((series, doors) for series in DOOR_SERIES)

    totals: dict[str, dict] = {}
    for series, payload in payloads:
        if not (points := _points(payload, series)):
            continue
        totals[series.key] = _summary(points)

        if not series.live:
            statistic_id, name = _external_id(hass, api, series.key)
            await _async_store_external(
                hass, statistic_id, name, series.unit, points
            )
        elif entity_id := _entity_id(hass, api, series.key):
            await _async_backfill(hass, entity_id, series.unit, points)
        else:
            _LOGGER.debug("No sensor yet for %s, charting it next time", series.key)

    if totals:
        device.set_history(totals)
        # Locally computed totals, not the echo of a command: nothing for the
        # appliance to confirm, so do not trigger the post-command polls.
        api.async_set_updated(poll_after=False)


@callback
def _async_drop_stale(hass: HomeAssistant, api: Any) -> None:
    """Clear statistics left behind by earlier shapes of this code.

    Two rounds of them: an external series keyed on LG's own alias, and a
    recorder series under the cooling sensor, which Home Assistant rightly
    complains about now that the sensor has no state class to compile from.
    """
    stale = [f"{DOMAIN}:{slugify(api.name)}_{key}" for key in ALL_KEYS]
    if entity_id := _entity_id(hass, api, ATTR_MAX_COOLING_RUNS):
        stale.append(entity_id)
    get_instance(hass).async_clear_statistics(stale)


def _fridges(hass: HomeAssistant) -> list:
    """Return the fridges currently set up."""
    devices = hass.data.get(DOMAIN, {}).get(LGE_DEVICES) or {}
    return devices.get(DeviceType.REFRIGERATOR, [])


@callback
def async_setup_history(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Keep the history sensors fed, on a timer and on demand."""

    async def _refresh(_now=None) -> None:
        for api in _fridges(hass):
            await async_update_history(hass, api)

    async def _first_run() -> None:
        for api in _fridges(hass):
            _async_drop_stale(hass, api)
        await _refresh()

    entry.async_on_unload(
        async_track_time_interval(hass, _refresh, UPDATE_INTERVAL)
    )

    async def _handle_service(_call: ServiceCall) -> None:
        await _refresh()

    hass.services.async_register(DOMAIN, SERVICE_UPDATE_HISTORY, _handle_service)

    hass.async_create_task(_first_run())
