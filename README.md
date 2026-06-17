# Instalika Power

**Kompiuterių įjungimas per LAN** – Wake-on-LAN (WoL) įrankis nuo **Instalika**.

| Platforma | Kaip paleisti |
|-----------|---------------|
| **Android** | Atidarykite `android/` Android Studio → Run |
| **Web panelė** | `apsa-power.bat` arba `python -m apsa_power --web` |
| **Komandinė eilutė** | `python -m apsa_power biuro-pc` |

## Android (Instalika Power v1.1)

- Įjungti vieną ar **visus** kompiuterius
- Magic packet **pakartojimai** (patikimumui)
- Auto **broadcast** iš Wi-Fi
- **Importas/eksportas** JSON

Detalės: [android/README.md](android/README.md)

## PC greitas startas

```bash
cp computers.json.example computers.json
python -m apsa_power --web
# http://localhost:8080
```

## Kompiuterių konfigūracija

```json
{
  "biuro-pc": {
    "mac": "AA:BB:CC:DD:EE:FF",
    "broadcast": "192.168.1.255",
    "description": "Biuro PC"
  }
}
```

## PC reikalavimai

| Nustatymas | Kur |
|------------|-----|
| Wake on LAN | BIOS |
| Wake on Magic Packet | Tinklo plokštė |
| Ethernet laidas | Wi-Fi PC nepalaiko WoL |

## Netikėtas išsijungimas?

Jei kompiuteris pats išsijungia (pvz. `192.168.0.97`) ir reikia vėl įjungti rankiniu būdu – **Instalika Power jo neišjungia** (tik WoL įjungimas). Žiūrėkite [išjungimo diagnostiką](docs/issijungimo-diagnostika.md) ir paleiskite `scripts/diagnose-shutdown.ps1` ant Windows PC.

## Temperatūros ir kompiuterio būsena

BIOS duomenis ir temperatūras galima nuskaityti **tik ant pačio PC** (ne iš debesies):

```powershell
powershell -ExecutionPolicy Bypass -File scripts\hardware-status.ps1
```

Detalės: [kompiuterio būsena](docs/kompiuterio-busena.md)

---

**Instalika Power** – IT sprendimai | instalika.eu
