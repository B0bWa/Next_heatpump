"""Climate platform for Next Heatpump."""
from __future__ import annotations

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.components.climate.const import (
    HVACAction,
    PRESET_BOOST,
    PRESET_ECO,
    PRESET_NONE,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SWITCH_REGISTER, SELECT_REGISTERS, NUMBER_REGISTERS
from .coordinator import NextCoordinator

# Modbus register addresses
_MODE_REGISTER = 0x0304
_RUNNING_MODE_REGISTER = 0x0307
_SWITCH_REGISTER = 0x0305
_SETPOINT_COOLING = 0x0300
_SETPOINT_HEATING = 0x0301
_SETPOINT_FLOOR = 0x0303

# Mapping between HA HVACMode and Modbus mode values
_HVAC_TO_MODBUS = {
    HVACMode.COOL: 0,
    HVACMode.HEAT: 1,
    HVACMode.HEAT_COOL: 3,
}
_MODBUS_TO_HVAC = {v: k for k, v in _HVAC_TO_MODBUS.items()}

# Preset modes
PRESET_NORMAL = PRESET_NONE
_PRESET_TO_MODBUS = {
    PRESET_NONE:  0,  # Standard
    PRESET_BOOST: 1,  # Boost
    PRESET_ECO:   2,  # Silent
}
_MODBUS_TO_PRESET = {v: k for k, v in _PRESET_TO_MODBUS.items()}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: NextCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([NextClimate(coordinator)])


class NextClimate(CoordinatorEntity, ClimateEntity):
    """Climate entity for Next R290."""

    _attr_name = "Next Hp"
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.COOL, HVACMode.HEAT, HVACMode.HEAT_COOL]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE |
        ClimateEntityFeature.PRESET_MODE
    )
    _attr_target_temperature_step = 1.0
    _attr_preset_modes = [PRESET_NONE, PRESET_BOOST, PRESET_ECO]

    def __init__(self, coordinator: NextCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_climate"

    @property
    def current_temperature(self) -> float | None:
        return self.coordinator.data.get("Water Inlet Temp T6")

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current HVAC mode."""
        is_on = self.coordinator.data.get("ON/OFF")
        if not is_on:
            return HVACMode.OFF
        mode_str = self.coordinator.data.get("Mode")
        mode_map = {"Cooling": HVACMode.COOL, "Heating": HVACMode.HEAT, "Floor Heating": HVACMode.HEAT_COOL}
        return mode_map.get(mode_str, HVACMode.OFF)

    @property
    def hvac_action(self) -> HVACAction | None:
        """Return current action based on compressor frequency."""
        is_on = self.coordinator.data.get("ON/OFF")
        if not is_on:
            return HVACAction.OFF
        freq = self.coordinator.data.get("Compressor Running Frequency") or 0
        if freq > 0:
            mode = self.hvac_mode
            if mode == HVACMode.COOL:
                return HVACAction.COOLING
            elif mode in (HVACMode.HEAT, HVACMode.HEAT_COOL):
                return HVACAction.HEATING
        return HVACAction.IDLE

    @property
    def target_temperature(self) -> float | None:
        """Return setpoint for current mode."""
        mode_str = self.coordinator.data.get("Mode")
        setpoint_map = {
            "Cooling":       "Temp Set Cooling",
            "Heating":       "Temp Set Heating",
            "Floor Heating": "Temp Set Floor Heating",
        }
        key = setpoint_map.get(mode_str)
        return self.coordinator.data.get(key) if key else None

    @property
    def min_temp(self) -> float:
        mode_str = self.coordinator.data.get("Mode")
        return 7.0 if mode_str == "Cooling" else 20.0

    @property
    def max_temp(self) -> float:
        return 25.0 if self.coordinator.data.get("Mode") == "Cooling" else 60.0

    @property
    def preset_mode(self) -> str | None:
        """Return current preset (Standard/Boost/Silent)."""
        running_mode = self.coordinator.data.get("Running Mode")
        mode_map = {
            "Standard Mode": PRESET_NONE,
            "Boost":         PRESET_BOOST,
            "Silent":        PRESET_ECO,
        }
        return mode_map.get(running_mode, PRESET_NONE)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set preset mode (Standard/Boost/Silent)."""
        modbus_value = _PRESET_TO_MODBUS.get(preset_mode, 0)
        await self.hass.async_add_executor_job(
            self.coordinator.write_register, _RUNNING_MODE_REGISTER, modbus_value
        )
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set HVAC mode (on/off + mode register)."""
        if hvac_mode == HVACMode.OFF:
            await self.hass.async_add_executor_job(
                self.coordinator.write_register, _SWITCH_REGISTER, 0
            )
        else:
            modbus_mode = _HVAC_TO_MODBUS.get(hvac_mode)
            if modbus_mode is not None:
                await self.hass.async_add_executor_job(
                    self.coordinator.write_register, _MODE_REGISTER, modbus_mode
                )
            await self.hass.async_add_executor_job(
                self.coordinator.write_register, _SWITCH_REGISTER, 1
            )
        await self.coordinator.async_request_refresh()

    async def async_set_temperature(self, **kwargs) -> None:
        """Set target temperature for current mode."""
        temp = kwargs.get("temperature")
        if temp is None:
            return
        mode_str = self.coordinator.data.get("Mode")
        setpoint_register_map = {
            "Cooling":       _SETPOINT_COOLING,
            "Heating":       _SETPOINT_HEATING,
            "Floor Heating": _SETPOINT_FLOOR,
        }
        register = setpoint_register_map.get(mode_str)
        if register is not None:
            await self.hass.async_add_executor_job(
                self.coordinator.write_register, register, int(temp)
            )
        await self.coordinator.async_request_refresh()

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.coordinator.config_entry.entry_id)},
            "name": "",
            "manufacturer": "Heative",
            "model": "",
        }
