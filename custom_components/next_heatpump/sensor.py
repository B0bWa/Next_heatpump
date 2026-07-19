"""Sensor platform for Next Heatpump."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SENSOR_REGISTERS
from .coordinator import NextCoordinator


def _safe_device_class(name: str | None):
    if name is None:
        return None
    try:
        return SensorDeviceClass(name)
    except ValueError:
        return None


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: NextCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        NextSensor(coordinator, address, name, unit, device_class)
        for address, name, unit, device_class, scale, signed in SENSOR_REGISTERS
    ]
    # Energy: state_class=TOTAL zodat HA dalingen (bijv. na reset) correct afhandelt
    entities.append(NextEnergySensor(coordinator))
    entities.append(NextSensor(coordinator, 0x0027, "Compressor Target Frequency", "Hz", "frequency"))
    entities.append(NextThermalPowerSensor(coordinator))
    entities.append(NextCOPSensor(coordinator))
    entities.append(NextCalculatedPowerSensor(coordinator))
    entities.append(NextRefrigerantSensor(coordinator))

    async_add_entities(entities)


class NextSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, address, name, unit, device_class):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{address:04X}"
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = _safe_device_class(device_class)
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._key = name

    @property
    def native_value(self):
        return self.coordinator.data.get(self._key)

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.coordinator.config_entry.entry_id)},
            "name": "Next Heatpump",
            "manufacturer": "Heative",
            "model": "R290",
        }


class AdlarEnergySensor(CoordinatorEntity, SensorEntity):
    """Totaal energieverbruik sensor.

    Gebruikt state_class=TOTAL zodat Home Assistant een daling (bijv. na reset
    van de interne teller) correct interpreteert als een reset en niet als fout.
    """

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_005D"
        self._attr_name = "Unit Power Consumption"
        self._attr_native_unit_of_measurement = "kWh"
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.TOTAL
        self._attr_icon = "mdi:counter"

    @property
    def native_value(self):
        return self.coordinator.data.get("Unit Power Consumption")

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.coordinator.config_entry.entry_id)},
            "name": "Adlar Aurora II Heatpump",
            "manufacturer": "Adlar",
            "model": "Aurora II",
        }


class AdlarThermalPowerSensor(CoordinatorEntity, SensorEntity):
    """Thermal power output calculated from flow and delta-T."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_thermal_power"
        self._attr_name = "Thermal Power"
        self._attr_native_unit_of_measurement = "kW"
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:heat-wave"

    @property
    def native_value(self) -> float | None:
        data = self.coordinator.data
        try:
            flow = float(data.get("Water Flow") or 0)
            t_in = float(data.get("Water Inlet Temp T6") or 0)
            t_out = float(data.get("Water Outlet Temp T7") or 0)
            delta_t = t_out - t_in
            thermal_kw = flow * delta_t * 4.186 / 60
            return round(thermal_kw, 2)
        except (TypeError, ValueError):
            return None

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.coordinator.config_entry.entry_id)},
            "name": "Adlar Aurora II Heatpump",
            "manufacturer": "Adlar",
            "model": "Aurora II",
        }


class AdlarCOPSensor(CoordinatorEntity, SensorEntity):
    """COP = Thermal Power / Electrical Power."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_cop"
        self._attr_name = "COP"
        self._attr_native_unit_of_measurement = None
        self._attr_device_class = None
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:lightning-bolt-circle"

    @property
    def native_value(self) -> float | None:
        data = self.coordinator.data
        try:
            flow = float(data.get("Water Flow") or 0)
            t_in = float(data.get("Water Inlet Temp T6") or 0)
            t_out = float(data.get("Water Outlet Temp T7") or 0)
            electrical_kw = float(data.get("Unit Input Power") or 0)
            if electrical_kw <= 0:
                return None
            delta_t = t_out - t_in
            thermal_kw = flow * delta_t * 4.186 / 60
            return round(thermal_kw / electrical_kw, 2)
        except (TypeError, ValueError):
            return None

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.coordinator.config_entry.entry_id)},
            "name": "Adlar Aurora II Heatpump",
            "manufacturer": "Adlar",
            "model": "Aurora II",
        }


class AdlarCalculatedPowerSensor(CoordinatorEntity, SensorEntity):
    """Estimated power = Supply Voltage x Compressor Current Draw."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_calculated_power"
        self._attr_name = "Calculated Power"
        self._attr_native_unit_of_measurement = "W"
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:flash"

    @property
    def native_value(self) -> float | None:
        data = self.coordinator.data
        try:
            voltage = float(data.get("Supply Line Voltage") or 0)
            current = float(data.get("Compressor Current Draw") or 0)
            if voltage <= 0:
                return None
            return round(voltage * current, 1)
        except (TypeError, ValueError):
            return None

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.coordinator.config_entry.entry_id)},
            "name": "Adlar Aurora II Heatpump",
            "manufacturer": "Adlar",
            "model": "Aurora II",
        }


class AdlarRefrigerantSensor(CoordinatorEntity, SensorEntity):
    """Koelmiddeltype sensor — toont R32/R290/R410A op basis van P119 (0x0177)."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_refrigerant_type"
        self._attr_name = "Refrigerant Type"
        self._attr_native_unit_of_measurement = None
        self._attr_device_class = None
        self._attr_state_class = None
        self._attr_icon = "mdi:molecule"

    @property
    def native_value(self):
        return self.coordinator.data.get("Refrigerant Type")

    @property
    def extra_state_attributes(self):
        return {
            "temperature_scale": self.coordinator.data.get("Temperature Scale"),
            "p119_register": "0x0177",
        }

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.coordinator.config_entry.entry_id)},
            "name": "Adlar Aurora II Heatpump",
            "manufacturer": "Adlar",
            "model": "Aurora II",
        }
