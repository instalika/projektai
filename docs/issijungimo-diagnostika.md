# Netikėtas kompiuterio išsijungimas – diagnostika

Jei kompiuteris (pvz. `192.168.0.97`) išsijungia pats ir reikia jį vėl **įjungti rankiniu būdu** ar per **Instalika Power (WoL)**, pirmiausia reikia nustatyti **kas jį išjungia**.

## Svarbu: Instalika Power neišjungia

Šis projektas siunčia tik **Wake-on-LAN** magic packet – **įjungia** kompiuterį. Jokios išjungimo komandos čia nėra.

---

## 1. Paleiskite diagnostiką ant pačio PC

Ant kompiuterio `192.168.0.97` (Windows), **Administratoriaus** PowerShell:

```powershell
cd C:\kelias\iki\projektai
powershell -ExecutionPolicy Bypass -File scripts\diagnose-shutdown.ps1 -Days 14 -OutputFile shutdown-report.txt
```

Atidarykite `shutdown-report.txt` ir ieškokite **Event ID 1074** – ten bus parašyta **kas** inicijavo išjungimą (procesas, vartotojas).

| Event ID | Reikšmė |
|----------|---------|
| **1074** | Planuotas išjungimas/restartas – **rodo kaltininką** (procesą) |
| **6008** | Sistema buvo išjungta netikėtai |
| **41** | Maitinimas nutrūko be tvarkingo shutdown (perkaitimas, elektros dingimas, hardveris) |
| **109** | Branduolys inicijavo maitinimo pokytį |

---

## 2. Home Assistant (HA)

Jei naudojate HA, patikrinkite:

1. **Nustatymai → Automacijos** – ieškokite `shutdown`, `restart`, `192.168.0.97`, `shell_command`
2. **Nustatymai → Scenarijai** – ar nėra `shutdown` / `turn_off`
3. **configuration.yaml** – `shell_command:` su `shutdown`, `poweroff`, `systemctl`
4. **Smart kištukas** – ar PC maitinimas nepertraukiamas per relę (Shelly, TP-Link ir pan.)
5. **HA logai** – Developer Tools → Logs tuo metu, kai PC išsijungė

> WoL integracija HA **tik įjungia** PC – neišjungia.

---

## 3. Greitas Windows patikrinimas

```powershell
# Paskutiniai išjungimai (kas inicijavo)
Get-WinEvent -FilterHashtable @{LogName='System'; Id=1074} -MaxEvents 10 |
  Format-List TimeCreated, Message

# Suplanuotos shutdown užduotys
Get-ScheduledTask | Where-Object { $_.Actions.Arguments -match 'shutdown|/s ' } |
  Select-Object TaskName, TaskPath, State
```

---

## 4. Dažnos priežastys

| Priežastis | Požymiai |
|------------|----------|
| **Windows Update** | 1074 rodo `TiWorker.exe` arba `MusNotificationUx.exe` |
| **HA automacija** | Išsijungia tuo pačiu laiku kasdien; HA loguose matosi veiksmas |
| **Smart kištukas** | PC visiškai negauna maitinimo (ne sleep) |
| **Perkaitimas / PSU** | 41, 6008 be 1074; dažnai po apkrovos |
| **Miego/hibernacija** | Atrodo kaip išsijungimas; WoL gali neveikti iš sleep |

---

## 5. Po diagnostikos

- Jei kaltas **HA** – išjunkite ar pataisykite automaciją.
- Jei **Windows Update** – nustatykite aktyvųs valandas ar atidėkite restartą.
- Jei **41/6008 be 1074** – tikrinkite maitinimą, ventiliatorius, BIOS temperatūras.
- Jei reikia **nuotolinio įjungimo** – naudokite Instalika Power (WoL), bet BIOS ir tinklo plokštėje turi būti įjungtas Wake-on-LAN.

---

**Instalika** | instalika.eu
