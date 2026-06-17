# Pilna HA diagnostika – galutinė ataskaita

**Data:** 2026-06-17 | **Šaltinis:** Nabu Casa API (pilna prieiga)  
**HA:** 2026.6.3 | Vieta: Namai | 2476 entitetės

---

## Kas patikrinta per jūsų prieigą

- ✅ Visos 2476 HA entitetės
- ✅ Visos 56 automacijos (pavadinimai, būsenos, last_triggered)
- ✅ Visi shell_command, rest_command, hassio servisai
- ✅ 56 LAN įrenginiai (device_tracker per Mikrotik)
- ✅ Mikrotik routeris (CPU, RAM, uptime)
- ✅ HA perkrovimų istorija
- ✅ Sonoff, miner, Frigate būsenos

---

## HA serveris 192.168.0.97

| Faktas | Rezultatas |
|--------|------------|
| IP `192.168.0.97` HA duomenyse | **NERASTAS** (nei viename įrenginyje) |
| device_tracker sąraše | **Nėra** (56 kiti įrenginiai matomi) |
| Automacijos shutdown/reboot | **Nerasta** (visos 56 peržiūrėtos) |
| shell_command shutdown | **Nėra** (tik backup, frigate, miner) |
| hassio.host_shutdown naudojimas | **Nerasta** automacijose |

> HA serveris `.97` pats savęs netrackingina – normalu. Bet routeris per Mikrotik irgi jo nerodo tarp aktyvių klientų.

---

## 🔴 KRITINIS RADINYS: Mikrotik routeris

| Sensorius | Reikšmė |
|-----------|---------|
| **RAM naudojimas** | **100%** |
| CPU | 8% |
| Uptime | ~53 min (ką tik perkrautas) |

**Išvada:** Routeris **perkrautas** ir **RAM pilnas** – gali sukelti tinklo sutrikimus, ping praradimą, „neveikia“ jausmą net kai serveris įjungtas.

---

## HA perkrovimai (faktai)

| Laikas (Vilnius) | Įvykis |
|------------------|--------|
| Vakar ~22:26 | HA perkrovimas |
| Šiandien ~10:28–10:31 | Trumpi sutrikimai |
| **Šiandien ~11:12** | **Pilnas HA perkrovimas** |

Po 11:12 paleistos automacijos: Backup valyti, Frigate valyti, Kolektoriaus termostatai.

**Jokia automacija neišjungia serverio** – tai HA vidinis restartas arba host reboot be automacijos.

---

## Kas NE kaltas

- ❌ Instalika Power / WoL (tik Samsung TV)
- ❌ Sonoff „SERVERIS" kištukas (maitina ESP `.25`, ne HA host)
- ❌ Automacijos su shutdown
- ❌ Diskas (1530 GB laisva)

---

## Tikėtinos tikrosios priežastys

1. **🥇 Mikrotik RAM 100%** – tinklo nestabilumas
2. **🥈 HA host crash / OOM / OS update** – maitinimas lieka
3. **🥉 Perkaitimas / PSU** – jei reikia fizinio įjungimo
4. Miner automacijos su „hard OFF Shelly" – tik miner'iui, ne HA

---

## Rekomendacijos

1. **Skubiai:** Mikrotik → patikrinkite RAM (100%), perkraukite, išvalykite senas taisykles/connections
2. Pridėti **Ping** sensorių `192.168.0.97` į HA
3. Įjungti **System Monitor** ant HA host (CPU, RAM, temp)
4. **WoL** – reikia MAC iš routerio ARP (ne ESP `.25`)
5. **Ištrinti** paviešintą API token

---

**Instalika** | instalika.eu
