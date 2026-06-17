# HA serverio PC monitorius (192.168.0.97)

Momentiniai duomenys Apžvalgoje: **CPU, RAM, temperatūra, diskas, ventiliatorius, apkrova** + grafikai ir statistika.

## Kas sukurtа

| Failas | Paskirtis |
|--------|-----------|
| `scripts/ha-host-metrics.sh` | Skaito metrikas iš HA OS (Linux) |
| `packages/ha_host_monitor.yaml` | Sensoriai, šablonai, statistika |
| `dashboards/ha_host_dashboard.yaml` | Skydelis su grafikais |
| `lovelace/apzvalga_ha_pc_mygtukas.yaml` | Mygtukas Apžvalgai |

## Greitas įdiegimas (HA OS)

### 1. Terminal & SSH add-on

**Nustatymai → Add-ons → Terminal & SSH** → atidarykite terminalą.

### 2. Nukopijuokite failus į `/config`

```bash
cd /config
mkdir -p scripts packages dashboards lovelace

# Atsisiųsti iš GitHub (arba kopijuoti ranka per Samba/File editor)
curl -fsSL "https://raw.githubusercontent.com/instalika/projektai/cursor/ha-pc-monitor-3ac6/homeassistant/scripts/ha-host-metrics.sh" -o scripts/ha-host-metrics.sh
curl -fsSL "https://raw.githubusercontent.com/instalika/projektai/cursor/ha-pc-monitor-3ac6/homeassistant/packages/ha_host_monitor.yaml" -o packages/ha_host_monitor.yaml
curl -fsSL "https://raw.githubusercontent.com/instalika/projektai/cursor/ha-pc-monitor-3ac6/homeassistant/dashboards/ha_host_dashboard.yaml" -o dashboards/ha_host_dashboard.yaml

chmod +x scripts/ha-host-metrics.sh
```

### 3. `configuration.yaml`

Pridėkite (jei dar nėra):

```yaml
homeassistant:
  packages: !include_dir_named packages
```

### 4. Perkraukite HA

**Nustatymai → Sistema → Perkrauti**

### 5. Patikrinkite sensorius

**Developer Tools → States** → ieškokite `sensor.ha_host_`

Turėtumėte matyti:
- `sensor.ha_host_cpu_temperatura`
- `sensor.ha_host_cpu_naudojimas`
- `sensor.ha_host_ram_naudojimas`
- `sensor.ha_host_disk_laisva`
- `sensor.ha_host_ventiliatorius_rpm`
- `sensor.ha_host_ip` (turėtų rodyti `192.168.0.97`)

### 6. Skydelis

**Nustatymai → Skydeliai → Pridėti skydelį → Importuoti** → įklijuokite `dashboards/ha_host_dashboard.yaml` turinį.

URL: `/ha-host-dashboard/ha-pc`

### 7. Mygtukas Apžvalgoje

**Apžvalga → Redaguoti → Pridėti kortelę → Rankinis (YAML)** → įklijuokite `lovelace/apzvalga_ha_pc_mygtukas.yaml` turinį.

Paspaudus mygtuką **HA Serveris PC** → atsidaro momentiniai duomenys ir grafikai.

---

## Papildomai (rekomenduojama)

### System Monitor integracija

**Nustatymai → Įrenginiai → Pridėti → System monitor**

Įjunkite: CPU, RAM, diskas, temperatūra, load, last boot.

Tai dubliuoja dalį duomenų, bet yra oficialus HA būdas.

---

## Ventiliatorius / temperatūra

- **Temperatūra:** skaitoma iš `/sys/class/thermal/` (veikia daugumoje HA OS įrenginių)
- **Ventiliatorius RPM:** `/sys/class/hwmon/` – jei `unknown`, jūsų mainboard nepateikia RPM per Linux (normalu ant kai kurių NUC/PC)

---

## Grafikai ir statistika

- **history-graph** – paskutinės 24 val. momentiniai duomenys
- **statistics-graph** – 7 dienų vidurkiai/min/max (renkami automatiškai per `recorder`)
- **statistics sensoriai** – 24 h vidurkiai (`sensor.ha_host_cpu_vidurkis_24h` ir kt.)

---

## Testas terminale

```bash
bash /config/scripts/ha-host-metrics.sh json
```

---

**Instalika** | instalika.eu
