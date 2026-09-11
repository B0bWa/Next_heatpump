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

###  Or disconnect TFT display and use this repository with EW11A instead. Both connected on the display connection rs485 WILL NOT WORK!
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
## Schema normal/ eco modus

Kort de opzet: je installeert via HACS twee dingen — de Scheduler-integratie (backend) en de bijbehorende scheduler-card (frontend). Omdat de kaart niet vanzelf weet welke opties jouw select.running_mode heeft, geeft het bestand  customize.yaml die koppeling mee ("Standard Mode" → Normaal, "Eco" → Eco/Silent). Daarna maak je de twee tijdsblokken (08:00 → Normaal, 22:00 → Eco) rechtstreeks in de kaart zelf aan — geen YAML meer nodig voor het schema, en volledig tikbaar/aanpasbaar vanaf het dashboard.

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
| Heating Curve Target | °C | Calculated: doel-watertemp. volgens de gekozen stooklijn (Heating Setting Curve) + actuele buitentemp. (T1). Zie Technical notes. |
| Unit Temperature Control Mode | — | Read-only. "Inlet (T6)" of "Outlet (T7)" — zie Technical notes (P116) |
| Actual Controlled Water Temp | °C | T6 of T7, automatisch gekozen op basis van Unit Temperature Control Mode |

---

## Technical notes (vervolg)

### Gevolgde stooklijn (Heating Curve Target)

De Engineering Manual (hfst. 4.1.1) definieert 16 vaste stooklijnen (H1–H8
"High Temperature Curve", L1–L8 "Low Temperature Curve"), elk een tabel die
een buitentemperatuur-bereik koppelt aan een doel-watertemperatuur. Deze
tabellen zijn overgenomen in `const.py` (`HEATING_CURVES`) en worden live
doorgerekend tegen de actuele buitentemperatuur (T1) en de gekozen curve
(`Heating Setting Curve`), resultaat in `sensor.heating_curve_target`.

**Bekende afwijking in het brondocument:** in de HL4-tabel ontbreekt het
buitentemperatuurbereik 8–13°C (springt in de manual direct van "13≤T<18"
naar "6≤T<8") — vermoedelijk een druk-/OCR-fout. Letterlijk overgenomen;
in dat bereik geeft de sensor `Onbekend` terug. Verifieer tegen je eigen
papieren handleiding als je HL4 in dat bereik gebruikt.

De volledige curve (alle breekpunten) staat als `curve_points`-attribuut op
`sensor.heating_curve_target`, bruikbaar voor een grafiekweergave op je
dashboard — zie [Dashboard: stooklijn-grafiek](#dashboard-stooklijn-grafiek)
hieronder.

### P116 — Unit Temperature Control Mode

Fabrieksparameter (register `0x0174`, manual hfst. 2.8) die bepaalt of de
unit intern regelt op de water-**inlet** (T6) of water-**outlet** (T7)
temperatuur. Bewust **niet** geïmplementeerd als schrijfbare `select`
entiteit — in tegenstelling tot Mode/Running Mode is dit geen routinematige
bedieningskeuze maar een installatie-/servicetijdsparameter, en een
dropdown-weergave zou dat ten onrechte suggereren. In plaats daarvan:

- `sensor.unit_temperature_control_mode` toont de huidige waarde,
  alleen-lezen.
- `sensor.actual_controlled_water_temp` volgt hier automatisch op: geeft
  altijd T6 of T7 terug, wat de unit ook daadwerkelijk als regelreferentie
  gebruikt — zodat andere berekeningen (zoals de stooklijn-vergelijking
  hierboven) niet zelf hoeven te kiezen tussen T6/T7 en correct blijven als
  deze parameter ooit wijzigt.

### Dashboard: stooklijn-grafiek

Een voorbeeld-dashboardsectie (entities-kaart + grafiek van de gekozen
curve met een gemarkeerd huidig-punt) staat in
[`dashboard/stooklijn-sectie.yaml`](dashboard/stooklijn-sectie.yaml).

**Vereist: [ApexCharts Card](https://github.com/RomRider/apexcharts-card)
via HACS** (categorie Frontend). Home Assistant heeft standaard geen kaart
die een vaste functie (buitentemp. → doeltemp.) kan plotten los van
tijdreeksen — deze community-kaart wel, via zijn `data_generator`-optie.

De grafiek toont de curve als trapvorm (`stroke.curve: stepline`, één punt
per temperatuurbucket) en sluit netjes af met een bericht in plaats van een
lege/kapotte grafiek wanneer `Heating Setting Curve` op **Off** staat.

---

## Changelog

Zie [`CHANGELOG.md`](CHANGELOG.md) voor de volledige lijst met bugfixes en
nieuwe features per release.


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
| Min Flow Protection | Number | 0–100 L/min — fabrieksparameter ("Low protection value - Water flow rate", register 0x0186). Bescherming tegen te lage waterdoorstroming. |
|Compressor Forced Control	Switch	on / off — |dwingt handmatige compressorfrequentie af
|Fan Forced Control	Switch	on / off — |dwingt handmatige ventilatorsnelheid af
|Compressor Forced Frequency	Number	0–120 Hz —|alleen actief zolang "Compressor Forced Control" aan staat
|Fan Forced Speed	Number	0–80 Hz — |alleen actief zolang "Fan Forced Control" aan staat
|Silent Mode - Compressor Max Frequency	Number	|20–70 Hz —| bovengrens tijdens Silent/Eco-modus (fabrieksparameter P88)
|Silent Mode - Fan Max Frequency	Number	|20–60 Hz — |bovengrens tijdens Silent/Eco-modus (fabrieksparameter P89)

## Technical notes

## "Silent Mode frequentiegrenzen (P88/P89)"

Registers 0x0158 (compressor, 20–70 Hz) en 0x0159 (ventilator, 20–60 Hz) uit de "System Parameters P"-sectie (0x0100–0x02FF) van de Engineering Manual. Dit zijn dezelfde grenswaarden die op het bediendisplay onder installateurswachtwoord instelbaar zijn (P88/P89, hoofdstuk "Silent Mode") — bedoeld om geluidsoverlast te beperken.
Dit is geen forceerwaarde: de warmtepomp blijft binnen deze grens gewoon zelf regelen op basis van vraag/druk/temperatuur. De grens geldt alleen zolang de unit in Silent/Eco-modus draait (zet de bestaande "Running Mode" select-entiteit op "Eco"). Met deze twee registers is het bediendisplay dus niet meer nodig om deze waarden aan te passen.

## "Forced control (compressor/fan)"

Sinds deze versie kun je de compressorfrequentie en ventilatorsnelheid handmatig vastzetten, gebaseerd op register 0x0331 ("Load Forcing Control") en de bijbehorende waarderegisters 0x0332 (compressor, 0–120 Hz) en 0x033E (ventilator, 0–80 Hz) uit de Engineering Manual.

### Dit is een service-/commissioningfunctie, GEEN NORMALE BEDIENINGSKNOP. ALLEEN GEBRUIKEN IN TESTMODUS
Zolang de bijbehorende "Forced Control"-switch aan staat, negeert de warmtepomp zijn eigen regellus voor dat onderdeel en houdt hij de ingestelde frequentie/snelheid aan — zonder zelf te corrigeren op basis van druk, temperatuur of andere veiligheidsgrenzen.
## Zet de switch na gebruik altijd weer uit of gebruik het niet en verwijder de entiteiten uit je lijst!
Incorrect gebruik van deze functie kan de warmtepomp beschadigen of onveilige bedrijfscondities veroorzaken (bijv. te hoge/lage druk). Gebruik op eigen risico — zie de disclaimer onderaan dit document.


### Scan interval
The default scan interval is 45 seconds. With ~40 registers × 200ms delay = ~8 seconds per poll cycle, a minimum of 30 seconds is recommended.

---

### DISCLAIMER
**This integration is community-developed and not affiliated with Heative, Adlår or SolarEast. USE AT YOUR OWN RISK. Incorrect writes to control registers could affect heat pump operation. Always verify setpoints before applying changes.** Use of logo is approved by Heative, thanks!
