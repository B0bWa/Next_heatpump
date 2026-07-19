"""Modbus TCP data coordinator for Next Heatpump."""
from __future__ import annotations

import logging
import ctypes
import time
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    SENSOR_REGISTERS,
    STATUS_REGISTER,
    STATUS_BITS,
    NUMBER_REGISTERS,
    SWITCH_REGISTER,
    SELECT_REGISTERS,
    ENERGY_REGISTER,
    REFRIGERANT_REGISTER,
    REFRIGERANT_TYPES,
    get_temperature_scale,
)

_LOGGER = logging.getLogger(__name__)

# Delay between individual register reads (seconds)
# Gives the JPX-3002 splitter and EW11 time to process each request
REQUEST_DELAY = 0.2

# Registers die een temperatuur zijn (device_class == "temperature")
# Schaling wordt bepaald door P119 koelmiddeltype
TEMPERATURE_DEVICE_CLASS = "temperature"


def _to_signed(value: int) -> int:
    return ctypes.c_int16(value).value


class NextCoordinator(DataUpdateCoordinator):

    def __init__(self, hass, host, port, slave, scan_interval):
        self.host = host
        self.port = port
        self.slave = slave
        self._client = None
        self.refrigerant_type: int | None = None
        self.refrigerant_name: str = "Unknown"
        self.temperature_scale: float = 1.0  # default R32
        super().__init__(
            hass, _LOGGER, name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    def _get_client(self):
        """Return connected client, reconnect if needed."""
        from pymodbus.client import ModbusTcpClient
        if self._client is None or not self._client.connected:
            if self._client is not None:
                try:
                    self._client.close()
                except Exception:
                    pass
            self._client = ModbusTcpClient(host=self.host, port=self.port, timeout=10)
            self._client.connect()
        return self._client

    def _read_one(self, address: int) -> int | None:
        """Read a single holding register with delay. Reconnects on failure.

        No address offset is applied. pymodbus uses 0-based addressing natively,
        identical to jsmodbus. Register 0x0040 = address 0x0040.
        """
        time.sleep(REQUEST_DELAY)
        try:
            client = self._get_client()
            result = client.read_holding_registers(
                address=address, count=1, device_id=self.slave
            )
            if hasattr(result, 'isError') and result.isError():
                _LOGGER.warning("Error reading register 0x%04X", address)
                return None
            return result.registers[0]
        except Exception as err:
            _LOGGER.warning("Exception reading 0x%04X: %s — reconnecting", address, err)
            self._client = None
            return None

    def _detect_refrigerant(self) -> None:
        """Lees P119 (0x0177) en stel temperatuurschaling in.

        Wordt éénmalig uitgevoerd bij de eerste poll.
        R32  (2) → ×1.0  (directe °C waarden)
        R290 (3) → ×0.1  (raw/10 = °C)
        R410A(1) → ×1.0  (aanname gelijk aan R32)
        """
        raw = self._read_one(REFRIGERANT_REGISTER)
        if raw is None:
            _LOGGER.warning(
                "P119 (0x0177) kon niet worden uitgelezen — "
                "standaard temperatuurschaling ×1 (R32) wordt gebruikt"
            )
            return

        self.refrigerant_type = raw
        self.refrigerant_name = REFRIGERANT_TYPES.get(raw, f"Unknown ({raw})")
        self.temperature_scale = get_temperature_scale(raw)

        _LOGGER.info(
            "Koelmiddeltype gedetecteerd: %s (P119=%d) — temperatuurschaling: ×%s",
            self.refrigerant_name,
            raw,
            self.temperature_scale,
        )

    async def _async_update_data(self) -> dict:
        try:
            return await self.hass.async_add_executor_job(self._fetch_all)
        except Exception as err:
            raise UpdateFailed(f"Error communicating with heatpump: {err}") from err

    def _fetch_all(self) -> dict:
        data: dict = {}

        # ── Eénmalig: koelmiddeltype detecteren ──
        if self.refrigerant_type is None:
            self._detect_refrigerant()

        # Sla koelmiddelinfo op in data zodat het als sensor beschikbaar is
        data["Refrigerant Type"] = self.refrigerant_name
        data["Temperature Scale"] = self.temperature_scale

        # ── Compressor target frequency ──
        raw = self._read_one(0x0027)
        data["Compressor Target Frequency"] = raw

        # ── Sensor registers ──
        for address, name, unit, device_class, scale, signed in SENSOR_REGISTERS:
            raw = self._read_one(address)
            if raw is None:
                data[name] = None
            else:
                value = _to_signed(raw) if signed else raw
                # Temperatuurregisters: schaling uit P119
                if device_class == TEMPERATURE_DEVICE_CLASS:
                    effective_scale = self.temperature_scale
                else:
                    effective_scale = scale
                data[name] = round(value * effective_scale, 1) if effective_scale != 1 else value

        # ── Energy register (single 16-bit, value directly in kWh) ──
        raw = self._read_one(ENERGY_REGISTER)
        data["Unit Power Consumption"] = float(raw) if raw is not None else None

        # ── Status bitmask ──
        raw_status = self._read_one(STATUS_REGISTER)
        for mask, bit_name in STATUS_BITS:
            data[bit_name] = bool(raw_status & mask) if raw_status is not None else None

        # ── Number registers (control register area) ──
        for address, name, unit, device_class, mn, mx, step in NUMBER_REGISTERS:
            raw = self._read_one(address)
            data[name] = _to_signed(raw) if raw is not None else None

        # ── Switch register ──
        raw = self._read_one(SWITCH_REGISTER)
        data["ON/OFF"] = bool(raw) if raw is not None else None

        # ── Select registers ──
        for address, name, options_map in SELECT_REGISTERS:
            raw = self._read_one(address)
            if raw is None:
                data[name] = None
            else:
                rev = {v: k for k, v in options_map.items()}
                data[name] = rev.get(raw, f"Unknown ({raw})")

        return data

    def write_register(self, address: int, value: int) -> bool:
        """Write a single holding register."""
        try:
            time.sleep(REQUEST_DELAY)
            client = self._get_client()
            result = client.write_register(
                address=address, value=value, device_id=self.slave
            )
            return not result.isError()
        except Exception as err:
            _LOGGER.error("Write error at 0x%04X: %s", address, err)
            self._client = None
            return False
