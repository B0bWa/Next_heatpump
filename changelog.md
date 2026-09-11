# Wijzigingen — [11-9-2024]

## 🐛 Bugfixes

### Thermal Power / COP toonden altijd 0
**Bestand:** `sensor.py`
`NextThermalPowerSensor` en `NextCOPSensor` zochten naar de register-sleutels
`"Water Inlet Temp T6"` / `"Water Outlet Temp T7"` (zonder punt), terwijl
`const.py` ze als `"Water Inlet Temp. T6"` / `"Water Outlet Temp. T7"` (mét
punt) registreert. Door de ontbrekende punt gaf `data.get(...)` altijd
`None` terug, viel de berekening stil terug op `0`, en toonde Thermal Power
daardoor permanent **0,00 kW** (geen foutmelding — de bug was onzichtbaar
zonder de sleutelnamen te vergelijken).

### Calculated Power gaf altijd "Onbekend"
**Bestand:** `sensor.py`
`NextCalculatedPowerSensor` zocht naar `"Supply Line Voltage"` en
`"Compressor Current Draw"` — sleutels die nergens in `const.py` bestaan.
Vervangen door `"AC Input Voltage"` × `"Compressor Phase Current"`
(compressor-niveau spanning/stroom, de meest logische beschikbare match).

## ✨ Nieuwe features

### Min Flow Protection instelbaar
**Bestand:** `const.py`
Fabrieksparameter uit de handleiding (`0x0186`, "Low protection value -
Water flow rate") toegevoegd aan `NUMBER_REGISTERS`. Bereik 0-100 L/min.
⚠️ Fabrieksparameter — pas alleen wijzigen met een concrete reden; te hoog
kan de beveiliging onterecht laten aanslaan, te laag vermindert de
bescherming tegen te weinig waterdoorstroming.

### Gevolgde stooklijn zichtbaar maken
**Bestanden:** `const.py`, `sensor.py`
- `HEATING_CURVES` in `const.py`: complete HH1-HH8/HL1-HL8 curve-tabellen
  overgenomen uit de handleiding (hfst. 4.1.1), plus
  `get_heating_curve_target(curve_name, ambient_temp)` als lookup-helper.
- **Let op**: in de HL4-tabel ontbreekt in de handleiding zelf het bereik
  8-13°C (waarschijnlijk een druk-/OCR-fout in het brondocument) — hier
  letterlijk overgenomen, dus in dat bereik geeft de lookup `None` terug.
  Verifieer dit tegen de papieren handleiding als je HL4 gebruikt.
- Nieuwe entiteit `sensor.heating_curve_target`: berekent live de
  doel-watertemperatuur op basis van de gekozen curve
  (`select.heating_setting_curve`) en de actuele buitentemperatuur (T1).
  De volledige curve staat als `curve_points`-attribuut op de sensor, voor
  eventuele grafiekweergave.

### P116 Unit Temperature Control Mode
**Bestanden:** `const.py`, `coordinator.py`, `sensor.py`
Fabrieksparameter (`0x0174`, handleiding hfst. 2.8) bepaalt of de unit
regelt op de water-**inlet** (T6) of water-**outlet** (T7) temperatuur.
Bewust **niet** als schrijfbare `select` toegevoegd (dat suggereert ten
onrechte een routinematige keuze, zoals Mode/Running Mode) — in plaats
daarvan:
- `sensor.unit_temperature_control_mode`: alleen-lezen weergave van de
  huidige P116-waarde ("Inlet (T6)" / "Outlet (T7)").
- `sensor.actual_controlled_water_temp`: geeft **automatisch** T6 óf T7
  terug, afhankelijk van de live P116-waarde — zodat andere vergelijkingen
  (zoals de stooklijn) niet zelf hoeven te kiezen tussen T6/T7 en correct
  blijven als deze parameter ooit wijzigt.

## 📊 Dashboard: stooklijn-visualisatie

Nieuwe dashboardsectie met:
1. Een entities-kaart (gekozen curve, regelmodus, buitentemp., doeltemp.,
   T6, T7)
2. Een grafiek van de volledige geselecteerde curve (trapvorm/stepline),
   met een los gemarkeerd punt voor de huidige, werkelijke positie
3. Nette "Off"-afhandeling via een conditionele kaart (i.p.v. een lege,
   kapotte grafiek wanneer er geen curve actief is)

**Vereist: [ApexCharts Card](https://github.com/RomRider/apexcharts-card)
via HACS** (Frontend-categorie) — de grafiek is gebaseerd op deze
community-kaart, niet op een kale Home Assistant kaart, omdat HA zelf geen
ingebouwde manier heeft om een vaste functie (buitentemp. → doeltemp.)
te plotten los van tijdreeksen.

Voorbeeldconfiguratie: zie `dashboard/stooklijn-sectie.yaml` in deze
release.

## Nieuwe entiteiten in deze release
| Entiteit | Type | Omschrijving |
|---|---|---|
| `number.min_flow_protection` | number | Fabrieksparameter min. doorstroming (L/min) |
| `sensor.heating_curve_target` | sensor | Doeltemp. volgens gekozen stooklijn + buitentemp. |
| `sensor.unit_temperature_control_mode` | sensor | P116, alleen-lezen (Inlet T6 / Outlet T7) |
| `sensor.actual_controlled_water_temp` | sensor | T6 of T7, automatisch op basis van P116 |
