#!/bin/bash
# Ilgalaikė HA našumo optimizacija – paleisti Terminal & SSH add-on
# Vienas paleidimas sutvarko Frigate, recorder, balso addonus ir įjungia apsaugą.

set -euo pipefail

REPO="${REPO:-https://raw.githubusercontent.com/instalika/projektai/cursor/ha-permanent-fix-3ac6/homeassistant}"
CONFIG="${CONFIG:-/config}"
FRIGATE_SLUG="${FRIGATE_SLUG:-ccab4aaf_frigate}"
VOICE_ADDONS=(core_whisper core_piper core_openwakeword)

log() { echo "→ $*"; }
ok() { echo "✓ $*"; }
warn() { echo "!! $*"; }

mkdir -p "$CONFIG/scripts" "$CONFIG/packages"

log "Atsisiunčiama iš repo..."
curl -fsSL "$REPO/scripts/ha-host-metrics.sh" -o "$CONFIG/scripts/ha-host-metrics.sh"
curl -fsSL "$REPO/scripts/frigate-optimize-local.py" -o "$CONFIG/scripts/frigate-optimize-local.py"
curl -fsSL "$REPO/packages/ha_host_monitor.yaml" -o "$CONFIG/packages/ha_host_monitor.yaml"
curl -fsSL "$REPO/packages/ha_performance.yaml" -o "$CONFIG/packages/ha_performance.yaml"
curl -fsSL "$REPO/packages/ha_performance_guard.yaml" -o "$CONFIG/packages/ha_performance_guard.yaml"
chmod +x "$CONFIG/scripts/ha-host-metrics.sh" "$CONFIG/scripts/frigate-optimize-local.py"

if [[ ! -f "$CONFIG/ha-host-metrics.sh" ]] && [[ -f "$CONFIG/scripts/ha-host-metrics.sh" ]]; then
  cp "$CONFIG/scripts/ha-host-metrics.sh" "$CONFIG/ha-host-metrics.sh"
  chmod +x "$CONFIG/ha-host-metrics.sh"
fi

if ! grep -q "include_dir_named packages" "$CONFIG/configuration.yaml" 2>/dev/null; then
  echo "" >> "$CONFIG/configuration.yaml"
  echo "homeassistant:" >> "$CONFIG/configuration.yaml"
  echo "  packages: !include_dir_named packages" >> "$CONFIG/configuration.yaml"
  warn "Pridėta packages eilutė į configuration.yaml"
fi

PERF_FILE="$(mktemp)"
cat > "$PERF_FILE" <<'EOF'
# === INSTALIKA_PERFORMANCE_BEGIN ===
recorder:
  purge_keep_days: 5
  commit_interval: 45
  auto_purge: true
  exclude:
    domains:
      - image
      - automation
      - script
      - scene
      - updater
      - event
      - button
      - device_tracker
    entity_globs:
      - sensor.*_rssi
      - sensor.*_linkquality
      - sensor.*_last_seen
      - sensor.*_uptime
      - binary_sensor.*update*
      - camera.*

logger:
  default: warning
  logs:
    homeassistant.components.mqtt: error
    homeassistant.components.recorder: warning
    homeassistant.components.camera: error

history:
  exclude:
    domains:
      - image
      - automation
      - script
      - scene
      - updater
      - event
      - device_tracker

stream:
  ll_hls: false
# === INSTALIKA_PERFORMANCE_END ===
EOF

if grep -q "INSTALIKA_PERFORMANCE_BEGIN" "$CONFIG/configuration.yaml" 2>/dev/null; then
  python3 - "$CONFIG/configuration.yaml" "$PERF_FILE" <<'PY'
import re, sys
cfg_path, perf_path = sys.argv[1], sys.argv[2]
text = open(cfg_path, encoding="utf-8").read()
block = open(perf_path, encoding="utf-8").read().strip()
text = re.sub(
    r"# === INSTALIKA_PERFORMANCE_BEGIN ===.*?# === INSTALIKA_PERFORMANCE_END ===",
    block,
    text,
    flags=re.DOTALL,
)
open(cfg_path, "w", encoding="utf-8").write(text)
PY
  ok "configuration.yaml našumo blokas atnaujintas"
else
  echo "" >> "$CONFIG/configuration.yaml"
  cat "$PERF_FILE" >> "$CONFIG/configuration.yaml"
  ok "configuration.yaml našumo blokas pridėtas"
fi
rm -f "$PERF_FILE"

if grep -q "scan_interval: 5" "$CONFIG/configuration.yaml" || grep -q "scan_interval: 10" "$CONFIG/configuration.yaml"; then
  sed -i 's/scan_interval: 5/scan_interval: 30/g; s/scan_interval: 10/scan_interval: 30/g' "$CONFIG/configuration.yaml"
  ok "Modbus scan_interval → 30s"
fi

log "Frigate optimizacija..."
if python3 "$CONFIG/scripts/frigate-optimize-local.py"; then
  ok "Frigate config optimizuotas"
else
  warn "Frigate config nerastas arba klaida – tęsiama"
fi

log "Balso addonai – sustabdyti ir boot: manual..."
for slug in "${VOICE_ADDONS[@]}"; do
  ha addons stop "$slug" 2>/dev/null && ok "Sustabdytas $slug" || true
  ha addons options "$slug" --boot manual 2>/dev/null && ok "$slug boot=manual" || true
done

log "Frigate perkrovimas (tik addon, ne visas HA)..."
ha addons restart "$FRIGATE_SLUG" 2>/dev/null && ok "Frigate perkrautas" || warn "Frigate restart nepavyko"

log "Laukiama 60s stabilizacijos..."
sleep 60

log "HA konfigūracijos perkrovimas (be pilno restart)..."
if ha core reload 2>/dev/null; then
  ok "ha core reload"
else
  warn "ha core reload nepavyko – Nustatymai → Developer tools → YAML perkrovimas"
fi

echo ""
echo "=============================================="
echo "  ILGALAIKĖ OPTIMIZACIJA ĮDIEGTA"
echo "=============================================="
echo ""
echo "Automatinė apsauga (ha_performance_guard.yaml):"
echo "  • Balso addonai – sustabdyti po paleidimo ir kas 4 val."
echo "  • Frigate optimizacija – po paleidimo ir sekmadieniais 04:15"
echo "  • Recorder valymas – kasdien 03:30"
echo "  • CPU >85% įspėjimas po 15 min"
echo ""
if [[ -x "$CONFIG/scripts/ha-host-metrics.sh" ]]; then
  echo "Metrikos:"
  bash "$CONFIG/scripts/ha-host-metrics.sh" json 2>/dev/null | head -3 || true
fi
echo ""
