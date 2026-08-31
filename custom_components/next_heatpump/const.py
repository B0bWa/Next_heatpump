"""Constants for Next Heatpump integration."""

DOMAIN = "next_heatpump"
DEFAULT_PORT = 502
DEFAULT_SLAVE = 1
DEFAULT_SCAN_INTERVAL = 45

# ─────────────────────────────────────────────
# Register definitions — adressen gebaseerd op HHI Modbus repo v2.2
# Schaling gevalideerd met Tuya app (Conrad, juni 2026):
#   R32 model stuurt Temperaturen als directe graden (130 = 13°C), scale=1
#   NIET ×0.1 zoals HHI aangeeft (die werkt met een andere firmware/model)
#                 N.B. : De NEXT WP heeft bij R290 versie ook een factor 1 nodig, zie onder
#
# Each entry: (address, name, unit, device_class, scale, signed, min_val, max_val)
# min_val/max_val zijn RAW waarden (vóór scale) — gebruikt voor plausibiliteitscontrole
# bij het lezen (zie coordinator._read_one), om mismatches tussen verzoek en
# antwoord (bijv. door de RTU-TCP gateway) te detecteren: een waarde buiten dit
# bereik wordt behandeld als een mislukte read en opnieuw geprobeerd.
# De bereiken zijn bewust ruim gehouden zodat nooit een geldige waarde wordt
# afgewezen — verfijn ze gerust op basis van wat jouw systeem in de praktijk laat zien.
# ─────────────────────────────────────────────

SENSOR_REGISTERS = [
    # address, name, unit, device_class, scale, signed, min_val, max_val

    # --- Compressor & Ventilator ---
    (0x0040, "Compressor Running Frequency", "Hz",    "frequency",        1,     True,  0,    150),
    (0x0041, "Fan Running Speed",            "Hz",    "frequency",        1,     True,  0,    150),
    (0x0042, "EEV Open Step",                "P",     None,               1,     True,  0,    500),
    (0x0043, "EVI Valve Open Step",          "P",     None,               1,     True,  0,    500),

    # --- Elektrisch (compressor niveau) ---
    (0x0044, "AC Input Voltage",             "V",     "voltage",          1,     True,  0,    300),
    (0x0045, "AC Input Current",             "A",     "current",          0.1,   True,  0,    600),
    (0x0046, "Compressor Phase Current",     "A",     "current",          0.1,   True,  0,    600),

    # --- Temperaturen: adressen HHI v2.2, schaling ×1 (R32 model) ---
    (0x0047, "Compressor IPM Temp.",          "°C",   "temperature",      1,     True,  -20,  120),
    (0x0048, "High Pressure Saturation Temp.","°C",   "temperature",      1,     True,  -20,   90),
    (0x0049, "Low Pressure Saturation Temp.", "°C",   "temperature",      1,     True,  -40,   60),
    (0x004A, "Ambient Temp. T1",              "°C",   "temperature",      1,     True,  -40,   60),
    (0x004B, "Outer Coil Temp. T2",           "°C",   "temperature",      1,     True,  -40,   90),
    (0x004C, "Inner Coil Temp. T3",           "°C",   "temperature",      1,     True,  -40,   90),
    (0x004D, "Suction Temp. T4",              "°C",   "temperature",      1,     True,  -40,   60),
    (0x004E, "Exhaust Temp. T5",              "°C",   "temperature",      1,     True,  -20,  150),
    (0x004F, "Water Inlet Temp. T6",          "°C",   "temperature",      1,     True,  -10,   80),
    (0x0050, "Water Outlet Temp. T7",         "°C",   "temperature",      1,     True,  -10,   80),
    (0x0051, "Economizer Inlet Temp. T8",     "°C",   "temperature",      1,     True,  -40,   90),
    (0x0052, "Economizer Outlet Temp. T9",    "°C",   "temperature",      1,     True,  -40,   90),

    # 0x0053 = Device Tooling No — geen Temperatuur, weglaten

    (0x0054, "DHW Tank Temp.",                "°C",   "temperature",      1,     True,  -50,  90),
    (0x0055, "Plate HX Exhaust Temp.",        "°C",   "temperature",      1,     True,  -40,   90),

    # 0x0056 = Drive Manufacturer Code — geen sensor, weglaten

    # --- Pomp & Flow ---
    (0x0057, "Water Pump Speed PWM",         "%",     None,               1,     True,  0,    100),
    (0x0058, "Water Flow",                   "L/min", "volume_flow_rate", 1,     True,  0,    200),
    (0x0059, "DHW Return Water Temp.",        "°C",    "temperature",      1,     True,  -20,  90),

    # --- Unit niveau elektrisch ---
    (0x005A, "Unit Input Voltage",           "V",     "voltage",          1,     True,  0,    300),
    (0x005B, "Unit Input Current",           "A",     "current",          0.01,  True,  0,    10000),
    (0x005C, "Unit Input Power",             "kW",    "power",            0.01,  True,  0,    3000),

    # --- DC Bus ---
    (0x0085, "DC Bus Inverter Voltage",      "V",     "voltage",          0.1,   True,  0,    8000),
]

# Running status register (bitmask sensors)
STATUS_REGISTER = 0x0000
STATUS_BITS = [
    (0x0001, "Running Status: Refrigerant Recovery"),
    (0x0002, "Running Status: Primary Anti-freeze"),
    (0x0004, "Running Status: Secondary Anti-freeze"),
    (0x0008, "Running Status: Fault Alarm"),
    (0x0010, "Running Status: System Oil Return"),
    (0x0100, "Running Status: System Frosting"),
    (0x1000, "Running Status: Shutdown after Reaching Temp."),
    (0x2000, "Running Status: Shutdown after Unit Failure"),
    (0x4000, "Running Status: Unit Operation"),
    (0x8000, "Running Status: Unit Waiting for Operation"),
]

# ─────────────────────────────────────────────
# Foutregisters — compacte selectie uit handleiding hfst. 4.2 (Error Code)
# Elk register is een aparte 16-bit bitmask, net als STATUS_REGISTER hierboven.
# Alleen de meest relevante bits voor een thuisgebruiker zijn geselecteerd;
# zie de handleiding voor het volledige overzicht (o.a. System 1 Error Status 2/3
# en de driver-board P-codes, die hier bewust zijn weggelaten).
# ─────────────────────────────────────────────

ERROR_STATUS_1_REGISTER = 0x0002
ERROR_STATUS_1_BITS = [
    (0x0001, "Error: Wrong Phase"),
    (0x0002, "Error: Missing Phase"),
    (0x0004, "Error: Water Flow Failure"),
    (0x0008, "Error: Communication Failure"),
    (0x0040, "Error: Water Tank Temp. Sensor Failure"),
    (0x0080, "Error: Water Inlet Temp. Sensor Failure"),
    (0x2000, "Error: Water Outlet Temp. Sensor Failure"),
    (0x4000, "Error: Water Outlet Temp. Too High in Heating Mode"),
    (0x8000, "Error: Large Temp. Difference Water Inlet/Outlet"),
]

ERROR_STATUS_2_REGISTER = 0x0003
ERROR_STATUS_2_BITS = [
    (0x0001, "Error: Ambient Temp. Too Low"),
    (0x2000, "Error: Water Pump 1 Failure"),
    (0x4000, "Error: Water Pump 2 Failure"),
    (0x8000, "Error: Low Water Flow"),
]

SYSTEM1_ERROR_STATUS_1_REGISTER = 0x0005
SYSTEM1_ERROR_STATUS_1_BITS = [
    (0x0001, "Error: High Pressure Switch Failure"),
    (0x0002, "Error: Low Pressure Switch Failure"),
    (0x0004, "Error: High Pressure Too High"),
    (0x0010, "Error: Exhaust Pressure Too High"),
    (0x2000, "Error: Fan Failure"),
]

# Alle statusregisters gebundeld: (register_adres, bits_lijst).
# coordinator.py en binary_sensor.py itereren hierover in plaats van het
# losse STATUS_REGISTER/STATUS_BITS-paar, zodat elk register los wordt
# uitgelezen en de bits erin correct worden gedecodeerd.
STATUS_REGISTERS = [
    (STATUS_REGISTER, STATUS_BITS),
    (ERROR_STATUS_1_REGISTER, ERROR_STATUS_1_BITS),
    (ERROR_STATUS_2_REGISTER, ERROR_STATUS_2_BITS),
    (SYSTEM1_ERROR_STATUS_1_REGISTER, SYSTEM1_ERROR_STATUS_1_BITS),
]

# Energy register: enkel 16-bit register, waarde direct in kWh (geen schaling)
ENERGY_REGISTER = 0x005D

# Writable number registers (address, name, unit, device_class, min, max, step)
NUMBER_REGISTERS = [
    (0x0300, "Temp. Set Cooling",       "°C", "temperature", 7,  25, 1),
    (0x0301, "Temp. Set Heating",       "°C", "temperature", 20, 60, 1),
    (0x0302, "Temp.Set Hot Water",     "°C", "temperature", 20, 75, 1),
    (0x0303, "Temp. Set Floor Heating", "°C", "temperature", 20, 60, 1),
]

# ON/OFF switch register, 0=off, 1=on
SWITCH_REGISTER = 0x0305

# Select registers (address, name, options_map)

CURVE_OPTIONS = {
    "Off": 0, "H1": 1, "H2": 2, "H3": 3, "H4": 4,
    "H5": 5, "H6": 6, "H7": 7, "H8": 8,
    "L1": 11, "L2": 12, "L3": 13, "L4": 14,
    "L5": 15, "L6": 16, "L7": 17, "L8": 18,

}

CURVE_OPTIONS_DHW = {
    "Off": 0, "1": 1, "2": 2, "3": 3, "4": 4,
} 
 
SELECT_REGISTERS = [
    (0x0304, "Mode", {
        "Cooling": 0, "Heating": 1, "Hot Water": 2,
        "Floor Heating": 3, "Hot Water + Cooling": 4,
        "Hot Water + Heating": 5, "Hot Water + Floor Heating": 7,
    }),
    (0x0307, "Running Mode", {
        "Standard Mode": 0, "Boost": 1, "Eco": 2,
    }),
    (0x0313, "Cooling Setting Curve",            CURVE_OPTIONS),
    (0x0314, "Heating Setting Curve",            CURVE_OPTIONS),
    (0x0315, "Hot Water Setting Curve",         CURVE_OPTIONS_DHW),
    (0x0316, "Underfloor Heating Setting Curve", CURVE_OPTIONS),
]

# ─────────────────────────────────────────────
# P119 Refrigerant Type register
# Adres: 0x0177, waarden: 1=R410A, 2=R32, 3=R290
# Bepaalt de Temperatuurschaling:
#   R32  (waarde 2) → ×1  (raw waarde is directe °C)
#   R290 (waarde 3) → ×0.1 (raw waarde gedeeld door 10)
#   R410A (waarde 1) → ×1  (aanname, zelfde als R32)
#   De Next R290 geeft waarde 1 terug ook bij R290
# ─────────────────────────────────────────────
REFRIGERANT_REGISTER = 0x0177

REFRIGERANT_TYPES = {
    1: "R410A",
    2: "R32",
    3: "R290",
}

def get_temperature_scale(refrigerant_type: int) -> float:
    """Bepaal Temperatuurschaling op basis van koelmiddeltype.
    R290 gebruikt ook 1, alle andere ×1.
    """
    return 1 if refrigerant_type == 3 else 1.0


# ─────────────────────────────────────────────
# Geforceerde besturing (Load Forcing) — Engineering Manual, hfst.
# "5. UserCommands 0x0330": "Unit forced control, frequency/speed of
# forced control". Zet de warmtepomp voor het gekozen subsysteem buiten
# zijn normale regellus en dwingt een vaste compressorfrequentie of
# ventilatorsnelheid af, ongeacht wat de normale besturingslogica zou
# kiezen.
#
# Dit is een service-/commissioning-functie, geen normale bedieningsknop:
# zolang het bijbehorende bit aan staat, blijft de opgegeven frequentie/
# snelheid aangehouden totdat het bit weer uit wordt gezet — de warmtepomp
# corrigeert dan niet meer zelf op basis van druk, temperatuur of
# veiligheidsgrenzen voor dat subsysteem. Zie de disclaimer in README.md;
# alleen compressor en ventilator zijn hier ontsloten (EEV/EVI-forcering en
# de "Compressor 2"-variant voor dual-systeem-units bewust niet, buiten de
# scope van deze feature).
#
# 0x0331 "Load Forcing Control" — bitmask-register, elk bit schakelt
# geforceerde besturing voor één subsysteem in (1) of uit (0).
FORCE_CONTROL_REGISTER = 0x0331
FORCE_CONTROL_BITS = [
    (0x0001, "Compressor Forced Control"),
    (0x0008, "Fan Forced Control"),
]

# Geforceerde frequentie-/snelheidswaarden. Hebben alleen effect zolang het
# bijbehorende bit in FORCE_CONTROL_BITS aan staat.
# address, name, unit, device_class, min, max, step
FORCE_VALUE_REGISTERS = [
    (0x0332, "Compressor Forced Frequency", "Hz", "frequency", 0, 120, 1),
    (0x033E, "Fan Forced Speed",            "Hz", "frequency", 0, 80,  1),
]

# ─────────────────────────────────────────────
# Silent Mode frequentiegrenzen — Engineering Manual, "System Parameters P"
# (0x0100～0x02FF), registers 0x0158/0x0159. Dit zijn de Modbus-adressen
# achter de fabrieksparameters P88 ("Max. compressor operating frequency",
# standaard 50Hz, 20-70Hz) en P89 ("Max. fan operating frequency", standaard
# 40Hz, 20-60Hz) die op het bediendisplay onder installateurswachtwoord
# staan, in het hoofdstuk "Silent Mode" — bedoeld om geluidsoverlast te
# beperken.
#
# Dit is GEEN forceerwaarde zoals FORCE_VALUE_REGISTERS hierboven: het zijn
# bovengrenzen die alleen gelden zolang de unit in Silent/Eco-modus draait
# (zie SELECT_REGISTERS "Running Mode", waarde "Eco" = 2 = fabrieksmatig
# "Silent mode"). Binnen die grens blijft de warmtepomp gewoon zelf regelen
# op basis van vraag/druk/temperatuur — vergelijkbaar met wat je via het
# display met installateurswachtwoord kon instellen.
# address, name, unit, device_class, min, max, step
SILENT_MODE_REGISTERS = [
    (0x0158, "Silent Mode - Compressor Max Frequency", "Hz", "frequency", 20, 70, 1),
    (0x0159, "Silent Mode - Fan Max Frequency",         "Hz", "frequency", 20, 60, 1),
]

# ─────────────────────────────────────────────
# Elektrisch bijverwarmingselement — vrijgavetemperatuur (P22)
# Engineering Manual, "System Parameters P" (0x0100～0x02FF), register
# 0x0116. Komt overeen met fabrieksparameter P22 ("Ambient temperature
# value - Allow electric heater to start", hoofdstuk 4.3.2 Factory
# Parameter, sectie "Electric heating"): de buitentemperatuur waaronder
# de elektrische bijverwarming mag inschakelen als ondersteuning van de
# warmtepomp. Standaard -7°C op de meeste unitvarianten, instelbaar
# -15～40°C.
#
# LET OP: dit bereik bevat negatieve waarden. write_register() in
# coordinator.py maskeert de te schrijven waarde daarom naar 16-bit
# unsigned (two's complement) vóór verzending — zie de toelichting daar.
# address, name, unit, device_class, min, max, step
ELECTRIC_HEATER_REGISTERS = [
    (0x0116, "Electric Heater Allow Start Temp.", "°C", "temperature", -15, 40, 1),
]

# ─────────────────────────────────────────────
# 6. Version Information 0x0360~0x036F
# (Product Model / Customized Version / Software Version)
#
# Alleen de vier door de fabrikant gedocumenteerde registers in dit blok
# zijn hier opgenomen (0x0360-0x0363, aaneengesloten, één batch-read);
# 0x0364-0x036F staan niet in de manual en worden niet uitgelezen.
# Alle vier zijn read-only (R) — er komt dus geen number/select-entiteit
# voor, alleen sensoren.
# ─────────────────────────────────────────────
VERSION_INFO_START_REGISTER = 0x0360  # t/m 0x0363, 4 registers

# Program Version (0x0360) en Protocol Version (0x0363): de raw waarde is
# major*100 + minor, bijv. 100 → weergegeven als "V1.00". De manual noteert
# de defaultwaarde van Program Version als "V1.0." en die van Protocol
# Version als "V1.0.0" — twee verschillende notaties voor kennelijk hetzelfde
# schaalformaat; vermoedelijk een inconsistentie in het brondocument. Beide
# worden hier op dezelfde manier geformatteerd, zie coordinator._fetch_all.

# Product Type (0x0361):
PRODUCT_TYPE_MAP = {
    0: "Commercial inverter unit",
    1: "Domestic ON/OFF unit",
    2: "Commercial ON/OFF unit",
}

# Product Type ID Number (0x0362) — de betekenis is afhankelijk van de
# gelijktijdige waarde van Product Type (0x0361). Letterlijk overgenomen uit
# de manual-note:
#   Product Type=0 (Commercial inverter unit):
#       0 = Commercial inverter 2-unit, 1 = Commercial inverter 3-unit
#   Product Type=1 (Domestic ON/OFF unit):
#       0 = Domestic inverter unit
#   Product Type=2 (Commercial ON/OFF unit):
#       0 = Commercial inverter unit
# LET OP: bij Product Type=2 noemt de manual ID-waarde 0 zélf ook weer
# "Commercial inverter unit" — inconsistent met Product Type=2 zelf, dat
# "Commercial ON/OFF unit" heet. Dit lijkt een fout/typo in het
# brondocument; hier bewust letterlijk overgenomen in plaats van
# stilzwijgend gecorrigeerd, zodat je dit zelf tegen je eigen toestel kunt
# verifiëren (kijk wat Product Type bij jouw model teruggeeft).
PRODUCT_TYPE_ID_MAP = {
    0: {0: "Commercial inverter 2-unit", 1: "Commercial inverter 3-unit"},
    1: {0: "Domestic inverter unit"},
    2: {0: "Commercial inverter unit"},
}
