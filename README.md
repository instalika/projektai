# APSA Power Instalika

**Kompiuterių įjungimas per LAN** – Wake-on-LAN (WoL) įrankis nuo **Instalika**.

Siunčia magic packet UDP paketą į kompiuterio MAC adresą ir nuotoliniu būdu įjungia sistemą.

```
  [Valdymo PC]  ──UDP magic packet──►  [Tinklo plokštė]  ──►  [Kompiuteris įsijungia]
```

## Greitas startas

### Web valdymo panelė (rekomenduojama)

**Windows:** dukart spustelėkite `apsa-power.bat`

**Linux / macOS:**
```bash
chmod +x apsa-power.sh
./apsa-power.sh
```

Atidarykite naršyklėje: **http://localhost:8080**

### Komandinė eilutė

```bash
# Įjungti pagal MAC
python -m apsa_power AA:BB:CC:DD:EE:FF

# Įjungti pagal vardą iš sąrašo
python -m apsa_power biuro-pc

# Parodyti kompiuterių sąrašą
python -m apsa_power --list
```

## Diegimas

1. Atsisiųskite arba klonuokite repozitoriją
2. Reikalingas **Python 3.10+** (papildomų bibliotekų nereikia)
3. Nukopijuokite konfigūraciją:
   ```bash
   cp computers.json.example computers.json
   ```
4. Redaguokite `computers.json` – įrašykite tikrus MAC adresus

## Kompiuterių konfigūracija

`computers.json` pavyzdys:

```json
{
  "biuro-pc": {
    "mac": "AA:BB:CC:DD:EE:FF",
    "description": "Biuro stacionarus kompiuteris",
    "broadcast": "192.168.1.255"
  },
  "namu-serveris": {
    "mac": "11:22:33:44:55:66",
    "description": "Namų NAS serveris",
    "broadcast": "192.168.1.255"
  }
}
```

## Reikalavimai tiksliniam kompiuteriui

| Nustatymas | Kur |
|------------|-----|
| Wake on LAN / Power On By PCI-E | BIOS / UEFI |
| Wake on Magic Packet | Tinklo plokštės tvarkyklė (Windows: Įrenginių tvarkyklė) |
| Laidinis Ethernet | Wi-Fi dažniausiai nepalaiko pilno WoL |
| Prijungtas prie elektros | Soft-off režimas (ne iš rozetės) |

## Kaip sužinoti MAC adresą

- **Windows:** `ipconfig /all` → Physical Address
- **Linux:** `ip link` arba `ip a`
- **Maršrutizatorius:** DHCP klientų sąrašas

## Visos komandos

| Komanda | Aprašymas |
|---------|-----------|
| `python -m apsa_power --web` | Web valdymo panelė |
| `python -m apsa_power --list` | Kompiuterių sąrašas |
| `python -m apsa_power -b 192.168.1.255 MAC` | Subnet broadcast |
| `python -m apsa_power --web --host 0.0.0.0` | Panelė visam tinklui |

## Įjungimas iš kito tinklo

WoL veikia toje pačioje subnet. Iš interneto:
- VPN į namų tinklą, tada naudokite kaip įprastai
- Maršrutizatoriaus port forwarding UDP 9 → broadcast adresas
- Kai kurie maršrutizatoriai turi integruotą WoL

## Programinis naudojimas

```python
from apsa_power import wake

wake("AA:BB:CC:DD:EE:FF", ip_address="192.168.1.255")
```

## Failų struktūra

```
apsa_power/          # Pagrindinis paketas
  cli.py             # Komandinė eilutė
  web.py             # Web valdymo panelė
  wake.py            # Magic packet logika
apsa-power.bat       # Windows paleidimas
apsa-power.sh        # Linux paleidimas
computers.json       # Jūsų kompiuterių sąrašas
```

---

**APSA Power Instalika** v1.0 – IT sprendimai
