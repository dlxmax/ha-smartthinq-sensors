#!/usr/bin/env python3
"""Consolidated smartthinq_sensors patches for LG KR PAC stand units (FNQ161MK4W).

Usage: apply_all.py <path-to-custom_components/smartthinq_sensors>

Idempotent, and converges either pristine upstream OR an already-partially-patched
tree to the same final state.
"""
import os, sys, py_compile

ROOT = sys.argv[1].rstrip("/")
CONST = os.path.join(ROOT, "wideq", "const.py")
AC = os.path.join(ROOT, "wideq", "devices", "ac.py")
REF = os.path.join(ROOT, "wideq", "devices", "refrigerator.py")
SWITCH = os.path.join(ROOT, "switch.py")
SENSOR = os.path.join(ROOT, "sensor.py")
CLIMATE = os.path.join(ROOT, "climate.py")

E = []          # (path, old, new, optional)
def edit(p, o, n, optional=False): E.append((p, o, n, optional))

# ============================ const.py ============================
edit(CONST,
     '    MODE_AIRCLEAN = "mode_airclean"\n',
     '    MODE_AIRCLEAN = "mode_airclean"\n'
     '    MODE_POWER_SAVE = "mode_power_save"\n'
     '    MODE_POWER_SAVE_DRY = "mode_power_save_dry"\n'
     '    MODE_ICE_VALLEY = "mode_ice_valley"\n'
     '    MODE_AUTO_DRY = "mode_auto_dry"\n'
     '    MODE_FEEDBACK_SOUND = "mode_feedback_sound"\n'
     '    DIAGNOSIS = "diagnosis"\n')

edit(CONST,
     '    ECOFRIENDLY = "eco_friendly"\n',
     '    ACTIVESAVINGSTATUS = "active_saving_status"\n'
     '    ECOFRIENDLY = "eco_friendly"\n'
     '    LOCKINGSTATUS = "locking_status"\n'
     '    SMARTSAVINGMODESTATUS = "smart_saving_mode_status"\n')

# ============================ ac.py: constants ============================
edit(AC,
     'SUPPORT_AIRCLEAN = [SUPPORT_RAC_MODE, "@AIRCLEAN"]\n',
     'SUPPORT_AIRCLEAN = [SUPPORT_RAC_MODE, "@AIRCLEAN"]\n'
     'SUPPORT_POWER_SAVE = [SUPPORT_PAC_MODE, "@ENERGYSAVING"]\n'
     'SUPPORT_POWER_SAVE_RAC = [SUPPORT_RAC_MODE, "@ENERGYSAVING"]\n'
     'SUPPORT_WIND_MODE = ["SupportWindMode", "support.windMode"]\n'
     'SUPPORT_POWER_SAVE_DRY = [SUPPORT_PAC_MODE, "@ENERGYSAVINGDRY"]\n'
     'SUPPORT_AUTO_DRY = [SUPPORT_PAC_MODE, "@AUTODRY"]\n'
     'SUPPORT_ICE_VALLEY = [SUPPORT_WIND_MODE, "@AC_MAIN_WIND_MODE_ICEVALLEY_W"]\n')

edit(AC,
     'STATE_MODE_AIRCLEAN = ["AirClean", "airState.wMode.airClean"]\n',
     'STATE_MODE_AIRCLEAN = ["AirClean", "airState.wMode.airClean"]\n'
     'STATE_MODE_POWER_SAVE = ["PowerSave", "airState.powerSave.basic"]\n'
     'STATE_MODE_POWER_SAVE_DRY = ["PowerSaveDry", "airState.powerSave.dry"]\n'
     'STATE_MODE_ICE_VALLEY = ["IceValley", "airState.wMode.iceValley"]\n'
     'STATE_MODE_AUTO_DRY = ["AutoDry", "airState.miscFuncState.autoDry"]\n'
     'STATE_MODE_FEEDBACK_SOUND = ["FeedbackSound", "airState.miscFuncState.feedbackSound"]\n'
     'STATE_DIAG_CODE = ["DiagCode", "airState.diagCode"]\n')

edit(AC,
     'CMD_STATE_MODE_AIRCLEAN = [CTRL_BASIC, "Set", STATE_MODE_AIRCLEAN]\n',
     'CMD_STATE_MODE_AIRCLEAN = [CTRL_BASIC, "Set", STATE_MODE_AIRCLEAN]\n'
     'CMD_STATE_MODE_POWER_SAVE = [CTRL_BASIC, "Set", STATE_MODE_POWER_SAVE]\n'
     'CMD_STATE_MODE_POWER_SAVE_DRY = [CTRL_BASIC, "Set", STATE_MODE_POWER_SAVE_DRY]\n'
     'CMD_STATE_MODE_ICE_VALLEY = [CTRL_BASIC, "Set", STATE_MODE_ICE_VALLEY]\n'
     'CMD_STATE_MODE_AUTO_DRY = [CTRL_BASIC, "Set", STATE_MODE_AUTO_DRY]\n'
     'CMD_STATE_MODE_FEEDBACK_SOUND = [CTRL_BASIC, "Set", STATE_MODE_FEEDBACK_SOUND]\n')

# --- display-light labels. Units whose SupportLight is @BRIGHTNESS_CONTROL take the
# --- INV branch, and on those the plain @OFF/@ON enum is inverted too (verified on
# --- PAC_910604_KR: selecting "on" with the straight mapping turned the display off).
LIGHT_TARGET = (
    'LIGHT_DISPLAY_OFF = ["@RAC_LED_OFF", "@AC_LED_OFF_W", "@OFF"]\n'
    'LIGHT_DISPLAY_ON = ["@RAC_LED_ON", "@AC_LED_ON_W", "@ON"]\n'
    'LIGHT_DISPLAY_INV_OFF = ["@RAC_LED_ON", "@AC_LED_OFF_W", "@ON"]\n'
    'LIGHT_DISPLAY_INV_ON = ["@RAC_LED_OFF", "@AC_LED_ON_W", "@OFF"]\n')
edit(AC,  # pristine upstream
     'LIGHT_DISPLAY_OFF = ["@RAC_LED_OFF", "@AC_LED_OFF_W"]\n'
     'LIGHT_DISPLAY_ON = ["@RAC_LED_ON", "@AC_LED_ON_W"]\n'
     'LIGHT_DISPLAY_INV_OFF = ["@RAC_LED_ON", "@AC_LED_OFF_W"]\n'
     'LIGHT_DISPLAY_INV_ON = ["@RAC_LED_OFF", "@AC_LED_ON_W"]\n',
     LIGHT_TARGET)
# ============================ ac.py: capability probes ============================
edit(AC,
     '    @cached_property\n'
     '    def is_mode_airclean_supported(self):\n'
     '        """Return if AirClean mode is supported."""\n'
     '        return self._is_mode_supported(SUPPORT_AIRCLEAN)\n',
     '    @cached_property\n'
     '    def is_mode_airclean_supported(self):\n'
     '        """Return if AirClean mode is supported."""\n'
     '        return self._is_mode_supported(SUPPORT_AIRCLEAN)\n'
     '\n'
     '    @cached_property\n'
     '    def is_mode_power_save_supported(self):\n'
     '        """Return if PowerSave (energy saving) mode is supported."""\n'
     '        return bool(\n'
     '            self._is_mode_supported(SUPPORT_POWER_SAVE)\n'
     '            or self._is_mode_supported(SUPPORT_POWER_SAVE_RAC)\n'
     '        )\n'
     '\n'
     '    @cached_property\n'
     '    def is_mode_power_save_dry_supported(self):\n'
     '        """Return if PowerSaveDry mode is supported."""\n'
     '        return bool(self._is_mode_supported(SUPPORT_POWER_SAVE_DRY))\n'
     '\n'
     '    @cached_property\n'
     '    def is_mode_ice_valley_supported(self):\n'
     '        """Return if IceValley (ice cool power) mode is supported."""\n'
     '        return bool(self._is_mode_supported(SUPPORT_ICE_VALLEY))\n'
     '\n'
     '    @cached_property\n'
     '    def is_mode_auto_dry_supported(self):\n'
     '        """Return if AutoDry mode is supported."""\n'
     '        return bool(self._is_mode_supported(SUPPORT_AUTO_DRY))\n')

# ============================ ac.py: setters ============================
edit(AC,
     '        keys = self._get_cmd_keys(CMD_STATE_MODE_AIRCLEAN)\n'
     '        mode_key = MODE_AIRCLEAN_ON if status else MODE_AIRCLEAN_OFF\n'
     '        mode = self.model_info.enum_value(keys[2], mode_key)\n'
     '        await self.set(keys[0], keys[1], key=keys[2], value=mode)\n',
     '        keys = self._get_cmd_keys(CMD_STATE_MODE_AIRCLEAN)\n'
     '        mode_key = MODE_AIRCLEAN_ON if status else MODE_AIRCLEAN_OFF\n'
     '        mode = self.model_info.enum_value(keys[2], mode_key)\n'
     '        await self.set(keys[0], keys[1], key=keys[2], value=mode)\n'
     '\n'
     '    async def _set_simple_mode(self, cmd_keys, status: bool):\n'
     '        """Set a plain @OFF/@ON mode on or off."""\n'
     '        keys = self._get_cmd_keys(cmd_keys)\n'
     '        mode_key = MODE_ON if status else MODE_OFF\n'
     '        mode = self.model_info.enum_value(keys[2], mode_key)\n'
     '        await self.set(keys[0], keys[1], key=keys[2], value=mode)\n'
     '\n'
     '    async def set_mode_power_save(self, status: bool):\n'
     '        """Set the PowerSave (energy saving) mode on or off."""\n'
     '        if not self.is_mode_power_save_supported:\n'
     '            raise ValueError("PowerSave mode not supported")\n'
     '        await self._set_simple_mode(CMD_STATE_MODE_POWER_SAVE, status)\n'
     '\n'
     '    async def set_mode_power_save_dry(self, status: bool):\n'
     '        """Set the PowerSaveDry mode on or off."""\n'
     '        if not self.is_mode_power_save_dry_supported:\n'
     '            raise ValueError("PowerSaveDry mode not supported")\n'
     '        await self._set_simple_mode(CMD_STATE_MODE_POWER_SAVE_DRY, status)\n'
     '\n'
     '    async def set_mode_ice_valley(self, status: bool):\n'
     '        """Set the IceValley mode on or off."""\n'
     '        if not self.is_mode_ice_valley_supported:\n'
     '            raise ValueError("IceValley mode not supported")\n'
     '        await self._set_simple_mode(CMD_STATE_MODE_ICE_VALLEY, status)\n'
     '\n'
     '    async def set_mode_auto_dry(self, status: bool):\n'
     '        """Set the AutoDry mode on or off."""\n'
     '        if not self.is_mode_auto_dry_supported:\n'
     '            raise ValueError("AutoDry mode not supported")\n'
     '        await self._set_simple_mode(CMD_STATE_MODE_AUTO_DRY, status)\n'
     '\n'
     '    async def set_mode_feedback_sound(self, status: bool):\n'
     '        """Set the feedback sound (button beep) on or off.\n'
     '\n'
     '        There is no SetFeedbackSound action in ControlWifi, but THINQ1 control\n'
     '        commands are sent as a plain {key: value} pair, so the write is still\n'
     '        attempted; FeedbackSound is in the Monitoring protocol so the next poll\n'
     '        shows whether the unit honoured it.\n'
     '        """\n'
     '        await self._set_simple_mode(CMD_STATE_MODE_FEEDBACK_SOUND, status)\n')

# ============================ ac.py: optimistic display light ============================
edit(AC,
     '        if lighting is None:\n'
     '            raise ValueError("Not possible to determinate a valid light mode")\n'
     '        await self.set(keys[0], keys[1], key=keys[2], value=lighting)\n',
     '        if lighting is None:\n'
     '            raise ValueError("Not possible to determinate a valid light mode")\n'
     '        await self.set(keys[0], keys[1], key=keys[2], value=lighting)\n'
     '        # Some units accept SetDisplayControl but never report DisplayControl back,\n'
     '        # so remember what we asked for and reflect it straight away: features are\n'
     '        # only recomputed once per status object, i.e. once per poll interval.\n'
     '        self.assumed_lighting_display = status\n'
     '        if self._status is not None:\n'
     '            self._status.device_features[\n'
     '                AirConditionerFeatures.LIGHTING_DISPLAY\n'
     '            ] = status\n')

edit(AC,
     '        key = self._get_state_key(STATE_LIGHTING_DISPLAY)\n'
     '        if (value := self.lookup_enum(key, True)) is None:\n'
     '            return None\n'
     '        return self._update_feature(\n'
     '            AirConditionerFeatures.LIGHTING_DISPLAY, value in supp_modes[MODE_ON], False\n'
     '        )\n',
     '        key = self._get_state_key(STATE_LIGHTING_DISPLAY)\n'
     '        if not (value := self.lookup_enum(key, True)):\n'
     '            # Write-only on some units: fall back to the last commanded value.\n'
     '            return self._update_feature(\n'
     '                AirConditionerFeatures.LIGHTING_DISPLAY,\n'
     '                getattr(self._device, "assumed_lighting_display", False),\n'
     '                False,\n'
     '            )\n'
     '        return self._update_feature(\n'
     '            AirConditionerFeatures.LIGHTING_DISPLAY, value in supp_modes[MODE_ON], False\n'
     '        )\n')
# ============================ ac.py: status properties ============================
edit(AC,
     '        status = value == MODE_AIRCLEAN_ON\n'
     '        return self._update_feature(AirConditionerFeatures.MODE_AIRCLEAN, status, False)\n',
     '        status = value == MODE_AIRCLEAN_ON\n'
     '        return self._update_feature(AirConditionerFeatures.MODE_AIRCLEAN, status, False)\n'
     '\n'
     '    def _simple_mode_status(self, supported, state_key, feature):\n'
     '        """Return status for a plain @OFF/@ON mode, or None if not reported."""\n'
     '        if not supported:\n'
     '            return None\n'
     '        key = self._get_state_key(state_key)\n'
     '        if (value := self.lookup_enum(key, True)) is None:\n'
     '            return None\n'
     '        return self._update_feature(feature, value == MODE_ON, False)\n'
     '\n'
     '    @property\n'
     '    def mode_power_save(self):\n'
     '        """Return PowerSave (energy saving) mode status."""\n'
     '        return self._simple_mode_status(\n'
     '            self._device.is_mode_power_save_supported,\n'
     '            STATE_MODE_POWER_SAVE,\n'
     '            AirConditionerFeatures.MODE_POWER_SAVE,\n'
     '        )\n'
     '\n'
     '    @property\n'
     '    def mode_power_save_dry(self):\n'
     '        """Return PowerSaveDry mode status."""\n'
     '        return self._simple_mode_status(\n'
     '            self._device.is_mode_power_save_dry_supported,\n'
     '            STATE_MODE_POWER_SAVE_DRY,\n'
     '            AirConditionerFeatures.MODE_POWER_SAVE_DRY,\n'
     '        )\n'
     '\n'
     '    @property\n'
     '    def mode_ice_valley(self):\n'
     '        """Return IceValley mode status."""\n'
     '        return self._simple_mode_status(\n'
     '            self._device.is_mode_ice_valley_supported,\n'
     '            STATE_MODE_ICE_VALLEY,\n'
     '            AirConditionerFeatures.MODE_ICE_VALLEY,\n'
     '        )\n'
     '\n'
     '    @property\n'
     '    def mode_auto_dry(self):\n'
     '        """Return AutoDry mode status."""\n'
     '        return self._simple_mode_status(\n'
     '            self._device.is_mode_auto_dry_supported,\n'
     '            STATE_MODE_AUTO_DRY,\n'
     '            AirConditionerFeatures.MODE_AUTO_DRY,\n'
     '        )\n'
     '\n'
     '    @property\n'
     '    def mode_feedback_sound(self):\n'
     '        """Return feedback sound (button beep) status."""\n'
     '        return self._simple_mode_status(\n'
     '            True,\n'
     '            STATE_MODE_FEEDBACK_SOUND,\n'
     '            AirConditionerFeatures.MODE_FEEDBACK_SOUND,\n'
     '        )\n'
     '\n'
     '    @property\n'
     '    def diagnosis(self):\n'
     '        """Return the smart-diagnosis result reported over the network."""\n'
     '        key = self._get_state_key(STATE_DIAG_CODE)\n'
     '        if (value := self.lookup_enum(key, True)) is None:\n'
     '            return None\n'
     '        if not value:\n'
     '            status = "no_data"\n'
     '        elif value.endswith("_NORMAL_S"):\n'
     '            status = "normal"\n'
     '        else:\n'
     '            status = (\n'
     '                value.replace("@AC_SMART_DIAGNOSIS_RESULT_", "")\n'
     '                .rstrip("S")\n'
     '                .rstrip("_")\n'
     '                .lower()\n'
     '            ) or "no_data"\n'
     '        return self._update_feature(AirConditionerFeatures.DIAGNOSIS, status, False)\n')

edit(AC,
     '            self.mode_airclean,\n',
     '            self.mode_airclean,\n'
     '            self.mode_power_save,\n'
     '            self.mode_power_save_dry,\n'
     '            self.mode_ice_valley,\n'
     '            self.mode_auto_dry,\n'
     '            self.mode_feedback_sound,\n'
     '            self.diagnosis,\n')

# ============================ refrigerator.py ============================
# Upstream already has locked_state and active_saving_status as raw, unregistered
# properties; register them as features rather than adding duplicates.
edit(REF,
     "    @property\n"
     "    def locked_state(self):\n"
     '        """Return current locked state."""\n'
     '        state = self.lookup_enum("LockingStatus")\n'
     "        if not state:\n"
     "            return StateOptions.NONE\n"
     "        return self._device.get_enum_text(state)\n"
     "\n"
     "    @property\n"
     "    def active_saving_status(self):\n"
     '        """Return current active saving status."""\n'
     '        return self._data.get("ActiveSavingStatus", "N/A")\n'
     "\n"
     "    def _update_features(self):\n"
     "        _ = [\n"
     "            self.eco_friendly_state,\n",

     "    @property\n"
     "    def locked_state(self):\n"
     '        """Return current locked state."""\n'
     '        key = "LockingStatus"\n'
     "        state = self.lookup_enum(key)\n"
     "        if not state:\n"
     "            return StateOptions.NONE\n"
     "        return self._update_feature(\n"
     "            RefrigeratorFeatures.LOCKINGSTATUS,\n"
     "            self._device.get_enum_text(state),\n"
     "            False,\n"
     "            key,\n"
     "        )\n"
     "\n"
     "    @property\n"
     "    def active_saving_status(self):\n"
     '        """Return current active saving status."""\n'
     '        key = "ActiveSavingStatus"\n'
     "        if (status := self._data.get(key)) is None:\n"
     "            return None\n"
     "        return self._update_feature(\n"
     "            RefrigeratorFeatures.ACTIVESAVINGSTATUS, status, False, key\n"
     "        )\n"
     "\n"
     "    @property\n"
     "    def smart_saving_mode_status(self):\n"
     '        """Return whether smart saving is currently active."""\n'
     '        key = "smartSavingModeStatus" if self.is_info_v2 else "SmartSavingModeStatus"\n'
     "        if not (status := self.lookup_enum(key)):\n"
     "            return None\n"
     "        return self._update_feature(\n"
     "            RefrigeratorFeatures.SMARTSAVINGMODESTATUS,\n"
     "            self._device.get_enum_text(status),\n"
     "            False,\n"
     "            key,\n"
     "        )\n"
     "\n"
     "    def _update_features(self):\n"
     "        _ = [\n"
     "            self.eco_friendly_state,\n"
     "            self.locked_state,\n"
     "            self.active_saving_status,\n"
     "            self.smart_saving_mode_status,\n")

# ============================ switch.py ============================
edit(SWITCH,
     '    ThinQSwitchEntityDescription(\n'
     '        key=AirConditionerFeatures.MODE_AIRCLEAN,\n'
     '        name="Ionizer",\n'
     '        icon="mdi:pine-tree",\n'
     '        turn_off_fn=lambda x: x.device.set_mode_airclean(False),\n'
     '        turn_on_fn=lambda x: x.device.set_mode_airclean(True),\n'
     '    ),\n',
     '    ThinQSwitchEntityDescription(\n'
     '        key=AirConditionerFeatures.MODE_AIRCLEAN,\n'
     '        name="Ionizer",\n'
     '        icon="mdi:pine-tree",\n'
     '        turn_off_fn=lambda x: x.device.set_mode_airclean(False),\n'
     '        turn_on_fn=lambda x: x.device.set_mode_airclean(True),\n'
     '    ),\n'
     '    ThinQSwitchEntityDescription(\n'
     '        key=AirConditionerFeatures.MODE_POWER_SAVE,\n'
     '        name="Energy saving",\n'
     '        icon="mdi:leaf-circle-outline",\n'
     '        turn_off_fn=lambda x: x.device.set_mode_power_save(False),\n'
     '        turn_on_fn=lambda x: x.device.set_mode_power_save(True),\n'
     '    ),\n'
     '    ThinQSwitchEntityDescription(\n'
     '        key=AirConditionerFeatures.MODE_POWER_SAVE_DRY,\n'
     '        name="Energy saving dry",\n'
     '        icon="mdi:water-percent",\n'
     '        turn_off_fn=lambda x: x.device.set_mode_power_save_dry(False),\n'
     '        turn_on_fn=lambda x: x.device.set_mode_power_save_dry(True),\n'
     '    ),\n'
     '    ThinQSwitchEntityDescription(\n'
     '        key=AirConditionerFeatures.MODE_ICE_VALLEY,\n'
     '        name="Ice cool power",\n'
     '        icon="mdi:snowflake-alert",\n'
     '        turn_off_fn=lambda x: x.device.set_mode_ice_valley(False),\n'
     '        turn_on_fn=lambda x: x.device.set_mode_ice_valley(True),\n'
     '    ),\n'
     '    ThinQSwitchEntityDescription(\n'
     '        key=AirConditionerFeatures.MODE_AUTO_DRY,\n'
     '        name="Auto dry",\n'
     '        icon="mdi:hair-dryer",\n'
     '        turn_off_fn=lambda x: x.device.set_mode_auto_dry(False),\n'
     '        turn_on_fn=lambda x: x.device.set_mode_auto_dry(True),\n'
     '    ),\n'
     '    ThinQSwitchEntityDescription(\n'
     '        key=AirConditionerFeatures.MODE_FEEDBACK_SOUND,\n'
     '        name="Beep",\n'
     '        icon="mdi:volume-high",\n'
     '        entity_category=EntityCategory.CONFIG,\n'
     '        turn_off_fn=lambda x: x.device.set_mode_feedback_sound(False),\n'
     '        turn_on_fn=lambda x: x.device.set_mode_feedback_sound(True),\n'
     '    ),\n')

# ============================ sensor.py ============================
edit(SENSOR,
     'AC_SENSORS: tuple[ThinQSensorEntityDescription, ...] = (\n',
     'AC_SENSORS: tuple[ThinQSensorEntityDescription, ...] = (\n'
     '    ThinQSensorEntityDescription(\n'
     '        key=AirConditionerFeatures.DIAGNOSIS,\n'
     '        name="Diagnosis",\n'
     '        icon="mdi:stethoscope",\n'
     '        entity_category=EntityCategory.DIAGNOSTIC,\n'
     '    ),\n')

edit(SENSOR,
     'REFRIGERATOR_SENSORS: tuple[ThinQSensorEntityDescription, ...] = (\n',
     'REFRIGERATOR_SENSORS: tuple[ThinQSensorEntityDescription, ...] = (\n'
     '    ThinQSensorEntityDescription(\n'
     '        key=RefrigeratorFeatures.ACTIVESAVINGSTATUS,\n'
     '        name="Active saving status",\n'
     '        icon="mdi:gauge",\n'
     '        state_class=SensorStateClass.MEASUREMENT,\n'
     '        entity_category=EntityCategory.DIAGNOSTIC,\n'
     '    ),\n'
     '    ThinQSensorEntityDescription(\n'
     '        key=RefrigeratorFeatures.SMARTSAVINGMODESTATUS,\n'
     '        name="Smart saving active",\n'
     '        icon="mdi:leaf",\n'
     '        entity_category=EntityCategory.DIAGNOSTIC,\n'
     '    ),\n'
     '    ThinQSensorEntityDescription(\n'
     '        key=RefrigeratorFeatures.LOCKINGSTATUS,\n'
     '        name="Control lock",\n'
     '        icon="mdi:lock",\n'
     '        entity_category=EntityCategory.DIAGNOSTIC,\n'
     '    ),\n')

# ============================ climate.py ============================
edit(CLIMATE, '    PRESET_ECO,\n    PRESET_NONE,\n',
     '    PRESET_BOOST,\n    PRESET_ECO,\n    PRESET_NONE,\n')

EXTRA_PRESETS = (
    '    @property\n'
    '    def _extra_presets(self) -> dict:\n'
    '        """Presets synthesised from standalone toggles rather than op modes.\n'
    '\n'
    '        Maps preset name -> (feature key, setter coroutine). Only used when the\n'
    '        device exposes no op-mode based presets.\n'
    '        """\n'
    '        if self._available_preset_modes():\n'
    '            return {}\n'
    '        presets = {}\n'
    '        if getattr(self._device, "is_mode_power_save_supported", False):\n'
    '            presets[PRESET_ECO] = (\n'
    '                AirConditionerFeatures.MODE_POWER_SAVE,\n'
    '                self._device.set_mode_power_save,\n'
    '            )\n'
    '        if getattr(self._device, "is_mode_ice_valley_supported", False):\n'
    '            presets[PRESET_BOOST] = (\n'
    '                AirConditionerFeatures.MODE_ICE_VALLEY,\n'
    '                self._device.set_mode_ice_valley,\n'
    '            )\n'
    '        return presets\n'
    '\n'
    '    @property\n'
    '    def preset_mode(self) -> str | None:\n'
    '        """Return the current preset mode."""\n'
    '        if extra := self._extra_presets:\n'
    '            features = self._api.state.device_features\n'
    '            for name, (feature, _setter) in extra.items():\n'
    '                if features.get(feature):\n'
    '                    return name\n'
    '            return PRESET_NONE\n'
    '        return self._attr_preset_mode\n'
    '\n')
edit(CLIMATE,
     '    @property\n'
     '    def preset_modes(self) -> list[str] | None:\n'
     '        """Return the list of available preset modes."""\n'
     '        modes = self._available_preset_modes()\n'
     '        if not modes:\n'
     '            return None\n'
     '        return [PRESET_NONE] + list(modes.values())\n',
     EXTRA_PRESETS +
     '    @property\n'
     '    def preset_modes(self) -> list[str] | None:\n'
     '        """Return the list of available preset modes."""\n'
     '        modes = self._available_preset_modes()\n'
     '        if not modes:\n'
     '            if extra := self._extra_presets:\n'
     '                return [PRESET_NONE] + list(extra)\n'
     '            return None\n'
     '        return [PRESET_NONE] + list(modes.values())\n')

edit(CLIMATE,
     '    async def async_set_preset_mode(self, preset_mode: str) -> None:\n'
     '        """Set new preset mode."""\n'
     '        if not (modes := self._available_preset_modes()):\n'
     '            raise NotImplementedError()\n',
     '    async def async_set_preset_mode(self, preset_mode: str) -> None:\n'
     '        """Set new preset mode."""\n'
     '        if extra := self._extra_presets:\n'
     '            if preset_mode != PRESET_NONE and preset_mode not in extra:\n'
     '                raise ValueError(f"Invalid preset_mode [{preset_mode}]")\n'
     '            if not self._api.state.is_on and preset_mode != PRESET_NONE:\n'
     '                await self._device.power(True)\n'
     '            # Only one synthesised preset may be active at a time.\n'
     '            for name, (_feature, setter) in extra.items():\n'
     '                await setter(name == preset_mode)\n'
     '            self._api.async_set_updated()\n'
     '            return\n'
     '\n'
     '        if not (modes := self._available_preset_modes()):\n'
     '            raise NotImplementedError()\n')

# ============================ washerDryer.py: keep last tub-clean count ============================
WD = os.path.join(ROOT, "wideq", "devices", "washerDryer.py")
edit(WD,
     '            result = self._data.get(key)\n'
     '            if result is None:\n'
     '                result = self._tcl_count or "N/A"\n'
     '        return self._update_feature(WashDeviceFeatures.TUBCLEAN_COUNT, result, False)\n',
     '            result = self._data.get(key)\n'
     '            if result is None:\n'
     '                # Keep reporting the last known count while the machine is powered\n'
     '                # off, instead of dropping to the "N/A" placeholder.\n'
     '                result = self._tcl_count\n'
     '            elif self.int_or_none(result) is not None:\n'
     '                self._tcl_count = result\n'
     '            if result is None:\n'
     '                result = "N/A"\n'
     '        return self._update_feature(WashDeviceFeatures.TUBCLEAN_COUNT, result, False)\n')

edit(WD,
     '    def reset_status(self):\n'
     '        tcl_count = None\n'
     '        if self._status:\n'
     '            tcl_count = self._status.tubclean_count\n'
     '        self._status = WMStatus(self, tcl_count=tcl_count)\n',
     '    def reset_status(self):\n'
     '        tcl_count = None\n'
     '        if self._status:\n'
     '            tcl_count = self._status.tubclean_count\n'
     '            if tcl_count == "N/A":\n'
     '                # Never carry the placeholder forward: it would stick permanently.\n'
     '                tcl_count = None\n'
     '        self._status = WMStatus(self, tcl_count=tcl_count)\n')

# =================== sensor.py: retained tub-clean counter ===================
# The wideq-side fix stops "N/A" poisoning the value, but it is in-memory only.
# RestoreEntity carries the last real count across a Home Assistant restart.
edit(SENSOR,
     '    PERCENTAGE,\n'
     '    STATE_UNAVAILABLE,\n',
     '    PERCENTAGE,\n'
     '    STATE_UNAVAILABLE,\n'
     '    STATE_UNKNOWN,\n')

edit(SENSOR,
     'from homeassistant.helpers.entity_platform import AddEntitiesCallback, current_platform\n',
     'from homeassistant.helpers.entity_platform import AddEntitiesCallback, current_platform\n'
     'from homeassistant.helpers.restore_state import RestoreEntity\n')

edit(SENSOR,
     '_LOGGER = logging.getLogger(__name__)\n',
     '_LOGGER = logging.getLogger(__name__)\n'
     '\n'
     '# States that carry no reading, and so must not overwrite a retained value.\n'
     '_NO_VALUE_STATES = (None, "N/A", "-", STATE_UNAVAILABLE, STATE_UNKNOWN)\n')

edit(SENSOR,
     '    feature_attributes: dict[str, str] | None = None\n',
     '    feature_attributes: dict[str, str] | None = None\n'
     '    restore_last_value: bool = False\n')

edit(SENSOR,
     '        key=WashDeviceFeatures.TUBCLEAN_COUNT,\n'
     '        name="Tub clean counter",\n'
     '        icon=DEFAULT_ICON,\n'
     '        entity_registry_enabled_default=False,\n'
     '    ),\n',
     '        key=WashDeviceFeatures.TUBCLEAN_COUNT,\n'
     '        name="Tub clean counter",\n'
     '        icon=DEFAULT_ICON,\n'
     '        entity_registry_enabled_default=False,\n'
     '        restore_last_value=True,\n'
     '    ),\n')

edit(SENSOR,
     'class LGESensor(CoordinatorEntity, SensorEntity):\n',
     'class LGESensor(CoordinatorEntity, RestoreEntity, SensorEntity):\n')

edit(SENSOR,
     '        self._is_default = description.key == DEFAULT_SENSOR\n',
     '        self._is_default = description.key == DEFAULT_SENSOR\n'
     '        self._restored_value = None\n'
     '\n'
     '    async def async_added_to_hass(self) -> None:\n'
     '        """Restore the previous value for sensors that must survive a restart."""\n'
     '        await super().async_added_to_hass()\n'
     '        if not self.entity_description.restore_last_value:\n'
     '            return\n'
     '        if (last_state := await self.async_get_last_state()) is None:\n'
     '            return\n'
     '        if last_state.state not in _NO_VALUE_STATES:\n'
     '            self._restored_value = last_state.state\n')

edit(SENSOR,
     '        """Return the state of the sensor."""\n'
     '        if not self.available:\n'
     '            return STATE_UNAVAILABLE\n'
     '        return self._get_sensor_state()\n',
     '        """Return the state of the sensor."""\n'
     '        if self.entity_description.restore_last_value:\n'
     '            value = self._get_sensor_state() if self._api.available else None\n'
     '            if value in _NO_VALUE_STATES:\n'
     '                return self._restored_value\n'
     '            self._restored_value = value\n'
     '            return value\n'
     '        if not self.available:\n'
     '            return STATE_UNAVAILABLE\n'
     '        return self._get_sensor_state()\n')

edit(SENSOR,
     '        """Return True if entity is available."""\n'
     '        return self._api.available\n',
     '        """Return True if entity is available."""\n'
     '        if self.entity_description.restore_last_value:\n'
     '            # A retained counter stays meaningful while the appliance is off,\n'
     '            # so keep the entity available as long as we have a value to show.\n'
     '            if self._restored_value is not None:\n'
     '                return True\n'
     '        return self._api.available\n')

applied = skipped = missing = 0
for path, old, new, optional in E:
    src = open(path, encoding="utf-8").read()
    if new in src:
        skipped += 1
        continue
    n = src.count(old)
    if n == 0:
        if optional:
            missing += 1
            continue
        print("FAIL: anchor not found in %s ::\n%s" % (path, old[:200]))
        sys.exit(1)
    if n != 1:
        print("FAIL: anchor matched %d times in %s" % (n, path))
        sys.exit(1)
    open(path, "w", encoding="utf-8").write(src.replace(old, new, 1))
    print("OK    %-16s %s" % (os.path.basename(path), old.strip().split("\n")[0][:56]))
    applied += 1

print("\napplied=%d already-current=%d not-applicable=%d" % (applied, skipped, missing))
print("\n=== syntax check ===")
for f in (CONST, AC, REF, WD, SWITCH, SENSOR, CLIMATE):
    py_compile.compile(f, doraise=True)
    print("  OK", os.path.basename(f))
