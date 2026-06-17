# APSA Power Instalika – Android

Kotlin + Jetpack Compose programėlė kompiuterių įjungimui per LAN.

## Reikalavimai

- [Android Studio](https://developer.android.com/studio) (Ladybug ar naujesnė)
- Android SDK 35
- JDK 17

## Paleidimas

1. Atidarykite **Android Studio**
2. **File → Open** → pasirinkite `android/` aplanką
3. Palaukite Gradle sinchronizacijos
4. Prijunkite telefoną (USB derinimas) arba naudokite emuliatorių
5. Paspauskite **Run** (▶)

## Funkcijos

- Kompiuterių sąrašas su vieno paspaudimo **Įjungti** mygtuku
- Pridėti / redaguoti / šalinti kompiuterius
- Greitas įjungimas pagal MAC adresą
- Duomenys saugomi telefone (DataStore)
- Veikia per Wi-Fi (telefonas turi būti tame pačiame tinkle kaip tikslinis PC)

## Svarbu

- Telefonas ir kompiuteris turi būti **tame pačiame LAN** tinkle
- Tiksliniame PC turi būti įjungtas **Wake on LAN** BIOS ir tinklo plokštėje
- Naudokite **subnet broadcast** (pvz. `192.168.1.255`), ne visada veikia `255.255.255.255`

## APK surinkimas

```bash
cd android
./gradlew assembleRelease
# APK: app/build/outputs/apk/release/app-release-unsigned.apk
```

Pasirašykite APK prieš diegimą į gamybos įrenginius.

## Paketo pavadinimas

`com.instalika.apsapower`
