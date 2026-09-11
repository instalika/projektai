# „Namo“ paskyros kiosk režimas

Tikslas: paskyrai, kurios rodomas vardas yra `Namo` (prisijungimo vardas
`namo`), rodyti tik namo valdymo skydelį – be šoninės ir viršutinės juostų.

> Kiosk režimas tik paslepia naršyklės sąsają. Tai nėra prieigos teisių
> apsauga. Paskyra turi likti ne administratoriaus, o skydelyje neturi būti
> kortelių ar veiksmų, kurių šiam naudotojui nereikia.

## Diegimas

1. Prisijungus administratoriumi atverti **HACS → Frontend**.
2. Įdiegti **Kiosk Mode** (`NemesisRE/kiosk-mode`; senesnėse versijose gali
   būti rodoma `maykar/kiosk-mode`). Rinktis naujausią su naudojama HA versija
   suderinamą leidimą.
3. Atverti būtent **Namo valdymas** skydelį, tada:
   **⋮ → Edit dashboard → ⋮ → Raw configuration editor**.
4. Aukščiausiame YAML lygyje, šalia `views:`, įrašyti:

   ```yaml
   kiosk_mode:
     user_settings:
       - users:
           - "Namo"
         kiosk: true
         hide_overflow: true
         hide_account: true
         hide_search: true
   ```

   `users` čia naudoja rodomą naudotojo vardą (`Namo`), ne prisijungimo
   vardą (`namo`). Kitoms paskyroms režimas nebus taikomas.

5. Išsaugoti ir perkrauti puslapį. Jei HACS to prašo, prieš tai perkrauti
   Home Assistant.
6. Prieš paslepiant meniu pirmą kartą prisijungti kaip `namo`, atverti
   **Namo valdymas** ir naudotojo profilyje pasirinkti jį kaip numatytąjį
   skydelį. Ši nuostata saugoma konkrečioje naršyklėje / įrenginyje.

## Patikrinimas

- Privačiame naršyklės lange prisijungus kaip `namo` turi būti rodomas
  **Namo valdymas**, be šoninės ir viršutinės juostų.
- Administratoriaus paskyroje abi juostos turi likti matomos.
- Jei režimas nepasileidžia, išvalyti HA svetainės podėlį ir patikrinti, ar
  HACS resursas yra **Settings → Dashboards → Resources**.

HA adresas: <http://192.168.0.97:8123/>

Šio adreso negalima pasiekti iš viešos debesies aplinkos, nes tai privatus
vietinio tinklo adresas. Todėl diegimas pačiame HA ir gyvas patikrinimas iš
šios darbo aplinkos neatlikti.
