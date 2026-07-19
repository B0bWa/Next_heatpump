"""Select platform for Next Heatpump."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SELECT_REGISTERS
from .coordinator import NextCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: NextCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        NextSelect(coordinator, address, name, options_map)
        for address, name, options_map in SELECT_REGISTERS
    ]
    async_add_entities(entities)


class NextSelect(CoordinatorEntity, SelectEntity):
    def __init__(self, coordinator, address, name, options_map):
        super().__init__(coordinator)
        self._address = address
        self._key = name
        self._options_map = options_map  # label → int
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_sel_{address:04X}"
        self._attr_name = name
        self._attr_options = list(options_map.keys())

    @property
    def current_option(self) -> str | None:
        return self.coordinator.data.get(self._key)

    async def async_select_option(self, option: str) -> None:
        value = self._options_map.get(option)
        if value is None:
            return
        await self.hass.async_add_executor_job(
            self.coordinator.write_register, self._address, value
        )
        await self.coordinator.async_request_refresh()

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.coordinator.config_entry.entry_id)},
            "name": "Next Heatpump",
            "manufacturer": "Heative",
            "model": "R290",
        }
