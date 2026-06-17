# HA serverio diagnostikos ataskaita

**Data:** 2026-06-17  
**Šaltinis:** Home Assistant API (Nabu Casa)  
**HA versija:** 2026.6.3 | Vieta: Namai | Laiko juosta: Europe/Vilnius

---

## Pagrindinė išvada

**HA serverį neišjungia jokia automacija ir nei Sonoff kištukas.**

- `switch.sonoff_10017a018e` (**SERVERIS**) – visada **ON**
- Maitinimo istorijoje **nėra** suvartojimo <5W (serveris nuolat gavo elektros)
- Automacijų su `shutdown` / `reboot` / `host_shutdown` – **nerasta**

**Problema:** serveris **perkraunasi / užstringa**, bet **maitinimas nutrūksta ne per Sonoff**.

---

## Serverio duomenys

| Parametras | Reikšmė |
|------------|---------|
| **Tikras IP** (pagal HA) | `192.168.0.25` (ne 192.168.0.97) |
| **MAC** | `C0:49:EF:CF:A1:7C` |
| **Hostname** | espressif |
| **Maitinimas (Sonoff)** | 34.34 W, 0.23 A, 231 V |
| **Diskas laisva** | 1530.9 GB |
| **Entitetės** | 2476 (424 unavailable) |

---

## Užfiksuoti perkrovimai (paskutinės 48h)

| Laikas (UTC) | Laikas (Vilnius) | Įvykis |
|--------------|------------------|--------|
| 2026-06-16 19:26 | ~22:26 | HA perkrovimas |
| 2026-06-17 07:28 | ~10:28 | Trumpas HA sutrikimas |
| 2026-06-17 07:31 | ~10:31 | Trumpas HA sutrikimas |
| **2026-06-17 08:12** | **~11:12** | **Pilnas HA perkrovimas** (visos „paleidus HA" automacijos) |

---

## Kas NE kaltas

- ❌ Instalika Power / WoL (tik TV Samsung, ne serveris)
- ❌ Sonoff SERVERIS kištukas (niekada neišjungė)
- ❌ Automacijos su shutdown
- ❌ Disko vieta (1530 GB laisva)

---

## Tikėtinos priežastys

1. **Programinis HA/OS perkrovimas** (atnaujinimai, crash, OOM)
2. **Hardverio užstrigimas** (maitinimas ON, bet HA neatsako – reikia fizinio reset)
3. **19 miner automacijų unavailable** – integracijos problemos po perkrovimo
4. **424 unavailable entitetės** – nestabilus Zigbee/Sonoff tinklas apkrauna sistemą

---

## Rekomendacijos

1. **WoL serveriui** – pridėti MAC `C0:49:EF:CF:A1:7C` (IP `192.168.0.25`)
2. **Nejungti HA per Sonoff SERVERIS** – naudoti tik stebėsenai
3. **Įjungti HA OS host metrics** – CPU, RAM, temperatūra
4. **Patikrinti Supervisor logus** po 11:12 perkrovimo šiandien
5. **Atnaujinti token** – buvo paviešintas pokalbyje

---

**Instalika** | instalika.eu
