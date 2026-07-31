# LG KR PAC (stand) unit support — notes

Developed against an **LG 휘센 2-in-1 FNQ161MK4W** (2016), which the ThinQ API reports as
`PAC_910604_KR`, `PlatformType.THINQ1`.

`git diff upstream/master..master` is the full inventory of what this fork changes, and
`git merge upstream/master` carries it onto a newer upstream.

## Branches

- **`master`** — what HACS installs. The patches plus one extra commit dropping
  `zip_release`/`filename` from `hacs.json`.
- **`fnq161-pac-support`** — the same patches with `hacs.json` untouched, kept clean for
  an upstream pull request.

Upstream ships `"zip_release": true`, so HACS looks for a `smartthinq_sensors.zip` asset
on a GitHub release. This fork cuts no releases and tracks its default branch instead, so
that key has to go or every download 404s.

## Installing via HACS

Add `dlxmax/ha-smartthinq-sensors` as a custom repository (category: integration). Because
`ollo69/ha-smartthinq-sensors` writes to the same `custom_components/smartthinq_sensors`
folder, remove that one **first** — HACS deletes the folder on remove, so a download that
fails leaves nothing behind. Back the folder up before starting.

HACS reports the installed version as a commit sha rather than a tag, since there are no
releases; a new commit on `master` shows up as an available update.

## Terminology, from LG's own model JSON

```json
myOwnParts.supportDevice = {"pac": "Stand", "rac": "Wall"}
```

**PAC = floor-standing indoor unit. RAC = wall-mounted indoor unit.** A 2-in-1 system has
one of each sharing a single outdoor unit; only the stand unit is network-connected.

## Why upstream exposes almost nothing on these units

1. **PowerSave was gated on RAC only.** Unmerged PR #739 uses
   `SUPPORT_POWER_SAVE = [SUPPORT_RAC_MODE, "@ENERGYSAVING"]`. On this unit
   `SupportRACMode` is `@NON`, while `SupportPACMode` is
   `@NON, @ENERGYSAVING, @AUTODRY, @ENERGYSAVINGDRY`. The gate now accepts either.

2. **Display light could never resolve a value.** `set_lighting_display()` walks
   `LIGHT_DISPLAY_*` looking for a label valid for the `DisplayControl` enum, but this
   unit's `DisplayControl` is plain `@OFF`/`@ON`, not `@RAC_LED_*` / `@AC_LED_*_W`, so the
   loop always fell through and raised. Plain fallbacks are appended **after** the LED
   labels, so other units are unaffected.

   `SupportLight` here is `@BRIGHTNESS_CONTROL`, which selects the **inverted** branch, and
   the plain enum is inverted too. **Confirmed on hardware: `DisplayControl = 0` turns the
   display light on.**

3. **`DisplayControl` is not in the Monitoring protocol** — it is write-only, so the status
   falls back to the last commanded value (`assumed_lighting_display`). The switch is
   therefore optimistic and will not track changes made with the IR remote.

   The commanded value is also written straight into `status.device_features`, because
   `device_features` only calls `_update_features()` **once per status object** — i.e. once
   per poll interval, which defaults to **300 s**. Without that, the switch sprang back to
   its old state for up to five minutes after every command.

## V1 control permission and error 0011

V1 (THINQ1) devices grant **control to one client at a time**. There is no explicit
acquire — sending `rti/rtiControl` takes the permission — and `rti/delControlPermission`
releases it. While a client holds it, every other client is refused with code `0011`.

The server's `returnMsg` for `0011` is a generic *"등록되지 않은 모델입니다"* (unregistered
model), which is misleading and sent this fork down a long dead end. LG's own client knows
better: the per-device app module (`appModuleUri` in the device info, a zip containing
`wrm/GAM/GAM.bundle.js`) maps the code to the dialog `@CP_UX30_USE_PRODUCT_WAIT` with the
device alias substituted in — *"«에어컨» is in use"* — and responds by calling
`removeControlPermission()`. The app takes the permission when its device page opens and
releases it on exit, so an app killed on that page leaves the device locked out
indefinitely. Reads are unaffected: monitoring needs no permission, which is why a device
in this state still reports state perfectly while every command fails.

Same bundle, worth knowing before reaching for it again: control dispatch is gated on
`isT20`, defined as `platformType === "thinq2"`. A THINQ1 device gets the same legacy
`rti/*` path this integration uses — there is no newer route to borrow.

Handling, mirroring the app:

- `0011` maps to `ControlPermissionError` via `API1_ERRORS`, checked before `API2_ERRORS`
  since the two namespaces reuse numbers for unrelated conditions.
- `Device._set_control` catches it, calls `delete_permission()` and retries once. The
  release payload is `{"deviceId": ...}` with no client identity, so it clears whatever
  permission is on the device, not only one owned by this session.
- The permission is held for `CONTROL_PERMISSION_GRACE` (60 s) after a command and
  released by the first poll after that. It used to be released on the *second poll*
  after a command, which at this fork's 300 s scan interval meant holding the device
  hostage for up to ten minutes — a side effect of raising the interval from upstream's
  30 s. Worst case is still bounded by one poll interval, since the release rides on a
  poll.

## Added

**Air conditioner**
- `MODE_POWER_SAVE` — `PowerSave` / 절전냉방운전 (power-saving *cooling*)
- `MODE_POWER_SAVE_DRY` — `PowerSaveDry` / 절전제습운전 (power-saving *dehumidify*)
- `MODE_ICE_VALLEY` — `IceValley` / 아이스쿨파워 (max-cooling boost)
- `MODE_AUTO_DRY` — `AutoDry`
- `MODE_FEEDBACK_SOUND` — `FeedbackSound` / 피드백 사운드 (button beep)
- `DIAGNOSIS` — `DiagCode`, the Smart Diagnosis result (72 codes, `00` = normal).
  `Config.audibleDiagnosis` is `false` on this model, i.e. Smart Diagnosis is delivered over
  the network, not by audio tone. Reads `no_data` until a diagnosis is actually run.
- `PowerSave` and `IceValley` are also surfaced as **mutually exclusive climate presets**
  (`eco` / `boost`) for units that expose no op-mode based presets, so they appear on the
  thermostat card rather than only as switches.

**Refrigerator** — `locked_state` and `active_saving_status` already existed upstream as
raw, unregistered properties; they are now registered as features rather than duplicated.
`smart_saving_mode_status` is new. All three are in the Monitoring protocol.

**Washer** — the tub-clean counter dropped to the literal string `"N/A"` whenever the
machine was powered off, and `reset_status()` then carried that placeholder forward
permanently, so it could never recover. The last real count is now retained instead.

That fix alone is in-memory only, so the count still reset on every Home Assistant
restart. `ThinQSensorEntityDescription` therefore gained an opt-in
`restore_last_value` flag, backed by `RestoreEntity`, and it is set on the tub-clean
counter. A sensor that opts in:

- restores its previous state on startup, ignoring `None` / `"N/A"` / `"-"` /
  `unavailable` / `unknown`, which carry no reading;
- never lets one of those placeholder states overwrite the retained value;
- stays `available` while it holds a value, so the count remains visible with the
  appliance powered off.

Every other sensor is untouched — the flag defaults to `False`.

## Capability detection caveat

The AC's model JSON is LG's generic **"Full ModelJson"** superset for all KR PAC units
(`Info.model = "Full ModelJson"`), not specific to the physical model. `_is_mode_supported`
therefore passes for almost anything, so the reliable gate is whether the device actually
*reports* a value. Every new status property returns `None` when the key is absent, which
makes unsupported features self-skip rather than producing dead entities.

On this unit that correctly suppresses `PowerSaveDry` and `FeedbackSound` while keeping
`PowerSave`, `IceValley` and `AutoDry`.

## Not available on this hardware

`SupportOpMode` is cool/dry/fan only; `SupportWindDir` is `FIX` (no swing);
`SupportWindMode` is `OFF` + `ICEVALLEY` only; `SupportTempCtrl` is `@1_0UNIT_CONTROL`,
confirming 1 °C setpoint granularity in firmware. There is **no tropical-night (열대야)**
mode anywhere in the model JSON.

`FeedbackSound` has no `Set` action in `ControlWifi` — the only sound setter is
`SetSpkVolume`, which is not monitored and drives voice guidance rather than the button
beep. The switch is wired up regardless, since THINQ1 sends control commands as a plain
`{key: value}` pair and does not need a named action. **This unit never reports
`FeedbackSound`, so the entity self-skips and beep control is genuinely unavailable here.**
