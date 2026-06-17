#!/bin/bash
# APSA Power Instalika – web valdymo panelės paleidimas
cd "$(dirname "$0")"

if ! command -v python3 &>/dev/null; then
    echo "Klaida: python3 nerastas."
    exit 1
fi

echo ""
echo "  APSA Power Instalika – web valdymo panelė"
echo "  =========================================="
echo ""

exec python3 -m apsa_power --web --host 0.0.0.0 --web-port 8080
