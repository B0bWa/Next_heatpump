"""Modbus TCP data coordinator for Next Heatpump."""
from __future__ import annotations

import logging
import ctypes
import random
import threading
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

WRITE_DELAY = 0.25
REQUEST_DELAY = 0.5
# Kleine willekeurige variatie op REQUEST_DELAY, zodat onze polling niet
# steeds op exact dezelfde momenten valt als het pollritme van een andere
# Modbus-master op de bus (bijv. een display via een RS485-splitter).
REQUEST_DELAY_JITTER = 0.2

# Aantal pogingen per registerlezing voordat we het als mislukt beschouwen
READ_ATTEMPTS = 2

# ── Bus-contentie / "circuit breaker" ──
# Als meerdere registers/batches ná elkaar volledig mislukken, is dat een
# sterke aanwijzing dat de gedeelde RS485-bus op dit moment bezet is door
# een andere master (bijv. een display via een 2-master/1-slave splitter),
# niet dat onze eigen instellingen fout staan. Doorrammen met de gebruikelijke
# REQUEST_DELAY helpt dan niet en genereert alleen maar extra reconnects naar
# de RTU-TCP gateway terwijl die het al druk heeft. In plaats daarvan pauzeren
# we een tijdje zodat de bus kan vrijkomen, en gaan daarna pas weer verder.
CONSECUTIVE_FAILURE_THRESHOLD = 3
BURST_COOLDOWN = 8.0  # seconden

# Maximaal aantal registers dat in één Modbus-call wordt gebatcht.
# Ruim onder de Modbus-limiet van 125, en klein genoeg om een batch op
# 9600 bd nog in een fractie van een seconde te versturen/ontvangen.
MAX_BATCH_SIZE = 32

# Registers die een temperatuur zijn (device_class == "temperature")
# Schaling wordt bepaald door P119 koelmiddeltype
TEMPERATURE_DEVICE_CLASS = "temperature"


def _to_signed(value: int) -> int:
    return ctypes.c_int16(value).value


def _contiguous_runs(specs: list[tuple], max_batch: int = MAX_BATCH_SIZE) -> list[list[tuple]]:
    """Groepeer registerspecs (waarvan specs[i][0] het adres is) in reeksen
    van opeenvolgende adressen, zodat ze in één Modbus-call gelezen kunnen
    worden i.p.v. één call per register.

    Een reeks wordt afgekapt zodra het volgende adres niet aansluit, of
    zodra `max_batch` registers bereikt is.
    """
    if not specs:
        return []
    runs: list[list[tuple]] = []
    current = [specs[0]]
    for spec in specs[1:]:
        prev_address = current[-1][0]
        address = spec[0]
        if address == prev_address + 1 and len(current) < max_batch:
            current.append(spec)
        else:
            runs.append(current)
            current = [spec]
    runs.append(current)
    return runs


# Eenmalig (bij import) berekend — de registerlijsten in const.py zijn statisch.
_SENSOR_RUNS = _contiguous_runs(SENSOR_REGISTERS)
_NUMBER_RUNS = _contiguous_runs(NUMBER_REGISTERS)


class NextCoordinator(DataUpdateCoordinator):

    def __init__(self, hass, host, port, slave, scan_interval):
        self.host = host
        self.port = port
        self.slave = slave
        self._client = None
        # ModbusTcpClient is not thread-safe, and both the polling cycle
        # (_fetch_all, run in an executor thread) and service/entity writes
        # (write_register, run in their own executor thread) share
        # self._client. This lock ensures only one thread touches the
        # socket at a time — prevents "Bad file descriptor" races where
        # one thread closes the connection while another is mid read/write.
        self._lock = threading.Lock()
        # Teller: aantal implausibele waarden (buiten min_val/max_val) die
        # tijdens de laatste pollcyclus zijn afgevangen en opnieuw geprobeerd.
        # Gereset aan het begin van elke _fetch_all-cyclus.
        self._implausible_count = 0
        # Laatst succesvol (plausibel) gelezen register — gebruikt om te loggen
        # welk register vlak vóór een implausibele lezing werd gelezen, om een
        # "antwoord komt één stap te laat"-mismatch te kunnen herkennen.
        self._last_read_address: int | None = None
        self._last_read_value: int | None = None
        # Aantal opeenvolgende volledig mislukte registers/batches — de
        # circuit breaker voor busbezetting (zie _register_failure).
        self._consecutive_failures = 0
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
            self._client = ModbusTcpClient(
                host=self.host, port=self.port, timeout=10, retries=3
            )
            self._client.connect()
        return self._client

    def _sleep_request_delay(self) -> None:
        time.sleep(REQUEST_DELAY + random.uniform(0, REQUEST_DELAY_JITTER))

    def _register_success(self) -> None:
        """Reset de mislukking-op-rij-teller na een geslaagde lezing."""
        self._consecutive_failures = 0

    def _register_failure(self) -> None:
        """Hoog de mislukking-op-rij-teller op en pauzeer indien nodig.

        Wordt aangeroepen wanneer een register (via _read_one) of een hele
        batch (via _read_range) uiteindelijk niets bruikbaars opleverde.
        Bij CONSECUTIVE_FAILURE_THRESHOLD op rij nemen we aan dat de bus
        momenteel bezet is door een andere master en pauzeren we even, in
        plaats van door te blijven rammen met reconnects.
        """
        self._consecutive_failures += 1
        if self._consecutive_failures >= CONSECUTIVE_FAILURE_THRESHOLD:
            _LOGGER.warning(
                "%d opeenvolgende mislukte lezingen — de RS485-bus lijkt "
                "momenteel bezet (bijv. door een andere Modbus-master zoals "
                "een display via de splitter). Pauzeer %.0fs voordat er "
                "verder wordt gepolld.",
                self._consecutive_failures, BURST_COOLDOWN,
            )
            time.sleep(BURST_COOLDOWN)
            self._consecutive_failures = 0

    def _read_one(
        self,
        address: int,
        attempts: int = READ_ATTEMPTS,
        min_val: int | None = None,
        max_val: int | None = None,
    ) -> int | None:
        """Read a single holding register with delay. Reconnects on failure.

        No address offset is applied. pymodbus uses 0-based addressing natively,
        identical to jsmodbus. Register 0x0040 = address 0x0040.

        Probeert een read tot `attempts` keer voordat de client wordt weggegooid
        en None wordt teruggegeven — voorkomt dat één hikkende read de hele
        cyclus dwingt tot herhaaldelijk herverbinden.

        Als min_val/max_val zijn opgegeven, wordt een waarde buiten dat bereik
        behandeld als een mislukte read (kan wijzen op een mismatch tussen
        verzoek en antwoord bij de RTU-TCP gateway) en opnieuw geprobeerd.
        De vergelijking gebeurt op de signed-geïnterpreteerde waarde.
        """
        last_err: Exception | None = None
        for attempt in range(1, attempts + 1):
            self._sleep_request_delay()
            try:
                with self._lock:
                    client = self._get_client()
                    result = client.read_holding_registers(
                        address=address, count=1, device_id=self.slave
                    )
                if hasattr(result, 'isError') and result.isError():
                    _LOGGER.warning(
                        "Error reading register 0x%04X (attempt %d/%d)",
                        address, attempt, attempts,
                    )
                    continue

                value = result.registers[0]

                if min_val is not None and max_val is not None:
                    signed_value = _to_signed(value)
                    if not (min_val <= signed_value <= max_val):
                        self._implausible_count += 1
                        if self._last_read_address is not None:
                            _LOGGER.warning(
                                "Implausibele waarde %d (verwacht %d..%d) voor "
                                "register 0x%04X (attempt %d/%d) — vorig gelezen "
                                "register was 0x%04X met waarde %s — waarschijnlijk "
                                "mismatch, opnieuw proberen",
                                signed_value, min_val, max_val, address, attempt, attempts,
                                self._last_read_address, self._last_read_value,
                            )
                        else:
                            _LOGGER.warning(
                                "Implausibele waarde %d (verwacht %d..%d) voor "
                                "register 0x%04X (attempt %d/%d) — geen vorig "
                                "register bekend — waarschijnlijk mismatch, "
                                "opnieuw proberen",
                                signed_value, min_val, max_val, address, attempt, attempts,
                            )
                        continue

                # Alleen bijhouden bij een geslaagde, plausibele read
                self._last_read_address = address
                self._last_read_value = value
                self._register_success()
                return value
            except Exception as err:
                last_err = err
                _LOGGER.warning(
                    "Exception reading 0x%04X (attempt %d/%d): %s",
                    address, attempt, attempts, err,
                )
                with self._lock:
                    self._client = None

        if last_err is not None:
            _LOGGER.warning(
                "Gaf op na %d pogingen voor register 0x%04X: %s — reconnecting",
                attempts, address, last_err,
            )
        self._register_failure()
        return None

    def _read_range(
        self,
        start_address: int,
        count: int,
        attempts: int = READ_ATTEMPTS,
    ) -> list[int] | None:
        """Lees `count` aaneengesloten holding registers in één Modbus-call.

        Zelfde retry-/reconnect-gedrag als _read_one, maar dan voor een heel
        blok registers tegelijk — dit scheelt round trips (en dus tijd op de
        gedeelde RS485-bus) t.o.v. één call per register. Geeft bij succes
        een lijst met `count` ruwe (unsigned) waarden terug, of None als het
        hele blok na `attempts` pogingen nog steeds mislukt.

        Plausibiliteitscontrole (min_val/max_val) gebeurt hier bewust niet —
        dat blijft aan de aanroeper, die voor een enkel afwijkend register
        binnen de batch een gerichte her-lezing via _read_one kan doen i.p.v.
        meteen de hele batch af te keuren.
        """
        last_err: Exception | None = None
        end_address = start_address + count - 1
        for attempt in range(1, attempts + 1):
            self._sleep_request_delay()
            try:
                with self._lock:
                    client = self._get_client()
                    result = client.read_holding_registers(
                        address=start_address, count=count, device_id=self.slave
                    )
                if hasattr(result, 'isError') and result.isError():
                    _LOGGER.warning(
                        "Error reading range 0x%04X..0x%04X (attempt %d/%d)",
                        start_address, end_address, attempt, attempts,
                    )
                    continue

                values = list(result.registers)
                self._register_success()
                return values
            except Exception as err:
                last_err = err
                _LOGGER.warning(
                    "Exception reading range 0x%04X..0x%04X (attempt %d/%d): %s",
                    start_address, end_address, attempt, attempts, err,
                )
                with self._lock:
                    self._client = None

        if last_err is not None:
            _LOGGER.warning(
                "Gaf op na %d pogingen voor bereik 0x%04X..0x%04X: %s — reconnecting",
                attempts, start_address, end_address, last_err,
            )
        self._register_failure()
        return None

    def _apply_scale(self, spec: tuple, raw: int | None):
        """Pas signed-conversie en schaling toe, zoals voorheen in _fetch_all."""
        address, name, unit, device_class, scale, signed, min_val, max_val = spec
        if raw is None:
            return None
        value = _to_signed(raw) if signed else raw
        effective_scale = self.temperature_scale if device_class == TEMPERATURE_DEVICE_CLASS else scale
        return round(value * effective_scale, 1) if effective_scale != 1 else value

    def _read_sensor_run(self, run: list[tuple], data: dict) -> None:
        """Lees één aaneengesloten reeks SENSOR_REGISTERS in één batch-call
        en vul `data` met de verwerkte waarden. Registers die buiten hun
        min/max-bereik vallen worden individueel opnieuw gelezen (zelfde
        vangnet als voorheen), zonder de hele batch te herhalen.
        """
        start = run[0][0]
        values = self._read_range(start, len(run))
        for i, spec in enumerate(run):
            address, name, unit, device_class, scale, signed, min_val, max_val = spec
            raw = values[i] if values is not None else None

            if raw is not None and min_val is not None and max_val is not None:
                signed_check = _to_signed(raw)
                if not (min_val <= signed_check <= max_val):
                    self._implausible_count += 1
                    _LOGGER.warning(
                        "Implausibele waarde %d (verwacht %d..%d) voor register "
                        "0x%04X binnen batch 0x%04X..0x%04X — losse her-lezing",
                        signed_check, min_val, max_val, address,
                        start, start + len(run) - 1,
                    )
                    raw = self._read_one(address, min_val=min_val, max_val=max_val)
                else:
                    self._last_read_address = address
                    self._last_read_value = raw

            data[name] = self._apply_scale(spec, raw)

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
        # Reset de teller voor implausibele waarden aan het begin van elke cyclus.
        self._implausible_count = 0
        # Bewust NIET self._consecutive_failures resetten aan het begin van de
        # cyclus — een busbotsing kan precies op de overgang tussen twee
        # cycli vallen, en dan willen we die telling laten doorlopen.
        try:
            # ── Eénmalig: koelmiddeltype detecteren ──
            if self.refrigerant_type is None:
                self._detect_refrigerant()

            # Sla koelmiddelinfo op in data zodat het als sensor beschikbaar is
            data["Refrigerant Type"] = self.refrigerant_name
            data["Temperature Scale"] = self.temperature_scale

            # ── Compressor target frequency ──
            raw = self._read_one(0x0027)
            data["Compressor Target Frequency"] = raw

            # ── Sensor registers — in aaneengesloten batches i.p.v. één
            #    Modbus-call per register (zie _SENSOR_RUNS hierboven) ──
            for run in _SENSOR_RUNS:
                self._read_sensor_run(run, data)

            # ── Energy register (single 16-bit, value directly in kWh) ──
            raw = self._read_one(ENERGY_REGISTER)
            data["Unit Power Consumption"] = float(raw) if raw is not None else None

            # ── Status bitmask ──
            raw_status = self._read_one(STATUS_REGISTER)
            for mask, bit_name in STATUS_BITS:
                data[bit_name] = bool(raw_status & mask) if raw_status is not None else None

            # ── Number registers (control register area) — ook gebatcht ──
            for run in _NUMBER_RUNS:
                start = run[0][0]
                values = self._read_range(start, len(run))
                for i, (address, name, unit, device_class, mn, mx, step) in enumerate(run):
                    raw = values[i] if values is not None else None
                    if raw is not None:
                        signed_check = _to_signed(raw)
                        if not (mn <= signed_check <= mx):
                            _LOGGER.warning(
                                "Implausibele waarde %d (verwacht %d..%d) voor "
                                "number-register 0x%04X binnen batch — losse "
                                "her-lezing", signed_check, mn, mx, address,
                            )
                            raw = self._read_one(address, min_val=mn, max_val=mx)
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

            if self._implausible_count:
                _LOGGER.info(
                    "Pollcyclus voltooid met %d implausibele waarde(n) "
                    "afgevangen en herprobeerd",
                    self._implausible_count,
                )

            return data
        finally:
            # Close the connection at the end of every cycle so the socket
            # never sits idle across scan_interval — avoids stale/half-closed
            # connections that the device silently drops between polls.
            with self._lock:
                if self._client is not None:
                    try:
                        self._client.close()
                    except Exception:
                        pass
                    self._client = None

    def write_register(self, address: int, value: int) -> bool:
        """Write a single holding register."""
        self._sleep_request_delay()
        with self._lock:
            try:
                client = self._get_client()
                result = client.write_register(
                    address=address, value=value, device_id=self.slave
                )
                return not result.isError()
            except Exception as err:
                _LOGGER.error("Write error at 0x%04X: %s", address, err)
                self._client = None
                return False
            finally:
                if self._client is not None:
                    try:
                        self._client.close()
                    except Exception:
                        pass
                    self._client = None
