"""Constants for Next Heatpump integration."""

DOMAIN = "next_heatpump"
DEFAULT_PORT = 502
DEFAULT_SLAVE = 1
DEFAULT_SCAN_INTERVAL = 30

# ─────────────────────────────────────────────
# Register definitions — adressen gebaseerd op HHI Modbus repo v2.2
# Schaling gevalideerd met Tuya app (Conrad, juni 2026): temperaturen als
# directe graden (130 = 13°C), scale=1 — NIET ×0.1 zoals HHI aangeeft (die
# werkt met een andere firmware/model).
#
# Deze integratie is uitsluitend bedoeld voor de R290-uitvoering van deze
# warmtepomp. Er wordt niet meer per koelmiddeltype vertakt/geschaald (dat
# leverde toch altijd dezelfde schaling ×1 op voor dit toestel) — het
# koelmiddeltype-register wordt alleen nog ter informatie uitgelezen, zie
# REFRIGERANT_REGISTER/REFRIGERANT_TYPES verderop.
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
    (0x0001, "Error: Wrong Phase E01"),
    (0x0002, "Error: Missing Phase"),
    (0x0004, "Error: Water Flow Failure E03"),
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
    # Fabrieksparameter (handleiding hfst. "Factory Parameter 0x0200-0x03FF"):
    # "Low protection value - Water flow rate" — minimaal doorstromingsdebiet
    # waaronder de flow-beveiliging aanslaat. Voorzichtig mee zijn: te hoog
    # instellen kan de beveiliging onterecht laten aanslaan bij normaal
    # bedrijf; te laag instellen vermindert de beveiliging tegen te weinig
    # waterdoorstroming (risico op bevriezing/ooverhitting van de
    # warmtewisselaar).
    (0x0186, "Min Flow Protection",     "L/min", None, 0, 100, 1),
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
# P119 Koelmiddeltype-register — alleen ter informatie/verificatie.
# Adres: 0x0177, waarden: 1=R410A, 2=R32, 3=R290. Deze integratie is
# uitsluitend bedoeld voor R290, dus er wordt niet meer op vertakt of
# geschaald — de sensor toont 'm puur zodat je kunt controleren dat de
# unit daadwerkelijk R290 rapporteert.
# ─────────────────────────────────────────────
REFRIGERANT_REGISTER = 0x0177

REFRIGERANT_TYPES = {
    1: "R410A",
    2: "R32",
    3: "R290",
}


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

# ─────────────────────────────────────────────
# Stooklijnen (weersafhankelijke regeling) — handleiding hfst. 4.1.1
# "Heating Curves". Elke curve is een lijst van
# (min_incl, max_excl, water_uitlaattemp) — min/max=None betekent "geen
# ondergrens" resp. "geen bovengrens" (komt overeen met "≥X" en "<X" in de
# tabel). Bij lookup: eerste bucket waar min <= T < max (met None als
# wildcard) geldt.
#
# H1-H8 = "HH"-curves (Hoge temperatuur voor verwarming, blz. 143)
# L1-L8 = "HL"-curves (Lage temperatuur voor verwarming, blz. 144)
# Curve 4 en 6 zijn door de fabrikant aangemerkt als ECO-energiebesparende
# curves (zie noot onder beide tabellen in de manual).
# ─────────────────────────────────────────────

HEATING_CURVES = {
    "H1": [(16, None, 50), (8, 16, 51), (0, 8, 52), (-8, 0, 53), (-16, -8, 54), (None, -16, 55)],
    "H2": [(17, None, 45), (14, 17, 46), (10, 14, 47), (6, 10, 48), (2, 6, 49), (-2, 2, 50),
           (-6, -2, 51), (-10, -6, 52), (-14, -10, 53), (-20, -14, 54), (None, -20, 55)],
    "H3": [(16, None, 45), (8, 16, 46), (0, 8, 47), (-8, 0, 48), (-16, -8, 49), (None, -16, 50)],
    # H4 = ECO energy saving curve (zie manual-noot)
    "H4": [(19, None, 40), (16, 19, 41), (13, 16, 42), (10, 13, 43), (7, 10, 44), (4, 7, 45),
           (1, 4, 46), (-2, 1, 47), (-5, -2, 48), (-8, -5, 49), (-10, -8, 50), (-12, -10, 51),
           (-14, -12, 52), (-16, -14, 53), (-18, -16, 54), (None, -18, 55)],
    "H5": [(17, None, 40), (14, 17, 41), (10, 14, 42), (6, 10, 43), (2, 6, 44), (-2, 2, 45),
           (-6, -2, 46), (-10, -6, 47), (-14, -10, 48), (-20, -14, 49), (None, -20, 50)],
    # H6 = ECO energy saving curve (zie manual-noot)
    "H6": [(16, None, 40), (8, 16, 41), (0, 8, 42), (-8, 0, 43), (-16, -8, 44), (None, -16, 45)],
    "H7": [(17, None, 35), (14, 17, 36), (10, 14, 37), (6, 10, 38), (2, 6, 39), (-2, 2, 40),
           (-6, -2, 41), (-10, -6, 42), (-14, -10, 43), (-20, -14, 44), (None, -20, 45)],
    "H8": [(16, None, 35), (8, 16, 36), (0, 8, 37), (-8, 0, 38), (-16, -8, 39), (None, -16, 40)],

    "L1": [(18, None, 32), (9, 18, 33), (4, 9, 34), (-3, 4, 35), (-10, -3, 36), (-16, -10, 37),
           (None, -16, 38)],
    "L2": [(16, None, 30), (8, 16, 31), (0, 8, 32), (-8, 0, 33), (-16, -8, 34), (None, -16, 35)],
    "L3": [(14, None, 30), (0, 14, 31), (-14, 0, 32), (None, -14, 33)],
    # LET OP: in de manual ontbreekt het bereik 8≤T<13 voor curve L4 (springt
    # direct van "13≤T<18" naar "6≤T<8") — vermoedelijk een druk-/OCR-fout in
    # het brondocument. Letterlijk overgenomen; T tussen 8 en 13°C valt hier
    # tussen wal en schip (lookup geeft dan None terug). Verifieer dit tegen
    # je eigen papieren handleiding als je vaak in dat bereik zit.
    "L4": [(18, None, 28), (13, 18, 29), (6, 8, 30), (0, 6, 31), (-5, 0, 32), (-9, -5, 33),
           (-16, -9, 34), (None, -16, 35)],
    "L5": [(16, None, 28), (8, 16, 29), (0, 8, 30), (-8, 0, 31), (-16, -8, 32), (None, -16, 33)],
    "L6": [(16, None, 26), (8, 16, 27), (0, 8, 28), (-8, 0, 29), (-16, -8, 30), (None, -16, 31)],
    "L7": [(14, None, 26), (0, 14, 27), (-14, 0, 28), (None, -14, 29)],
    "L8": [(16, None, 24), (8, 16, 25), (0, 8, 26), (-8, 0, 27), (-16, -8, 28), (None, -16, 29)],
}


def get_heating_curve_target(curve_name: str, ambient_temp: float):
    """Zoek de doel-water-uitlaattemperatuur op voor een gegeven stooklijn
    en buitentemperatuur. Retourneert None als de curve onbekend is, of als
    de temperatuur in een lacune van de tabel valt (zie noot bij L4)."""
    buckets = HEATING_CURVES.get(curve_name)
    if not buckets:
        return None
    for min_incl, max_excl, target in buckets:
        if (min_incl is None or ambient_temp >= min_incl) and (max_excl is None or ambient_temp < max_excl):
            return target
    return None


# ─────────────────────────────────────────────
# P116 "Unit Temperature Control Mode" (register 0x0174, manual hfst. 2.8) —
# bewust GEEN SELECT_REGISTERS-entry (dus niet als schrijfbare dropdown in
# HA). Dit is een fabrieksparameter die intern bepaalt of de unit regelt op
# de water-INLET (T6) of water-OUTLET (T7) temperatuur; het toont als een
# schrijfbare 'select' in HA suggereert ten onrechte dat je hier gewoon
# tussen kunt kiezen zoals bij Mode/Running Mode. Wordt daarom als
# alleen-lezen sensor uitgelezen (zie coordinator.py/sensor.py) — wie 'm
# toch wil wijzigen doet dat bewust via het display, niet per ongeluk
# vanuit dit dashboard.
CONTROL_MODE_REGISTER = 0x0174
CONTROL_MODE_OPTIONS = {0: "Inlet (T6)", 1: "Outlet (T7)"}
