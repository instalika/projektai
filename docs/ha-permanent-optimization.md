# HA ilgalaikė našumo optimizacija

Vienas diegimas sumažina CPU/RAM ir **automatiškai palaiko** optimizaciją po paleidimų bei addon atnaujinimų.

## Greitas diegimas (rekomenduojama)

**Terminal & SSH** add-on (tiesiogiai HA serveryje):

```bash
curl -fsSL "https://raw.githubusercontent.com/instalika/projektai/cursor/ha-permanent-fix-3ac6/homeassistant/install-ha-permanent-fix.sh" | bash
```

Skriptas:
1. Įkelia `ha_performance_guard.yaml` (automatinė apsauga)
2. Įrašo `INSTALIKA_PERFORMANCE` bloką į `configuration.yaml`
3. Optimizuoja Frigate (`person` lieka – kiemo šviesos automatizacija veikia)
4. Sustabdo Whisper/Piper/openWakeWord ir nustato `boot: manual`
5. Perkrauna **tik Frigate** addon (ne visą HA)
6. `ha core reload` (be pilno restart)

## Nuotolinis diegimas (su API raktu)

```bash
export HA_URL="https://JUSU.nabu.casa"
export HA_TOKEN="..."
python3 scripts/ha-permanent-fix.py
```

## Kas lieka automatiškai

| Mechanizmas | Kada veikia |
|-------------|-------------|
| Balso addonai sustabdomi | Po HA paleidimo + kas 4 val. |
| Frigate perkrovimas | Po paleidimo, sekmadieniais 04:15, CPU >90% 10 min |
| Recorder valymas | Kasdien 03:30 (5 dienos) |
| CPU įspėjimas | CPU >85% 15 min |

## Po Frigate addon atnaujinimo

Addon atnaujinimas kartais **perrašo** `config.yml`. Paleiskite diegimo skriptą dar kartą:

```bash
curl -fsSL "https://raw.githubusercontent.com/instalika/projektai/cursor/ha-permanent-fix-3ac6/homeassistant/install-ha-permanent-fix.sh" | bash
```

## Rankinės paslaugos HA

- `script.performance_guard_frigate_optimize` – Frigate optimizacija + perkrovimas
- `script.performance_guard_voice_addons_stop` – sustabdyti balso addonus
- `script.performance_guard_safe_reload` – saugus YAML perkrovimas

## Ko nedaryti

- **Nenaudokite** `homeassistant.restart` kai CPU >90% – gali užšaldyti sistemą
- **Nenaudokite** `hassio.host_shutdown` – išjungia kompiuterį
- Uždarykite Lovelace live kameras – kiekvienas srautas krauna CPU

## Tikėtini rezultatai

| Metrika | Prieš | Po |
|---------|-------|-----|
| CPU | ~90–100% | ~30–50% |
| RAM | ~60% | ~20–35% |

Judesio įrašymas Frigate: **motion 3d**, continuous 0d – **nepakeista**.
