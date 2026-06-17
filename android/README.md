# Instalika Power – Android

**Instalika Power** – kompiuterių įjungimas per LAN (Wake-on-LAN).

Versija **1.1.0**

## Funkcijos

- Vieno paspaudimo **Įjungti** kiekvienam kompiuteriui
- **Įjungti visus** vienu metu
- **3× magic packet** (nustatoma 1–10) – patikimesnis įjungimas
- Automatinis **Wi-Fi broadcast** (pvz. `192.168.1.255`)
- **Importas / eksportas** JSON (suderinama su PC `computers.json`)
- **Dalintis** kompiuterių sąrašu
- Individualus **UDP prievadas** kiekvienam PC
- Wi-Fi būsenos indikatorius

## Diegimas ant telefono

1. [Atsisiųskite Android Studio](https://developer.android.com/studio)
2. **File → Open** → `android/` aplankas
3. Prijunkite telefoną (USB derinimas) arba emuliatorių
4. Paspauskite **Run** ▶

## APK surinkimas

```bash
cd android
./gradlew assembleDebug
```

APK: `app/build/outputs/apk/debug/app-debug.apk`

Nukopijuokite į telefoną ir įdiekite (leiskite nežinomų šaltinių programėles).

## Naudojimas

1. Telefonas ir PC turi būti **tame pačiame Wi-Fi**
2. Pridėkite kompiuterį: **+** → vardas, MAC, broadcast
3. Spauskite **Įjungti**

### Importas iš PC

PC faile `computers.json`:
```json
{
  "biuro-pc": {
    "mac": "AA:BB:CC:DD:EE:FF",
    "broadcast": "192.168.1.255"
  }
}
```

Telefone: **⋮ meniu → Importuoti JSON**

## Paketas

`com.instalika.apsapower`

## Reikalavimai PC

- BIOS: Wake on LAN įjungta
- Tinklo plokštė: Wake on Magic Packet
- Laidinis Ethernet (ne Wi-Fi)
