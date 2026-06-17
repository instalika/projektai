# Saugios HA komandos (192.168.0.97)

## Svarbu: skirtumas tarp komandų

| Komanda | Ką daro | Ar išjungia kompiuterį? |
|---------|---------|-------------------------|
| `homeassistant.reload_core_config` | Perkrauna YAML konfigūraciją | **Ne** |
| `template.reload` | Perkrauna šablonus | **Ne** |
| `modbus.reload` | Perkrauna Modbus | **Ne** |
| `homeassistant.restart` | Perkrauna **tik HA programą** | **Ne turėtų** (ne OS shutdown) |
| `hassio.host_reboot` | **Perkrauna visą kompiuterį** | Taip (reboot) |
| `hassio.host_shutdown` | **Išjungia kompiuterį** | **Taip (shutdown)** |

Mūsų agento skriptai naudojo tik `homeassistant.restart` – tai **ne** `host_shutdown`.
Tačiau kai CPU >90% ir RAM >75%, dažni restart + `recorder.purge repack` gali:

- užkrauti diską ir CPU iki sistemos „užšalimo“;
- sukelti OOM (out-of-memory) ir netikėtą išsijungimą;
- atrodyti kaip „kompiuteris išsijungė“, nors Nabu Casa tiesiog nebeatsako.

**Nuo 2026-06-17 agento skriptuose pilnas `homeassistant.restart` išjungtas.**
Naudojamas tik `reload_core_config` + `template.reload` + `modbus.reload`.

## Jei kompiuteris vis tiek išsijungia

1. Patikrinkite HA **Automacijas** – paieška: `shutdown`, `host_shutdown`, `reboot`, `poweroff`
2. Ar serveris prijungtas per **Sonoff/smart kištuką** (ne „SERVERIS“ ESP, o pats PC maitinimas)?
3. **Mikrotik RAM 100%** – tinklo problemos, bet ne turėtų išjungti PC
4. **PSU / perkaitimas / OOM** – žiūrėkite `sensor.ha_host_cpu_temperatura`, RAM, uptime

## Saugus nuotolinis diegimas

```bash
python3 scripts/ha-optimize-now.py   # be restart
python3 scripts/ha-remote-deploy.py  # be restart
```

**Instalika Power / WoL** – tik **įjungia** kompiuterį, neišjungia.
