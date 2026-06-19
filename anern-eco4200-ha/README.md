# Anern ECO-4200 + SmartESS → Home Assistant

Paruoštas diegimo paketas **Anern ECO-4200** (AN-SCI-EVO4200) su **Wi-Fi Plug Pro** ir **SmartESS** programėle.

## Jūsų įrenginys

| Parametras | Reikšmė |
|-----------|---------|
| Inverteris | Anern ECO-4200 / AN-SCI-EVO4200 |
| WiFi adapteris | Wi-Fi Plug Pro (EyeBond / Eybond) |
| Programėlė | SmartESS |
| Debesies portalas | https://www.dessmonitor.com |
| LAN portai | TCP **8899**, UDP **58899** |
| HA protokolai | devcode **2428** arba **2341** |

## Greitas startas (5 min)

### 1. Suraskite Wi-Fi Plug Pro IP

**Windows (PowerShell):**

```powershell
cd C:\Users\euepa\Desktop\Mobilus
# Nukopijuokite scripts aplanką iš šio repo arba paleiskite tiesiai:
powershell -ExecutionPolicy Bypass -File .\anern-eco4200-ha\scripts\find-smartess-inverter.ps1
```

**Home Assistant SSH / Linux:**

```bash
bash anern-eco4200-ha/scripts/find-smartess-inverter.sh
```

Skriptas ieško įrenginio su atviru **TCP 8899** portu ir išsaugo IP į `found-smartess-ip.txt`.

### 2. Rezervuokite statinį IP routeryje

Routerio admin → DHCP → rezervacija Wi-Fi Plug Pro (hostname dažnai `W00...` arba `ESP_...`).

### 3. Prijunkite prie Home Assistant

Pasirinkite **vieną** variantą:

#### A) DESS Monitor (paprasčiausia, per debesį)

Žr. [home-assistant/dess-monitor-hacs.txt](home-assistant/dess-monitor-hacs.txt)

- Prisijungimas su SmartESS / dessmonitor.com paskyra
- Duomenys kas 5 min (arba 10 s su direct mode)
- **Patikrinta su Anern ECO-4200**

#### B) SmartESS Local (LAN, be debesies — rekomenduojama)

Žr. [home-assistant/smartess-local-hacs.txt](home-assistant/smartess-local-hacs.txt)

- Duomenys tiesiai iš loggerio per TCP 8899
- Atnaujinimas kas ~5–10 s
- SmartESS programėlė gali veikti kartu

## SmartESS programėlėje (jei reikia PN)

**Device Information** ekrane ieškokite:

- **PN** — Wi-Fi Plug Pro serija (pvz. `W0016250020617`)
- **SN** — inverterio serija
- **DevCode** — `2428` arba `2341`
- **DevAddr** — dažniausiai `1`

PN numeris padeda identifikuoti įrenginį routerio DHCP sąraše.

## Troubleshooting

| Problema | Sprendimas |
|---------|------------|
| Skriptas neranda 8899 | Patikrinkite, ar loggeris prisijungęs prie to paties Wi-Fi; SmartESS → 4 LED degantys |
| HA neprisijungia (Local) | HA ir loggeris tame pačiame LAN; išjunkite VLAN izoliaciją |
| DESS Monitor neprisijungia | Naudokite tą patį el. paštą kaip SmartESS; patikrinkite dessmonitor.com |
| IP keičiasi | Rezervuokite statinį IP routeryje |

## Failų struktūra

```
anern-eco4200-ha/
├── README.md
├── scripts/
│   ├── find-smartess-inverter.ps1   # Windows tinklo paieška
│   ├── find-smartess-inverter.sh    # Linux/HA SSH paieška
│   └── found-smartess-ip.txt        # sukuriamas po sėkmingos paieškos
└── home-assistant/
    ├── dess-monitor-hacs.txt        # Debesies integracija
    └── smartess-local-hacs.txt      # Vietinė LAN integracija
```
