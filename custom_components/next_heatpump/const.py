"""Constants for Next Heatpump integration."""

DOMAIN = "next_heatpump"
DEFAULT_PORT = 502
DEFAULT_SLAVE = 1
DEFAULT_SCAN_INTERVAL = 60

# ─────────────────────────────────────────────
# Register definitions — adressen gebaseerd op HHI Modbus repo v2.2
# Schaling gevalideerd met Tuya app (Conrad, juni 2026):
#   R32 model stuurt Temperaturen als directe graden (130 = 13°C), scale=1
#   NIET ×0.1 zoals HHI aangeeft (die werkt met een andere firmware/model)
#                 N.B. : De NEXT WP heeft bij R290 versie ook een factor 1 nodig, zie onder 
# Each entry: (address, name, unit, device_class, scale, signed)
# ─────────────────────────────────────────────

SENSOR_REGISTERS = [
    # address, name, unit, device_class, scale, signed

    # --- Compressor & Ventilator ---
    (0x0040, "Compressor Running Frequency", "Hz",    "frequency",        1,     True),
    (0x0041, "Fan Running Speed",            "Hz",    "frequency",        1,     True),
    (0x0042, "EEV Open Step",                "P",     None,               1,     True),
    (0x0043, "EVI Valve Open Step",          "P",     None,               1,     True),

    # --- Elektrisch (compressor niveau) ---
    (0x0044, "AC Input Voltage",             "V",     "voltage",          1,   True),
    (0x0045, "AC Input Current",             "A",     "current",          0.1,   True),
    (0x0046, "Compressor Phase Current",     "A",     "current",          0.1,   True),

    # --- Temperaturen: adressen HHI v2.2, schaling ×1 (R32 model) ---
    (0x0047, "Compressor IPM Temp.",          "°C",    "temperature",      1,     True),
    (0x0048, "High Pressure Saturation Temp.","°C",    "temperature",      1,     True),
    (0x0049, "Low Pressure Saturation Temp.", "°C",    "temperature",      1,     True),
    (0x004A, "Ambient Temp. T1",              "°C",    "temperature",      1,     True),
    (0x004B, "Outer Coil Temp. T2",           "°C",    "temperature",      1,     True),
    (0x004C, "Inner Coil Temp. T3",           "°C",    "temperature",      1,     True),
    (0x004D, "Suction Temp. T4",              "°C",    "temperature",      1,     True),
    (0x004E, "Exhaust Temp. T5",              "°C",    "temperature",      1,     True),
    (0x004F, "Water Inlet Temp. T6",          "°C",    "temperature",      1,     True),
    (0x0050, "Water Outlet Temp. T7",         "°C",    "temperature",      1,     True),
    (0x0051, "Economizer Inlet Temp. T8",     "°C",    "temperature",      1,     True),
    (0x0052, "Economizer Outlet Temp. T9",    "°C",    "temperature",      1,     True),
    
    # 0x0053 = Device Tooling No — geen Temperatuur, weglaten
    
    (0x0054, "DHW Tank Temp.",                "°C",   "temperature",      1,     True),
    (0x0055, "Plate HX Exhaust Temp.",        "°C",    "temperature",      1,     True),
    
    # 0x0056 = Drive Manufacturer Code — geen sensor, weglaten

    # --- Pomp & Flow ---
    (0x0057, "Water Pump Speed PWM",         "%",     None,               1,     True),
    (0x0058, "Water Flow",                   "L/min", "volume_flow_rate", 1,     True),
    (0x0059, "DHW Return Water Temp.",        "°C",    "temperature",      1,     True),

    # --- Unit niveau elektrisch ---
    (0x005A, "Unit Input Voltage",           "V",     "voltage",          1,     True),
    (0x005B, "Unit Input Current",           "A",     "current",          0.01,  True),
    (0x005C, "Unit Input Power",             "kW",    "power",            0.01,  True),
    

    # --- DC Bus ---
    (0x0085, "DC Bus Inverter Voltage",      "V",     "voltage",          0.1,   True),
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

# Energy register: enkel 16-bit register, waarde direct in kWh (geen schaling)
ENERGY_REGISTER = 0x005D

# Writable number registers (address, name, unit, device_class, min, max, step)
NUMBER_REGISTERS = [
    (0x0300, "Temp. Set Cooling",       "°C", "temperature", 7,  25, 1),
    (0x0301, "Temp. Set Heating",       "°C", "temperature", 15, 60, 1),
#   (0x0302, "Temp.Set Hot Water",     "°C", "temperature", 20, 75, 1),
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
# Warmwater:
#    "Off": 0, "DHW1": 1, "DHW2": 2, "DHW3": 3, "DHW4": 4,

}

SELECT_REGISTERS = [
    (0x0304, "Mode", {
        "Cooling": 0, "Heating": 1, "Hot Water": 2,
        "Floor Heating": 3, "Hot Water + Cooling": 4,
        "Hot Water + Heating": 5, "Hot Water + Floor Heating": 7,
    }),
    (0x0307, "Running Mode", {
        "Standard Mode": 0, "Boost": 1, "Silent": 2,
    }),
    (0x0313, "Cooling Setting Curve",            CURVE_OPTIONS),
    (0x0314, "Heating Setting Curve",            CURVE_OPTIONS),
    #(0x0315, "Hot Water Setting Curve",         CURVE_OPTIONS),
    (0x0316, "Underfloor Heating Setting Curve", CURVE_OPTIONS),
]

# ─────────────────────────────────────────────
# P119 Refrigerant Type register
# Adres: 0x0177, waarden: 1=R410A, 2=R32, 3=R290
# Bepaalt de Temperatuurschaling:
#   R32  (waarde 2) → ×1  (raw waarde is directe °C)
#   R290 (waarde 3) → ×0.1 (raw waarde gedeeld door 10)
#   R410A (waarde 1) → ×1  (aanname, zelfde als R32)
#   De Next geeft waarde 1 terug ook bij R290
# ─────────────────────────────────────────────
REFRIGERANT_REGISTER = 0x0177

REFRIGERANT_TYPES = {
    1: "R410A",
    2: "R32",
    3: "R290",
}

def get_temperature_scale(refrigerant_type: int) -> float:
    """Bepaal Temperatuurschaling op basis van koelmiddeltype.
    R290 gebruikt ×0.1, alle andere ×1.
    """
    return 1 if refrigerant_type == 3 else 1.0
