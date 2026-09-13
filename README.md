# Next_heatpump — Home Assistant Integration


<img width="200" height="150" alt="xlarge_Heative_Next_Incl_R290_9bada899cd" src="https://github.com/user-attachments/assets/b314144f-d007-4edc-bede-11d402fa12d3" />  


A HACS-compatible custom integration for the **Heative Next R290 heat pump**, communicating over **Modbus TCP** via an RS485-to-WiFi gateway.

No YAML required. All setup is done through the Home Assistant UI. But for dashboard and timeschedule extra repository and yaml files are required. See install via HACS: https://github.com/nielsfaber/scheduler-component  

### This software is a fork of the Adlar Aurora II repository as developed by https://github.com/conradhagemans.  
---

## Hardware setup

This integration was developed and tested with the following hardware:   

<img width="150" height="125" alt="display" src="https://github.com/user-attachments/assets/20c5453a-56c3-44a9-8a18-39b98387c47c" />

<img width="150" height="125" alt="ew11a" src="https://github.com/user-attachments/assets/10f683a6-cb0b-4d4a-b3b9-e8222eb84d58" />

<img width="150" height="125" alt="Naamloos" src="https://github.com/user-attachments/assets/f37784bc-e5b3-4190-a267-d83e73a5b944" />



- **E810-R21 Ebyte** RS485 splitter (2 master / 1 slave): 
  - **Slave port** → Modbus RS485 cable from the heat pump
  - **Master 1** → Elfin EW11 4G module
  - **Master 2** → Elfin EW11A (RS485 to WiFi/TCP bridge)
- The **Elfin EW11A** configured as TCP Server on port **502**
- Modbus slave ID of the heat pump: **1** (default)

[E810-Rx1+User+Manual_EN_v1.0.pdf](https://github.com/user-attachments/files/31154340/E810-Rx1%2BUser%2BManual_EN_v1.0.pdf)

Any RS485-to-Modbus-TCP bridge should work.

### Or disconnect TFT display and use this repository with EW11A instead. Both connected on the display connection rs485 WILL NOT WORK!
---

## Elfin EW11 configuration


**Serial Port Settings:**
- Baud Rate: `9600`
- Data Bit: `8`
- Stop Bit: `1`
- Parity: `None`
- Buffer Size: `1024`
- Gap Time: `100`
- <img width="350" height="350" alt="{E7B4D0CA-61EF-42FF-AC66-2C990CC92447}" src="https://github.com/user-attachments/assets/2c12cfb9-5e27-4f42-8286-12312379f9bc" />


**Communication Settings:**
- Protocol: `TCP Server`
- Local Port: `502`
- max 1 connection allowed
---
<img width="350" height="375" alt="{DDE042DB-5CA4-4184-A9F6-3280C5142FAC}" src="https://github.com/user-attachments/assets/6f7f7b44-7773-4fa5-8663-0195a624c6b8" />

## Installation

### Via HACS (recommended)

1. Open **HACS → Integrations**
2. Click the three-dot menu → **Custom repositories**
3. Add this repository URL, category: **Integration**
4. Search for **Next Heatpump** and install
5. Restart Home Assistant

### Manual

Copy the `custom_components/next_heatpump/` folder into your HA `config/custom_components/` directory, then restart.

---

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Next Heatpump**
3. Enter:
   - **IP address** of your RS485-TCP gateway
   - **Port** (default `502`)
   - **Slave ID** (default `1`)
   - **Scan interval** in seconds (default `45`)

---
## Schedule normal/eco mode

Brief overview: via HACS you install two things — the Scheduler integration (backend) and the matching scheduler card (frontend). Since the card doesn't automatically know which options your select.running_mode has, the customize.yaml file provides that mapping ("Standard Mode" → Normal, "Eco" → Eco/Silent). You then create the two time blocks (08:00 → Normal, 22:00 → Eco) directly in the card itself — no more YAML needed for the schedule, and fully tappable/adjustable from the dashboard.

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
| Fan settings in ECO mode| 20-60 Hz |  |
| Compressor settings in ECO mode |20- 80 Hz |  |
| Heating Curve Target | °C | Calculated: target water temp. according to the selected heating curve (Heating Setting Curve) + current outdoor temp. (T1). See Technical notes. |
| Unit Temperature Control Mode | — | Read-only. "Inlet (T6)" or "Outlet (T7)" — see Technical notes (P116) |
| Actual Controlled Water Temp | °C | T6 or T7, automatically selected based on Unit Temperature Control Mode |

---

## Technical notes (continued)

### Followed heating curve (Heating Curve Target)

The Engineering Manual (ch. 4.1.1) defines 16 fixed heating curves (H1–H8
"High Temperature Curve", L1–L8 "Low Temperature Curve"), each a table that
maps an outdoor temperature range to a target water temperature. These
tables have been transcribed into `const.py` (`HEATING_CURVES`) and are
calculated live against the current outdoor temperature (T1) and the
selected curve (`Heating Setting Curve`), with the result exposed as
`sensor.heating_curve_target`.

**Known discrepancy in the source document:** the HL4 table is missing the
outdoor temperature range 8–13°C (the manual jumps directly from
"13≤T<18" to "6≤T<8") — likely a printing/OCR error. Transcribed
literally; in that range the sensor returns `Unknown`. Verify against your
own printed manual if you use HL4 in that range.

The full curve (all breakpoints) is available as a `curve_points` attribute
on `sensor.heating_curve_target`, usable for a chart on your dashboard —
see [Dashboard: heating curve chart](#dashboard-heating-curve-chart)
below.

### P116 — Unit Temperature Control Mode

Factory parameter (register `0x0174`, manual ch. 2.8) that determines
whether the unit internally controls on the water **inlet** (T6) or water
**outlet** (T7) temperature. Deliberately **not** implemented as a
writable `select` entity — unlike Mode/Running Mode, this is not a
routine operating choice but an installation/service-time parameter, and
a dropdown would incorrectly suggest otherwise. Instead:

- `sensor.unit_temperature_control_mode` shows the current value,
  read-only.
- `sensor.actual_controlled_water_temp` automatically follows this: it
  always returns whichever of T6 or T7 the unit is actually using as its
  control reference — so other calculations (such as the heating curve
  comparison above) don't need to choose between T6/T7 themselves and
  stay correct if this parameter ever changes.

### Dashboard: heating curve chart

An example dashboard section (entities card + a chart of the selected
curve with the current point highlighted) is available in
[`dashboard/stooklijn-sectie.yaml`](dashboard/stooklijn-sectie.yaml).

**Requires: [ApexCharts Card](https://github.com/RomRider/apexcharts-card)
via HACS** (Frontend category). Home Assistant doesn't have a built-in
card that can plot a fixed function (outdoor temp. → target temp.)
independent of time series — this community card can, via its
`data_generator` option.

The chart displays the curve as a step shape (`stroke.curve: stepline`,
one point per temperature bucket) and gracefully shows a message instead
of an empty/broken chart when `Heating Setting Curve` is set to **Off**.

---

## Changelog

See [`CHANGELOG.md`](CHANGELOG.md) for the full list of bug fixes and new
features per release.


### Several Binary Sensors and fault sensors 
<img width="750" height="500" alt="{232E0B90-1DE7-421C-B3C2-22C8227567AA}" src="https://github.com/user-attachments/assets/f1a6042f-7bde-422a-be24-681d031edaaf" />



### Controls
| Entity | Type | Options / Range |
|---|---|---|
| Next Heatpump | Climate | Heat / Cool / Heat+Cool / Off |
| Heatpump ON/OFF | Switch | on / off |
| Temp Set Cooling | Number | 7–25 °C |
| Temp Set Heating | Number | 15–60 °C |
| Temp Set Floor Heating | Number | 20–60 °C |
| Mode | Select | Cooling / Heating / Hot Water / Floor Heating / combinations |
| Running Mode | Select | Standard Mode / Boost / Eco |
| Cooling Setting Curve | Select | Off, H1–H8, L1–L8 |
| Heating Setting Curve | Select | Off, H1–H8, L1–L8 |
| Underfloor Heating Setting Curve | Select | Off, H1–H8, L1–L8 |
| Hot water Setting Curve | Select | Off, 1-4 |
| Temp setting auxiliary heating P22 | Select | temp value |
| Min Flow Protection | Number | 0–100 L/min — factory parameter ("Low protection value - Water flow rate", register 0x0186). Protection against too-low water flow. |
|Compressor Forced Control	Switch	on / off — |forces manual compressor frequency
|Fan Forced Control	Switch	on / off — |forces manual fan speed
|Compressor Forced Frequency	Number	0–120 Hz —|only active while "Compressor Forced Control" is on
|Fan Forced Speed	Number	0–80 Hz — |only active while "Fan Forced Control" is on
|Silent Mode - Compressor Max Frequency	Number	|20–70 Hz —| upper limit during Silent/Eco mode (factory parameter P88)
|Silent Mode - Fan Max Frequency	Number	|20–60 Hz — |upper limit during Silent/Eco mode (factory parameter P89)

## Technical notes

## "Silent Mode frequency limits (P88/P89)"

Registers 0x0158 (compressor, 20–70 Hz) and 0x0159 (fan, 20–60 Hz) from the "System Parameters P" section (0x0100–0x02FF) of the Engineering Manual. These are the same limit values that are adjustable on the control display under the installer password (P88/P89, "Silent Mode" chapter) — intended to reduce noise nuisance.
This is not a forced value: within this limit, the heat pump simply keeps controlling itself based on demand/pressure/temperature. The limit only applies while the unit is running in Silent/Eco mode (set the existing "Running Mode" select entity to "Eco"). With these two registers, the control display is therefore no longer needed to adjust these values.

## "Forced control (compressor/fan)"

As of this version you can manually lock the compressor frequency and fan speed, based on register 0x0331 ("Load Forcing Control") and the corresponding value registers 0x0332 (compressor, 0–120 Hz) and 0x033E (fan, 0–80 Hz) from the Engineering Manual.

### This is a service/commissioning function, NOT A NORMAL CONTROL BUTTON. USE IN TEST MODE ONLY
As long as the corresponding "Forced Control" switch is on, the heat pump ignores its own control loop for that component and holds the configured frequency/speed — without correcting itself based on pressure, temperature, or other safety limits.
## Always turn the switch back off after use, or don't use it and remove the entities from your list!
Incorrect use of this function can damage the heat pump or cause unsafe operating conditions (e.g. too high/low pressure). Use at your own risk — see the disclaimer at the bottom of this document.


### Scan interval
The default scan interval is 45 seconds. With ~40 registers × 200ms delay = ~8 seconds per poll cycle, a minimum of 30 seconds is recommended.

---

### DISCLAIMER
**This integration is community-developed and not affiliated with Heative, Adlår or SolarEast. USE AT YOUR OWN RISK. Incorrect writes to control registers could affect heat pump operation. Always verify setpoints before applying changes.** Use of logo is approved by Heative, thanks!
