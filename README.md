# Next_heatpump — Home Assistant Integration

A HACS-compatible custom integration for the **Adlar Castra Aurora II** heat pump, communicating over **Modbus TCP** via an RS485-to-WiFi gateway.

No YAML required. All setup is done through the Home Assistant UI.
This software is a fork of the Adlar Aurora II as developed by https://github.com/conradhagemans. Thank you for this repository! 
---

## Hardware setup

This integration was developed and tested with the following hardware:

- **JPX-3002** RS485 splitter (2 master / 1 slave):
  - **Slave port** → Modbus RS485 cable from the heat pump
  - **Master 1** → JAN module (original controller)
  - **Master 2** → Elfin EW11A (RS485 to WiFi/TCP bridge)
- The **Elfin EW11A** configured as TCP Server on port **502**
- Modbus slave ID of the heat pump: **1** (default)

Any RS485-to-Modbus-TCP bridge should work (Waveshare, USR-W610, etc.).

---

## Elfin EW11 configuration

**Serial Port Settings:**
- Baud Rate: `9600`
- Data Bit: `8`
- Stop Bit: `1`
- Parity: `None`
- Buffer Size: `1024`
- Gap Time: `100`

**Communication Settings:**
- Protocol: `TCP Server`
- Local Port: `502`

---

## Installation

### Via HACS (recommended)

1. Open **HACS → Integrations**
2. Click the three-dot menu → **Custom repositories**
3. Add this repository URL, category: **Integration**
4. Search for **Next Heatpump** and install
5. Restart Home Assistant

### Manual

Copy the `custom_components/adlar_heatpump/` folder into your HA `config/custom_components/` directory, then restart.

---

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Next Heatpump**
3. Enter:
   - **IP address** of your RS485-TCP gateway
   - **Port** (default `502`)
   - **Slave ID** (default `1`)
   - **Scan interval** in seconds (default `60`)

---

## Entities created

### Sensors (read-only)
| Name | Unit | Notes |
|---|---|---|
| Compressor Target Frequency | Hz | |
| Compressor Running Frequency | Hz | |
| Fan Running Speed | Hz | |
| EEV Open Step | P | |
| EVI Valve Open Step | P | |
| AC Input Current | A | Unit level, ×0.01 |
| Compressor Phase Current | A | Compressor level, ×0.1 |
| High Pressure Saturation Temp | °C | |
| Low Pressure Saturation Temp | °C | |
| Ambient Temp T1 | °C | |
| Outer Coil Temp T2 | °C | |
| Inner Coil Temp T3 | °C | |
| Suction Temp T4 | °C | |
| Exhaust Temp T5 | °C | |
| Water Inlet Temp T6 | °C | |
| Water Outlet Temp T7 | °C | |
| Economizer Inlet Temp T8 | °C | |
| Economizer Outlet Temp T9 | °C | |
| Plate HX Exhaust Temp | °C | |
| Water Pump Speed PWM | % | |
| Water Flow | L/min | |
| Unit Input Current | A | ×0.01 |
| Unit Input Power | kW | ×0.01 |
| Unit Power Consumption | kWh | 32-bit cumulative counter |
| DC Bus Inverter Voltage | V | ×0.1 |
| Thermal Power | kW | Calculated: flow × ΔT × 4.186 / 60 |
| COP | — | Calculated: thermal power / electrical power |
| Calculated Power | W | Calculated: voltage × current |

### Binary Sensors (running status)
| Name | Notes |
|---|---|
| Running Status: Refrigerant Recovery | |
| Running Status: Primary Anti-freeze | |
| Running Status: Secondary Anti-freeze | |
| Running Status: Fault Alarm | |
| Running Status: System Oil Return | |
| Running Status: System Frosting | |
| Running Status: Shutdown after Reaching Temp | |
| Running Status: Shutdown after Unit Failure | |
| Running Status: Unit Operation | |
| Running Status: Unit Waiting for Operation | |

### Controls
| Entity | Type | Options / Range |
|---|---|---|
| Next Heatpump | Climate | Heat / Cool / Heat+Cool / Off |
| Heatpump ON/OFF | Switch | on / off |
| Temp Set Cooling | Number | 7–25 °C |
| Temp Set Heating | Number | 15–60 °C |
| Temp Set Floor Heating | Number | 20–60 °C |
| Mode | Select | Cooling / Heating / Hot Water / Floor Heating / combinations |
| Running Mode | Select | Standard Mode / Boost / Silent |
| Cooling Setting Curve | Select | Off, H1–H8, L1–L8 |
| Heating Setting Curve | Select | Off, H1–H8, L1–L8 |
| Underfloor Heating Setting Curve | Select | Off, H1–H8, L1–L8 |

---

## Technical notes

### Modbus addressing
This integration applies a **-1 address offset** to sensor registers (`0x0040`–`0x0085`). The firmware uses 1-based register addressing in this range, while pymodbus uses 0-based addressing. Control registers (`0x0300`+) and status registers (`0x0000`) do not require this correction.

### Registers not available on R32 model
The following registers always return 0 on the R32 model and are excluded:
- `0x0044` AC Input Voltage
- `0x0047` Compressor IPM Temperature

### Scan interval
The default scan interval is 60 seconds. With ~40 registers × 200ms delay = ~8 seconds per poll cycle, a minimum of 30 seconds is recommended.

---

## Disclaimer
This software is public and not in anyway related to Heative, SolarEast etc. Use at you own risk.
This integration is community-developed and not affiliated with Adlår. Use at your own risk. Incorrect writes to control registers could affect heat pump operation. Always verify setpoints before applying changes.
