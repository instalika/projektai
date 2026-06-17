#!/bin/bash
# Įdiegti HA Host monitorių ant Home Assistant OS
# Paleisti Terminal & SSH add-on: bash install-ha-host-monitor.sh

set -euo pipefail
REPO="${REPO:-https://raw.githubusercontent.com/instalika/projektai/cursor/ha-pc-monitor-3ac6/homeassistant}"
CONFIG="${CONFIG:-/config}"

mkdir -p "$CONFIG/scripts" "$CONFIG/packages" "$CONFIG/dashboards" "$CONFIG/lovelace"

echo "→ Atsisiunčiama..."
curl -fsSL "$REPO/scripts/ha-host-metrics.sh" -o "$CONFIG/scripts/ha-host-metrics.sh"
curl -fsSL "$REPO/packages/ha_host_monitor.yaml" -o "$CONFIG/packages/ha_host_monitor.yaml"
curl -fsSL "$REPO/dashboards/ha_host_dashboard.yaml" -o "$CONFIG/dashboards/ha_host_dashboard.yaml"
curl -fsSL "$REPO/lovelace/apzvalga_ha_pc_mygtukas.yaml" -o "$CONFIG/lovelace/apzvalga_ha_pc_mygtukas.yaml"
chmod +x "$CONFIG/scripts/ha-host-metrics.sh"

if ! grep -q "include_dir_named packages" "$CONFIG/configuration.yaml" 2>/dev/null; then
  echo "" >> "$CONFIG/configuration.yaml"
  echo "homeassistant:" >> "$CONFIG/configuration.yaml"
  echo "  packages: !include_dir_named packages" >> "$CONFIG/configuration.yaml"
  echo "!! Pridėta packages eilutė į configuration.yaml"
fi

if ! grep -q "ha-host-dashboard" "$CONFIG/configuration.yaml" 2>/dev/null; then
  cat >> "$CONFIG/configuration.yaml" <<'EOF'

lovelace:
  mode: storage
  dashboards:
    ha-host-dashboard:
      mode: yaml
      title: HA Serveris
      icon: mdi:server
      show_in_sidebar: true
      filename: dashboards/ha_host_dashboard.yaml
EOF
  echo "!! Pridėtas Lovelace skydelis ha-host-dashboard"
fi

echo ""
echo "✓ Įdiegta į $CONFIG"
echo ""
echo "Kitas žingsnis:"
echo "  1. Nustatymai → Sistema → Perkrauti"
echo "  2. Importuokite dashboards/ha_host_dashboard.yaml"
echo "  3. Pridėkite mygtuką iš lovelace/apzvalga_ha_pc_mygtukas.yaml į Apžvalgą"
echo ""
bash "$CONFIG/scripts/ha-host-metrics.sh" json | head -5
