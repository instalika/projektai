#!/bin/bash
# HA Host metrikos – Home Assistant OS (192.168.0.97)
# Naudojimas: ha-host-metrics.sh json | cpu_temp | fan_rpm | ...

set -euo pipefail

json_escape() { python3 -c "import json,sys; print(json.dumps(sys.stdin.read().strip()))"; }

cpu_temp() {
  local v max=0
  for tz in /sys/class/thermal/thermal_zone*/temp; do
    [[ -f "$tz" ]] || continue
    v=$(cat "$tz" 2>/dev/null || echo 0)
    [[ "$v" =~ ^[0-9]+$ ]] && (( v > max )) && max=$v
  done
  if (( max > 0 )); then
    awk "BEGIN {printf \"%.1f\", $max/1000}"
  else
    echo "null"
  fi
}

cpu_usage() {
  local idle1 total1 idle2 total2
  read -r _ u1 n1 s1 i1 iw1 irq1 sirq1 _ < /proc/stat
  idle1=$((i1 + iw1)); total1=$((u1 + n1 + s1 + idle1 + irq1 + sirq1))
  sleep 1
  read -r _ u2 n2 s2 i2 iw2 irq2 sirq2 _ < /proc/stat
  idle2=$((i2 + iw2)); total2=$((u2 + n2 + s2 + idle2 + irq2 + sirq2))
  local dt=$((total2 - total1)) di=$((idle2 - idle1))
  if (( dt <= 0 )); then echo "0.0"; return; fi
  awk "BEGIN {printf \"%.1f\", (1 - $di / $dt) * 100}"
}

ram_stats() {
  awk '/MemTotal:|MemAvailable:/ {
    if ($1=="MemTotal:") t=$2
    if ($1=="MemAvailable:") a=$2
  } END {
    if (t>0) {
      used=t-a
      printf "%.1f %.0f %.0f", used*100/t, used/1024, t/1024
    } else print "0 0 0"
  }' /proc/meminfo
}

disk_stats() {
  df -k / 2>/dev/null | awk 'NR==2 {
    total=$2/1024/1024
    used=$3/1024/1024
    free=$4/1024/1024
  pct=$5
  gsub(/%/,"",pct)
  printf "%.0f %.1f %.1f %.1f", pct, free, total, used
  }'
}

load_avg() {
  read -r l1 l5 l15 _ < /proc/loadavg
  echo "$l1 $l5 $l15"
}

uptime_hours() {
  awk '{printf "%.1f", $1/3600}' /proc/uptime
}

fan_rpm() {
  local rpm=0 v
  for f in /sys/class/hwmon/hwmon*/fan*_input; do
    [[ -f "$f" ]] || continue
    v=$(cat "$f" 2>/dev/null || echo 0)
    [[ "$v" =~ ^[0-9]+$ ]] && (( v > rpm )) && rpm=$v
  done
  if (( rpm > 0 )); then echo "$rpm"; else echo "null"; fi
}

host_ip() {
  ip -4 route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="src") print $(i+1); exit}' || hostname -I 2>/dev/null | awk '{print $1}' || echo "192.168.0.97"
}

case "${1:-json}" in
  json)
    read -r ram_pct ram_used ram_total <<< "$(ram_stats)"
    read -r disk_pct disk_free disk_total disk_used <<< "$(disk_stats)"
    read -r load_1 load_5 load_15 <<< "$(load_avg)"
    cpu_t=$(cpu_temp)
    cpu_u=$(cpu_usage)
    fan=$(fan_rpm)
  ip=$(host_ip)
    cat <<EOF
{
  "cpu_temp": ${cpu_t:-null},
  "cpu_usage": ${cpu_u:-0},
  "ram_pct": ${ram_pct:-0},
  "ram_used_mb": ${ram_used:-0},
  "ram_total_mb": ${ram_total:-0},
  "disk_pct": ${disk_pct:-0},
  "disk_free_gb": ${disk_free:-0},
  "disk_total_gb": ${disk_total:-0},
  "disk_used_gb": ${disk_used:-0},
  "load_1": ${load_1:-0},
  "load_5": ${load_5:-0},
  "load_15": ${load_15:-0},
  "uptime_h": $(uptime_hours),
  "fan_rpm": ${fan:-null},
  "ip": "$(echo "$ip" | tr -d '"')"
}
EOF
    ;;
  cpu_temp) cpu_temp ;;
  cpu_usage) cpu_usage ;;
  fan_rpm) fan_rpm ;;
  ip) host_ip ;;
  *) echo "Naudojimas: $0 json|cpu_temp|cpu_usage|fan_rpm|ip" >&2; exit 1 ;;
esac
