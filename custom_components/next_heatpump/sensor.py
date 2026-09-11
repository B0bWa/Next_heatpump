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
        for address, name, unit, device_class, scale, signed, min_val, max_val in SENSOR_REGISTERS
    ]
    # Energy: state_class=TOTAL zodat HA dalingen (bijv. na reset) correct afhandelt
    entities.append(NextEnergySensor(coordinator))
    entities.append(NextSensor(coordinator, 0x0027, "Compressor Target Frequency", "Hz", "frequency"))
    entities.append(NextThermalPowerSensor(coordinator))
    entities.append(NextCOPSensor(coordinator))
    entities.append(NextCalculatedPowerSensor(coordinator))
    entities.append(NextRefrigerantSensor(coordinator))
    entities.append(NextVersionSensor(coordinator, "Program Version", 0x0360, "mdi:chip"))
    entities.append(NextProductTypeSensor(coordinator))
    entities.append(NextProductTypeIdSensor(coordinator))
    entities.append(NextVersionSensor(coordinator, "Protocol Version", 0x0363, "mdi:transit-connection-variant"))

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
            "name": "",
            "manufacturer": "Heative",
            "model": "",
        }


class NextEnergySensor(CoordinatorEntity, SensorEntity):
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
            "name": "",
            "manufacturer": "Heative",
            "model": "",
        }


class NextThermalPowerSensor(CoordinatorEntity, SensorEntity):
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
            t_in = float(data.get("Water Inlet Temp. T6") or 0)
            t_out = float(data.get("Water Outlet Temp. T7") or 0)
            delta_t = t_out - t_in
            thermal_kw = flow * delta_t * 4.186 / 60
            return round(thermal_kw, 2)
        except (TypeError, ValueError):
            return None

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.coordinator.config_entry.entry_id)},
            "name": "",
            "manufacturer": "Heative",
            "model": "",
        }


class NextCOPSensor(CoordinatorEntity, SensorEntity):
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
            t_in = float(data.get("Water Inlet Temp. T6") or 0)
            t_out = float(data.get("Water Outlet Temp. T7") or 0)
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
            "name": "",
            "manufacturer": "Heative",
            "model": "",
        }


class NextCalculatedPowerSensor(CoordinatorEntity, SensorEntity):
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
            voltage = float(data.get("AC Input Voltage") or 0)
            current = float(data.get("Compressor Phase Current") or 0)
            if voltage <= 0:
                return None
            return round(voltage * current, 1)
        except (TypeError, ValueError):
            return None

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.coordinator.config_entry.entry_id)},
            "name": "",
            "manufacturer": "Heative",
            "model": "",
        }


class NextRefrigerantSensor(CoordinatorEntity, SensorEntity):
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
            "name": "",
            "manufacturer": "Heative",
            "model": "",
        }


class NextVersionSensor(CoordinatorEntity, SensorEntity):
    """Program Version (0x0360) / Protocol Version (0x0363).

    Statische, read-only firmware-/protocolversie ("V1.00"-notatie, zie
    const.py voor de formattering). Verandert alleen na een firmware-update
    van het toestel.
    """

    def __init__(self, coordinator, key: str, address: int, icon: str):
        super().__init__(coordinator)
        self._key = key
        self._raw_key = f"{key} Raw"
        self._address = address
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{address:04X}"
        self._attr_name = key
        self._attr_native_unit_of_measurement = None
        self._attr_device_class = None
        self._attr_state_class = None
        self._attr_icon = icon

    @property
    def native_value(self):
        return self.coordinator.data.get(self._key)

    @property
    def extra_state_attributes(self):
        return {
            "raw_value": self.coordinator.data.get(self._raw_key),
            "register": f"0x{self._address:04X}",
        }

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.coordinator.config_entry.entry_id)},
            "name": "",
            "manufacturer": "Heative",
            "model": "",
        }


class NextProductTypeSensor(CoordinatorEntity, SensorEntity):
    """Product Type (0x0361) — zie PRODUCT_TYPE_MAP in const.py."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_0361"
        self._attr_name = "Product Type"
        self._attr_native_unit_of_measurement = None
        self._attr_device_class = None
        self._attr_state_class = None
        self._attr_icon = "mdi:information-outline"

    @property
    def native_value(self):
        return self.coordinator.data.get("Product Type")

    @property
    def extra_state_attributes(self):
        return {
            "raw_value": self.coordinator.data.get("Product Type Raw"),
            "register": "0x0361",
        }

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.coordinator.config_entry.entry_id)},
            "name": "",
            "manufacturer": "Heative",
            "model": "",
        }


class NextProductTypeIdSensor(CoordinatorEntity, SensorEntity):
    """Product Type ID Number (0x0362) — betekenis hangt af van Product Type
    (0x0361), zie PRODUCT_TYPE_ID_MAP in const.py (incl. een gevlagde
    inconsistentie in de manual bij Product Type=2).
    """

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_0362"
        self._attr_name = "Product Type ID Number"
        self._attr_native_unit_of_measurement = None
        self._attr_device_class = None
        self._attr_state_class = None
        self._attr_icon = "mdi:identifier"

    @property
    def native_value(self):
        return self.coordinator.data.get("Product Type ID Number")

    @property
    def extra_state_attributes(self):
        return {
            "raw_value": self.coordinator.data.get("Product Type ID Number Raw"),
            "product_type": self.coordinator.data.get("Product Type"),
            "register": "0x0362",
        }

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.coordinator.config_entry.entry_id)},
            "name": "",
            "manufacturer": "Heative",
            "model": "",
        }
