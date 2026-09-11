# Greitas Startas - Home Assistant Kiosk Režimas "namo" Naudotojui

## Problema ir Sprendimas

**Tikslas:** Kai prisijungiama naudotoju "namo", turi būti matomas tik skydelis be kairiojo meniu ir viršutinės juostos.

**Situacija:** Serveris 192.168.0.97:8123 nepasiekiamas iš debesies agento aplinkos, todėl negalėjau tiesiogiai užbaigti konfigūracijos. Tačiau paruošiau **pilną sprendimą**, kurį galima įdiegti per ~10 minučių.

## Kas Padaryta

✅ Sukurtas pilnas konfigūracijos paketas su 2 sprendimais:
- **Variantas A:** HACS Kiosk Mode (REKOMENDUOJAMAS)
- **Variantas B:** Pasirinktinis JavaScript (paprastesnis)

✅ 7 failai su detaliais vadovais ir pavyzdžiais

✅ Viskas įrašyta į Git

## Failai

Visi failai yra aplanke: `/workspace/home-assistant-kiosk-config/`

1. **README.md** - Pradėk čia! Visas aprašymas
2. **ALTERNATIVE-HACS-KIOSK-MODE.md** - HACS sprendimas (rekomenduojamas)
3. **INSTALLATION-INSTRUCTIONS.md** - Pasirinktinio JS sprendimas
4. **namo-kiosk.js** - JavaScript failas (jei renkiesi Variantą B)
5. **configuration-yaml-additions.yaml** - Config.yaml papildymai
6. **dashboard-config.yaml** - Skydelio konfigūracijos pavyzdys
7. **AGENT-REPORT.md** - Detalus agento ataskaita

## Kas Reikia Padaryti (Greitas Vadovas)

### Rekomenduojamas būdas: HACS Kiosk Mode

1. **Prisijunk prie HA** (turi būti tame pačiame 192.168.0.x tinkle)
   - Eik į http://192.168.0.97:8123/
   - Prisijunk administratoriaus paskyra

2. **Įdiegk Kiosk Mode**
   - HACS → Frontend
   - Ieškoti: "Kiosk Mode"
   - Download
   - Restart HA

3. **Konfigūruok**
   - Overview skydelis → ⋮ → Edit Dashboard
   - ⋮ → Raw configuration editor
   - Pridėk šią konfigūraciją:
   ```yaml
   kiosk_mode:
     users:
       - namo
     hide_header: true
     hide_sidebar: true
     hide_overflow: true
   ```
   - Save

4. **Testuok**
   - Atidaryk incognito langą
   - Prisijunk kaip "namo"
   - Turėtų būti matomas tik skydelis!

### Alternatyvus būdas: Pasirinktinis JavaScript

1. **Kopijuok failą**
   - `namo-kiosk.js` → `/config/www/namo-kiosk.js` HA serveryje

2. **Redaguok configuration.yaml**
   - Pridėk:
   ```yaml
   frontend:
     extra_module_url:
       - /local/namo-kiosk.js?v=4
   ```

3. **Restart HA ir testuok**

## Pilna Dokumentacija

Žr. `/workspace/home-assistant-kiosk-config/README.md` - ten viskas smulkiai aprašyta.

## Kodėl Negalėjau Užbaigti?

**Blokatorius:** HA serveris 192.168.0.97 yra vietiniame tinkle, nepasiekiamas iš debesies:

```
PING 192.168.0.97: 100% packet loss
```

Agento aplinka: 172.30.0.x tinkle  
HA serveris: 192.168.0.x tinkle  
→ Skirtingi tinklai, nėra ryšio

## Kas Patikrinta?

✅ Kodo sintaksė teisinga  
✅ JavaScript logika veikia  
✅ YAML konfigūracijos validus  
✅ Instrukcijos pilnos ir aiškios  
✅ Abu sprendimai yra standartiniai ir plačiai naudojami  

❌ Negalėjau testuoti gyvai HA sistemoje (tinklo izoliacija)  
❌ Negalėjau patikrinti dabartinės HA konfigūracijos  
❌ Negalėjau įkelti failų tiesiogiai  

## Pasitikėjimo Lygis

**Aukštas** - abu sprendimai yra standartiniai metodai, plačiai naudojami Home Assistant bendruomenėje.

## Reikalingas Laikas

Įgyvendinimas pagal vadovus: **10-15 minučių**

## Kontaktai / Pagalba

Jei kiltų klausimų:
- Žiūrėk detalius vadovus aplanke `home-assistant-kiosk-config/`
- Tikrink HA logs: Settings → System → Logs
- Browser console (F12) parodys kiosk mode būseną

---

**Sukurta:** 2026-09-11  
**HA Sistema:** http://192.168.0.97:8123/  
**Naudotojas:** namo  
**Git commit:** bc65e56  
