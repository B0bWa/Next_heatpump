"""Number platform for Next Heatpump (writable setpoints)."""
from __future__ import annotations

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    NUMBER_REGISTERS,
    FORCE_VALUE_REGISTERS,
    SILENT_MODE_REGISTERS,
    ELECTRIC_HEATER_REGISTERS,
)
from .coordinator import NextCoordinator

# Namen uit FORCE_VALUE_REGISTERS krijgen een afwijkend icoon (zie
# NextNumber hieronder) zodat ze in de UI visueel te onderscheiden zijn van
# gewone setpoints: ze hebben alleen effect zolang de bijbehorende Load
# Forcing-switch aan staat, en overschrijven dan de normale regellus.
# SILENT_MODE_REGISTERS (P88/P89) krijgen bewust GEEN afwijkend icoon: dat
# zijn normale, door de fabrikant bedoelde instellingen (dezelfde die je via
# het bediendisplay met installateurswachtwoord kunt zetten), geen
# service-override.
_FORCE_VALUE_NAMES = {name for _, name, *_ in FORCE_VALUE_REGISTERS}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: NextCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        NextNumber(coordinator, address, name, unit, device_class, mn, mx, step)
        for address, name, unit, device_class, mn, mx, step
        in NUMBER_REGISTERS
        + SILENT_MODE_REGISTERS
        + ELECTRIC_HEATER_REGISTERS
        + FORCE_VALUE_REGISTERS
    ]
    async_add_entities(entities)


class NextNumber(CoordinatorEntity, NumberEntity):
    def __init__(self, coordinator, address, name, unit, device_class, mn, mx, step):
        super().__init__(coordinator)
        self._address = address
        self._key = name
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_num_{address:04X}"
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = NumberDeviceClass.TEMPERATURE if device_class == "temperature" else None
        self._attr_native_min_value = mn
        self._attr_native_max_value = mx
        self._attr_native_step = step
        self._attr_mode = NumberMode.BOX
        if name in _FORCE_VALUE_NAMES:
            self._attr_icon = "mdi:alert-decagram-outline"

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.get(self._key)

    async def async_set_native_value(self, value: float) -> None:
        await self.hass.async_add_executor_job(
            self.coordinator.write_register, self._address, int(value)
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
