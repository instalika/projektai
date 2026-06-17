#!/usr/bin/env bash
# Instalika Power – HA serverio diagnostika (paleisti ANT serverio)
# HA OS: ssh root@192.168.0.97, tada: bash ha-server-diagnose.sh
# Arba per Terminal & SSH add-on

set -uo pipefail

DAYS="${1:-7}"
REPORT="/tmp/ha-server-diagnose-$(date +%Y%m%d-%H%M%S).txt"

exec > >(tee "$REPORT") 2>&1

section() { echo ""; echo "=== $1 ==="; }

section "HA serverio diagnostika"
echo "Host: $(hostname)"
echo "Laikas: $(date -Iseconds)"
echo "Uptime: $(uptime -p 2>/dev/null || uptime)"

# --- Sistema ---
section "1. Sistema"
echo "OS: $(uname -a)"
if [[ -f /etc/os-release ]]; then
  grep -E "^(NAME|VERSION|ID)=" /etc/os-release
fi

# --- Resursai ---
section "2. Resursai (RAM, diskas, apkrova)"
free -h 2>/dev/null || true
echo ""
df -h / /data /mnt/data 2>/dev/null | head -10
echo ""
echo "Load: $(cat /proc/loadavg 2>/dev/null)"

# --- Temperatūros ---
section "3. Temperatūros"
FOUND_TEMP=0
for tz in /sys/class/thermal/thermal_zone*/temp; do
  [[ -f "$tz" ]] || continue
  raw=$(cat "$tz" 2>/dev/null)
  [[ "$raw" =~ ^[0-9]+$ ]] || continue
  c=$(awk "BEGIN {printf \"%.1f\", $raw/1000}")
  zone=$(echo "$tz" | grep -o 'thermal_zone[0-9]*')
  type_file="${tz%/temp}/type"
  type=$(cat "$type_file" 2>/dev/null || echo "unknown")
  echo "  $zone ($type): ${c}°C"
  FOUND_TEMP=1
  if awk "BEGIN {exit !($c >= 80)}"; then
    echo "    !! ĮSPĖJIMAS: aukšta temperatūra"
  fi
done
if [[ $FOUND_TEMP -eq 0 ]]; then
  echo "  Temperatūrų sensorių nerasta (/sys/class/thermal)"
  command -v vcgencmd &>/dev/null && vcgencmd measure_temp 2>/dev/null
fi

# --- OOM / kernel klaidos ---
section "4. OOM ir branduolio klaidos (dažna HA išsijungimo priežastis)"
if command -v journalctl &>/dev/null; then
  echo "-- OOM (Out of Memory) per ${DAYS}d:"
  journalctl --since "${DAYS} days ago" -k 2>/dev/null | grep -i "out of memory\|oom-kill\|killed process" | tail -20
  if [[ $? -ne 0 ]]; then echo "  (nerasta)"; fi
  echo ""
  echo "-- Kernel panic / watchdog:"
  journalctl --since "${DAYS} days ago" -k 2>/dev/null | grep -iE "panic|watchdog|hard LOCKUP|thermal" | tail -15
else
  dmesg 2>/dev/null | grep -iE "oom|out of memory|thermal|panic" | tail -20
fi

# --- Shutdown / reboot įvykiai ---
section "5. Shutdown / reboot įvykiai"
if command -v journalctl &>/dev/null; then
  journalctl --since "${DAYS} days ago" 2>/dev/null | \
    grep -iE "shutdown|reboot|power.?off|systemd.*halt|Reached target.*Shutdown" | tail -25
fi
last -x reboot shutdown 2>/dev/null | head -15

# --- Home Assistant ---
section "6. Home Assistant"
if command -v ha &>/dev/null; then
  echo "HA CLI:"
  ha core info 2>/dev/null | head -20
  echo ""
  ha supervisor info 2>/dev/null | head -15
elif [[ -d /config ]]; then
  echo "HA config: /config"
  ls -la /config/configuration.yaml 2>/dev/null
else
  echo "HA CLI nerastas (galbūt Docker / supervised)"
  docker ps 2>/dev/null | grep -i home || true
fi

# --- HA logai ---
section "7. HA klaidos (paskutinės)"
for log in /config/home-assistant.log /var/log/home-assistant/home-assistant.log; do
  [[ -f "$log" ]] && { echo "Log: $log"; tail -30 "$log" | grep -iE "error|shutdown|restart|critical" | tail -15; }
done
if command -v ha &>/dev/null; then
  ha core logs 2>/dev/null | tail -20
fi

# --- Automacijos su shutdown (jei yra API token) ---
section "8. Įtartinos automacijos (jei HA_TOKEN nustatytas)"
if [[ -n "${HA_TOKEN:-}" ]]; then
  HA_URL="${HA_URL:-http://127.0.0.1:8123}"
  curl -sS -H "Authorization: Bearer $HA_TOKEN" -H "Content-Type: application/json" \
    "$HA_URL/api/config" 2>/dev/null | head -5
  echo ""
  echo "Automacijos su shutdown/reboot/host:"
  curl -sS -H "Authorization: Bearer $HA_TOKEN" "$HA_URL/api/states" 2>/dev/null | \
    python3 -c "
import sys, json
try:
    states = json.load(sys.stdin)
    for s in states:
        eid = s.get('entity_id','')
        if any(k in eid for k in ('automation','script','shell_command')):
            attrs = str(s.get('attributes',{})).lower()
            if any(k in attrs or k in eid for k in ('shutdown','reboot','poweroff','host_shutdown','systemctl')):
                print(' ', eid, '-', s.get('state'))
except Exception as ex:
    print('  Klaida:', ex)
" 2>/dev/null || echo "  (reikia python3 ir HA_TOKEN)"
else
  echo "  Nustatykite HA_TOKEN aplinkos kintamąjį pilnai automacijų analizei"
  echo "  HA → Profilis → Long-Lived Access Tokens"
  if [[ -f /config/automations.yaml ]]; then
    echo ""
    echo "  Greita paieška automations.yaml:"
    grep -inE "shutdown|reboot|poweroff|host_shutdown|systemctl.*halt" /config/automations.yaml 2>/dev/null | head -20 || echo "  (nieko nerasta)"
  fi
  if [[ -f /config/scripts.yaml ]]; then
    grep -inE "shutdown|reboot|poweroff|host_shutdown" /config/scripts.yaml 2>/dev/null | head -10
  fi
fi

# --- Išvados ---
section "IŠVADOS – HA serverio išsijungimo tikėtinos priežastys"

MEM_AVAIL=$(free -m 2>/dev/null | awk '/Mem:/ {print $7}')
LOAD=$(cat /proc/loadavg 2>/dev/null | awk '{print $1}')
DISK_USE=$(df / 2>/dev/null | tail -1 | awk '{print $5}' | tr -d '%')

WARNINGS=()
[[ -n "$MEM_AVAIL" && "$MEM_AVAIL" -lt 200 ]] && WARNINGS+=("Mažai laisvos RAM (${MEM_AVAIL}MB) – OOM rizika")
[[ -n "$DISK_USE" && "$DISK_USE" -gt 90 ]] && WARNINGS+=("Diskas užpildytas ${DISK_USE}%")
[[ -n "$LOAD" ]] && awk "BEGIN {exit !($LOAD > 4)}" 2>/dev/null && WARNINGS+=("Didelė apkrova: $LOAD")

if [[ ${#WARNINGS[@]} -gt 0 ]]; then
  for w in "${WARNINGS[@]}"; do echo "  !! $w"; done
else
  echo "  Resursų įspėjimų nėra (pagal dabartinę būseną)"
fi

cat <<'EOF'

Prioritetinė tikrinimo tvarka:

  A) Ar serveris ant smart kištuko, kuris išjungia maitinimą?
  B) OOM žurnalai (4 skyrius) – dažniausia RPi priežastis
  C) Temperatūra > 80°C (3 skyrius) – perkaitimas
  D) HA automacijos su shutdown/reboot (8 skyrius)
  E) Nestabilus PSU / prasta SD kortelė (RPi)
  F) HA OS atnaujinimas su auto-reboot

Instalika Power WoL gali ĮJUNGTI serverį, bet neišjungia.
EOF

echo ""
echo "Pilna ataskaita: $REPORT"
