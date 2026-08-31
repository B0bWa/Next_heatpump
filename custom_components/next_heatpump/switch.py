"""Switch platform for Next Heatpump (ON/OFF + geforceerde besturing)."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SWITCH_REGISTER, FORCE_CONTROL_REGISTER, FORCE_CONTROL_BITS
from .coordinator import NextCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: NextCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [NextSwitch(coordinator)]
    entities += [
        NextForceControlSwitch(coordinator, mask, name)
        for mask, name in FORCE_CONTROL_BITS
    ]
    async_add_entities(entities)


class NextSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_onoff"
        self._attr_name = "Heatpump ON/OFF"

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.data.get("ON/OFF")

    async def async_turn_on(self, **kwargs) -> None:
        await self.hass.async_add_executor_job(
            self.coordinator.write_register, SWITCH_REGISTER, 1
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self.hass.async_add_executor_job(
            self.coordinator.write_register, SWITCH_REGISTER, 0
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


class NextForceControlSwitch(CoordinatorEntity, SwitchEntity):
    """Schakelt geforceerde besturing (Load Forcing, register 0x0331) in/uit
    voor één subsysteem (compressor of ventilator).

    LET OP: zolang dit bit aan staat, negeert de warmtepomp zijn normale
    regellus voor dit subsysteem en houdt hij de waarde aan die in de
    bijbehorende "Forced Frequency"/"Forced Speed" number-entiteit staat —
    zonder eigen correctie op basis van druk, temperatuur of
    veiligheidsgrenzen. Dit is bedoeld als kortdurende service-/testfunctie,
    niet om continu aan te laten staan. Zie de disclaimer in README.md.
    """

    def __init__(self, coordinator, mask, name):
        super().__init__(coordinator)
        self._mask = mask
        self._key = name
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_force_{mask:04X}"
        self._attr_name = name
        self._attr_icon = "mdi:alert-decagram-outline"

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.data.get(self._key)

    async def async_turn_on(self, **kwargs) -> None:
        await self.hass.async_add_executor_job(
            self.coordinator.write_bit, FORCE_CONTROL_REGISTER, self._mask, True
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self.hass.async_add_executor_job(
            self.coordinator.write_bit, FORCE_CONTROL_REGISTER, self._mask, False
        )
        await self.coordinator.async_request_refresh()

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.coordinator.config_entry.entry_id)},
            "name": "",
            "manufacturer": "Heative",
            "model": "",
        }"""Switch platform for Next Heatpump (ON/OFF)."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SWITCH_REGISTER
from .coordinator import NextCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: NextCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([NextSwitch(coordinator)])


class NextSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_onoff"
        self._attr_name = "Heatpump ON/OFF"

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.data.get("ON/OFF")

    async def async_turn_on(self, **kwargs) -> None:
        await self.hass.async_add_executor_job(
            self.coordinator.write_register, SWITCH_REGISTER, 1
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self.hass.async_add_executor_job(
            self.coordinator.write_register, SWITCH_REGISTER, 0
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
