"""Binary sensor platform for Next Heatpump."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, STATUS_REGISTER, STATUS_REGISTERS
from .coordinator import NextCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: NextCoordinator = hass.data[DOMAIN][entry.entry_id]
    # Alle statusregisters: Running Status (0x0000) plus de foutregisters.
    entities = [
        NextBinarySensor(coordinator, address, mask, name)
        for address, bits in STATUS_REGISTERS
        for mask, name in bits
    ]
    async_add_entities(entities)


class NextBinarySensor(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator, address, mask, name):
        super().__init__(coordinator)
        # Running Status behoudt de oorspronkelijke unique_id (geen dubbele
        # entiteiten na update); foutregisters krijgen het adres erbij,
        # omdat dezelfde bitmask in meerdere registers voorkomt.
        if address == STATUS_REGISTER:
            self._attr_unique_id = f"{coordinator.config_entry.entry_id}_status_{mask:04X}"
        else:
            self._attr_unique_id = (
                f"{coordinator.config_entry.entry_id}_status_{address:04X}_{mask:04X}"
            )
            self._attr_device_class = BinarySensorDeviceClass.PROBLEM
        self._attr_name = name
        self._key = name

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.data.get(self._key)

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.coordinator.config_entry.entry_id)},
            "name": "",
            "manufacturer": "Heative",
            "model": "",
        }
