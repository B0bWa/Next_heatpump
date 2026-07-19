"""Binary sensor platform for Next Heatpump."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, STATUS_BITS
from .coordinator import NextCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: NextCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        NextBinarySensor(coordinator, mask, name)
        for mask, name in STATUS_BITS
    ]
    async_add_entities(entities)


class NextBinarySensor(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator, mask, name):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_status_{mask:04X}"
        self._attr_name = name
        self._key = name

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.data.get(self._key)

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.coordinator.config_entry.entry_id)},
            "name": "Next R290 Heatpump",
            "manufacturer": "Heative",
            "model": "R290",
        }
