"""Constants for LGE ThinQ custom component."""

__version__ = "0.43.0"
PROJECT_URL = "https://github.com/ollo69/ha-smartthinq-sensors/"
ISSUE_URL = f"{PROJECT_URL}issues"

DOMAIN = "smartthinq_sensors"

MIN_HA_MAJ_VER = 2025
MIN_HA_MIN_VER = 7
__min_ha_version__ = f"{MIN_HA_MAJ_VER}.{MIN_HA_MIN_VER}.0"

# general sensor attributes
ATTR_CURRENT_COURSE = "current_course"
ATTR_ERROR_STATE = "error_state"
ATTR_INITIAL_TIME = "initial_time"
ATTR_REMAIN_TIME = "remain_time"
ATTR_RESERVE_TIME = "reserve_time"
ATTR_START_TIME = "start_time"
ATTR_END_TIME = "end_time"
ATTR_RUN_COMPLETED = "run_completed"

# refrigerator sensor attributes
ATTR_DOOR_OPEN = "door_open"
ATTR_FRIDGE_TEMP = "fridge_temp"
ATTR_FREEZER_TEMP = "freezer_temp"
ATTR_TEMP_UNIT = "temp_unit"

# range sensor attributes
ATTR_OVEN_LOWER_TARGET_TEMP = "oven_lower_target_temp"
ATTR_OVEN_UPPER_TARGET_TEMP = "oven_upper_target_temp"
ATTR_OVEN_TEMP_UNIT = "oven_temp_unit"

# configuration
CONF_LANGUAGE = "language"
CONF_OAUTH2_URL = "oauth2_url"
CONF_USE_API_V2 = "use_api_v2"
CONF_USE_HA_SESSION = "use_ha_session"
CONF_USE_REDIRECT = "use_redirect"

# Polling interval (seconds) - user-adjustable via OptionsFlow / number entity.
# LG cloud blocks accounts that poll too aggressively. Default raised from
# the original hardcoded 30 s to 300 s (5 min) so fresh installs and existing
# users without an explicit override avoid the ban.
CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_SCAN_INTERVAL = 300
MIN_SCAN_INTERVAL = 30
MAX_SCAN_INTERVAL = 3600

# After a control command the ThinQ app does not trust the echoed state: it
# calls setMonitoringInterval(deviceId, 5000, 5), i.e. five extra polls 5 s
# apart, and only then falls back to its normal cadence. Do the same, so a
# command's real outcome shows up in ~25 s instead of after a whole
# DEFAULT_SCAN_INTERVAL. V1 (THINQ1) only, where a poll reuses the cached
# work_id and costs a single request.
POST_COMMAND_POLL_INTERVAL = 5
POST_COMMAND_POLL_COUNT = 5
# First poll after a command. The app fires its first setMonitoringInterval poll
# at one interval (5 s), so match it: a mode change recalls the appliance's own
# per-mode setpoint and fan speed, and at 5 s that shows up in the UI in seconds
# instead of the ~20-40 s an earlier 20 s delay cost. A poll cannot collide with
# the next command - the confirm poll skips while session_busy and set_control
# holds _session_lock - so the longer gap that guarded against that is not
# needed. The poll that lands before the appliance has settled just reads the
# pre-command value; a later poll in the same burst corrects it (the app shows
# the same brief flicker), so no suppression is wanted.
POST_COMMAND_POLL_FIRST_DELAY = 5

# The LG PAC wifi module drops off the network for ~30 s at a time, on its own,
# several times an hour (see the AirPort investigation: it is the module, not
# the AP, and there is no fix on the network side). A poll that lands in one of
# those windows fails, and at a 300 s scan interval that costs five minutes of
# stale instant power - which is the input the aircon miser regulates on.
# So retry a failed poll on a short interval instead of waiting out the scan
# interval. A failed attempt never advances the additional-poll clock, so these
# retries do not spend the 300 s power-read budget; only a read that returned
# data does. Retries are bounded, and the allowance is only restored by a poll
# that succeeds, so an appliance that is simply off or unplugged settles back to
# the normal cadence instead of retrying forever.
FAILED_POLL_RETRY_INTERVAL = 30
FAILED_POLL_RETRY_COUNT = 4

CLIENT = "client"
LGE_DEVICES = "lge_devices"

LGE_DISCOVERY_NEW = f"{DOMAIN}_discovery_new"

DEFAULT_ICON = "def_icon"
DEFAULT_SENSOR = "default"

STARTUP = f"""
-------------------------------------------------------------------
{DOMAIN}
Version: {__version__}
This is a custom component
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""
