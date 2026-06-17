# Kompiuterių įjungimas per LAN (Wake-on-LAN)

Įrankis kompiuteriams **nuotoliniu būdu įjungti per vietinį tinklą** naudojant Wake-on-LAN (WoL) technologiją.

## Kaip tai veikia

Wake-on-LAN siunčia specialų **magic packet** UDP paketą į tikslinio kompiuterio MAC adresą. Jei kompiuteris yra išjungtas (bet prijungtas prie elektros ir tinklo), tinklo plokštė gali priimti šį paketą ir įjungti sistemą.

```
  [Jūsų PC]  ──UDP magic packet──►  [Tinklo plokštė]  ──►  [Kompiuteris įsijungia]
              255.255.255.255:9         (MAC adresas)
```

## Reikalavimai tiksliniam kompiuteriui

1. **BIOS/UEFI** – įjunkite *Wake on LAN*, *Power On By PCI-E* ar panašią parinktį
2. **Tinklo plokštės tvarkyklė** – įjunkite *Wake on Magic Packet*
3. Kompiuteris turi būti **prijungtas prie elektros** (gali būti soft-off, ne visiškai atjungtas nuo rozetės)
4. **Laidinis Ethernet** – dauguma Wi-Fi adapterių WoL nepalaiko (arba tik sleep, ne pilnas shutdown)

## Diegimas

```bash
git clone <repo-url>
cd projektai
# Python 3.10+ reikalingas
```

## Naudojimas

### Įjungti pagal MAC adresą

```bash
python -m wol AA:BB:CC:DD:EE:FF
```

### Naudoti kompiuterių konfigūraciją

```bash
cp computers.json.example computers.json
# Redaguokite computers.json – įrašykite tikrus MAC adresus
python -m wol biuro-pc
```

### Parodyti kompiuterių sąrašą

```bash
python -m wol --list
```

### Papildomos parinktys

| Parinktis | Aprašymas |
|-----------|-----------|
| `-b`, `--broadcast` | Transliacijos IP (pvz. `192.168.1.255`) |
| `-p`, `--port` | UDP prievadas (numatytasis: 9) |
| `-i`, `--interface` | Vietinės sąsajos IP |
| `-c`, `--config` | Kelias į `computers.json` |

### Subnet broadcast (rekomenduojama)

Vietoj `255.255.255.255` dažnai geriau naudoti subnet broadcast, pvz. `192.168.1.255`:

```bash
python -m wol -b 192.168.1.255 AA:BB:CC:DD:EE:FF
```

## Kaip sužinoti MAC adresą

**Windows:** `ipconfig /all` → „Physical Address“

**Linux:** `ip link` arba `ip a`

**Maršrutizatoriuje:** DHCP klientų sąraše

## Konfigūracijos failas

`computers.json` pavyzdys:

```json
{
  "biuro-pc": {
    "mac": "AA:BB:CC:DD:EE:FF",
    "description": "Biuro stacionarus kompiuteris",
    "broadcast": "192.168.1.255"
  }
}
```

## Įjungimas iš kito tinklo (internetas)

Wake-on-LAN veikia tik **toje pačioje subnet** arba su maršrutizatoriaus konfigūracija:

- Įjunkite **port forwarding** UDP 9 (arba 7) į transliacijos adresą
- Kai kurie maršrutizatoriai turi integruotą WoL funkciją
- Alternatyva: VPN į namų tinklą, tada siųskite paketą kaip įprastai

## Programinis naudojimas

```python
from wol import wake

wake("AA:BB:CC:DD:EE:FF", ip_address="192.168.1.255")
```

## Licencija

Laisvai naudokite ir modifikuokite pagal poreikį.
