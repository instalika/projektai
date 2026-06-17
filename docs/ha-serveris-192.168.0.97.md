# Home Assistant serveris (192.168.0.97) – diagnostika ir išvados

`192.168.0.97` – tai **Home Assistant serveris**, ne įprastas Windows PC.

## Kas atlikta automatiškai (iš debesies)

| Tikrinimas | Rezultatas |
|------------|------------|
| DNS `192.168.0.97` | **`ip-192-168-0-97.ec2.internal`** – tai AWS vidinis adresas, NE jūsų namų HA |
| Ping | Neatsako (ICMP blokuojamas) |
| Prievadai 8123, 22, 4357 | TCP prisijungia, bet **Connection reset** – klaidingas debesies atsakas |
| HA API / web | **Neprieinama** (tikras serveris nepasiektas) |

> **Išvada:** iš Cursor debesies **negalima** tikrinti jūsų namų HA serverio. Visi „atviri" prievadai – klaidingi (debesies tinklas). Diagnostiką paleiskite **iš namų Wi-Fi**.

> **Išvada:** iš Cursor debesies negalima tiesiogiai nuskaityti jūsų HA serverio. Diagnostiką reikia paleisti **iš jūsų tinklo** arba **ant paties serverio**.

---

## Įrankiai (repozitorijoje)

| Skriptas | Kur paleisti | Paskirtis |
|----------|--------------|-----------|
| `scripts/ha-remote-probe.sh` | Bet kuris PC telefone/LAN | Ar HA gyvas, MAC WoL |
| `scripts/ha-server-diagnose.sh` | Ant HA serverio (SSH) | Temperatūros, OOM, reboot logai, automacijos |

```bash
# Iš kompiuterio tame pačiame Wi-Fi:
bash scripts/ha-remote-probe.sh 192.168.0.97

# Ant HA serverio (SSH / Terminal add-on):
bash scripts/ha-server-diagnose.sh
```

---

## Išvados – kodėl HA serveris išsijungia

Remiantis tipine HA infrastruktūra ir tuo, kad serveris kartais **visiškai nebepasiekiamas** (reikia rankinio įjungimo):

### 1. Labiausiai tikėtina (90% atvejų)

| Priežastis | Požymiai | Sprendimas |
|------------|----------|------------|
| **Maitinimo nutraukimas** | Visiškai nepingina; kartais po audros/laiko | Patikimas PSU; ne smart kištukas be UPS |
| **OOM (per mažai RAM)** | RPi; loguose `oom-kill`; reboot be įspėjimo | Daugiau RAM (NUC), mažiau add-onų, swap |
| **Perkaitimas (RPi)** | >80°C; throttling | Ventiliatorius, radiatorius, atviresnė vieta |
| **SD kortelės gedimas** | Korupcija, lėtas HA, staigus death | SSD boot (USB/NUC), backup |

### 2. Galima, bet rečiau

| Priežastis | Kaip patikrinti |
|------------|-----------------|
| **HA automacija su shutdown** | `ha-server-diagnose.sh` skyrius 8; HA → Automacijos |
| **HA OS auto-update + reboot** | Supervisor logai; nustatykite maintenance langą |
| **Smart kištukas išjungia** | Ar serveris prijungtas per relę? |
| **UPS išsikrovė** | UPS logai |

### 3. Mažai tikėtina

- **Instalika Power / WoL** – tik **įjungia**, neišjungia
- **Išorinis hakeris shutdown** – labai reta namų tinkle

---

## Rekomenduojami veiksmai (prioritetas)

1. **Įjunkite serverį** ir iš LAN paleiskite: `bash scripts/ha-remote-probe.sh 192.168.0.97`
2. **SSH į serverį** ir paleiskite: `bash scripts/ha-server-diagnose.sh`
3. **Patikrinkite HA automacijas** – filtras: `shutdown`, `reboot`, `host_shutdown`
4. **Jei RPi** – pridėkite ventiliatorių, perkelkite ant SSD
5. **WoL įjungimui** – įrašykite MAC į Instalika Power `computers.json`

---

## Home Assistant monitoring (nuolat)

Kai serveris vėl veikia, pridėkite į `configuration.yaml`:

```yaml
command_line:
  - sensor:
      name: "HA serverio temperatūra"
      command: "cat /sys/class/thermal/thermal_zone0/temp | awk '{print $1/1000}'"
      unit_of_measurement: "°C"
      scan_interval: 120
```

Arba naudokite **System Monitor** integraciją.

---

**Instalika** | instalika.eu
