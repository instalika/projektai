# Kompiuterio temperatūros ir būsena

## Ar galima nuskaityti BIOS tiesiogiai?

**Ne visiškai taip, kaip BIOS ekrane.**

| Šaltinis | Ką rodo | Kada veikia |
|----------|---------|-------------|
| **SMBIOS / Win32_BIOS** | BIOS versija, gamintojas, plokštės modelis | Visada (Windows) |
| **ACPI thermal zones** | CPU/matinimo temperatūros | Dažnai **tuščia** ant stacionarių PC |
| **LibreHardwareMonitor** | CPU, GPU, diskų, plokštės temperatūros | Kai programa **paleista** fone |
| **BIOS Setup (F2/Del)** | Visi sensoriai tiesiogiai | Tik kai PC įjungtas ir esate BIOS meniu |

**Iš debesies (Cursor, GitHub) jūsų `192.168.0.97` pasiekti negalima** – skriptą reikia paleisti **ant pačio kompiuterio** arba per nuotolinį PowerShell / Home Assistant.

---

## Greitas startas (Windows)

```powershell
cd C:\kelias\iki\projektai
powershell -ExecutionPolicy Bypass -File scripts\hardware-status.ps1
```

JSON (Home Assistant, monitoring):

```powershell
powershell -ExecutionPolicy Bypass -File scripts\hardware-status.ps1 -Json -OutputFile C:\temp\pc-status.json
```

---

## Geresnės temperatūros (rekomenduojama)

1. Atsisiųskite [LibreHardwareMonitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases)
2. Paleiskite (gali veikti fone)
3. Vėl paleiskite `hardware-status.ps1` – matysite `LHM:...` temperatūras

LibreHardwareMonitor gali būti paleistas su Windows (Task Scheduler).

---

## Home Assistant pavyzdys

`configuration.yaml`:

```yaml
command_line:
  - sensor:
      name: "PC būsena JSON"
      command: 'powershell -ExecutionPolicy Bypass -File C:\instalika\scripts\hardware-status.ps1 -Json'
      scan_interval: 60
      value_template: "{{ value_json.cpu.loadPercent }}"
      json_attributes:
        - cpu
        - memory
        - temperatures
        - warnings
        - bios
```

---

## Ką tikrinti dėl netikėto išsijungimo

- **CPU > 90°C** – perkaitimas, ventiliatorius ar termopasta
- **Event 41** be 1074 – maitinimas ar hardveris (žr. [išjungimo diagnostiką](issijungimo-diagnostika.md))
- **Ventiliatorius 0 RPM** – gedimas

---

**Instalika** | instalika.eu
