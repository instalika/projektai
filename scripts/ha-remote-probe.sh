#!/usr/bin/env bash
# Instalika Power – nuotolinė HA serverio diagnostika (paleisti iš LAN)
# Naudojimas: ./ha-remote-probe.sh [IP]
# Pvz.: ./ha-remote-probe.sh 192.168.0.97

set -uo pipefail

TARGET="${1:-192.168.0.97}"
HA_PORT="${HA_PORT:-8123}"
TIMEOUT=5

section() { echo ""; echo "=== $1 ==="; }

CLOUD_FALSE_POSITIVE=0
REPORT="/tmp/ha-probe-${TARGET}-$(date +%Y%m%d-%H%M%S).txt"

exec > >(tee "$REPORT") 2>&1

section "Instalika Power – HA serverio nuotolinė diagnostika"
echo "Tikslas: $TARGET"
echo "Laikas: $(date -Iseconds)"
echo "Ataskaita: $REPORT"

section "0. DNS / maršrutizacija"
RESOLVED=$(getent hosts "$TARGET" 2>/dev/null | awk '{print $2}')
echo "DNS: $TARGET → ${RESOLVED:-nežinoma}"
if echo "$RESOLVED" | grep -qiE 'ec2\.internal|amazonaws|compute\.internal'; then
  echo ""
  echo "!! ĮSPĖJIMAS: IP išsprendžiamas į DEBESIES vidinį adresą ($RESOLVED),"
  echo "   NE į jūsų namų tinklo HA serverį. Ši diagnostika iš Cursor debesies"
  echo "   NEGALI pasiekti tikro 192.168.0.97 namuose."
  echo "   Paleiskite šį skriptą iš telefono/PC tame pačiame Wi-Fi."
  CLOUD_FALSE_POSITIVE=1
fi


# --- Tinklo pasiekiamumas ---
section "1. Tinklas"
if ping -c 3 -W 2 "$TARGET" &>/dev/null; then
  echo "OK: Ping atsako"
else
  echo "KLAIDA: Ping neatsako – serveris išjungtas arba nepasiekiamas tinkle"
fi

# --- HA web ---
section "2. Home Assistant web ($HA_PORT)"
HTTP_CODE=$(curl -sS -m "$TIMEOUT" -o /dev/null -w "%{http_code}" "http://${TARGET}:${HA_PORT}/" 2>/dev/null) || HTTP_CODE="000"
if [[ "$HTTP_CODE" == "200" ]]; then
  echo "OK: HA web veikia (HTTP 200)"
elif [[ "$HTTP_CODE" == "000" ]]; then
  echo "KLAIDA: HA web neatsako (timeout arba serveris down)"
else
  echo "ĮSPĖJIMAS: HTTP $HTTP_CODE"
fi

# --- HA API (be token – tik ar atsako) ---
section "3. HA REST API"
API_RESP=$(curl -sS -m "$TIMEOUT" "http://${TARGET}:${HA_PORT}/api/" 2>/dev/null || echo "")
if echo "$API_RESP" | grep -q "API running"; then
  echo "OK: HA API veikia"
  echo "$API_RESP"
else
  echo "API neprieinama arba reikia autentifikacijos"
fi

# --- SSH ---
section "4. SSH (22)"
if timeout 3 bash -c "echo >/dev/tcp/${TARGET}/22" 2>/dev/null; then
  echo "OK: SSH prievadas atviras"
else
  echo "SSH neprieinamas (normalu HA OS – SSH dažnai išjungtas)"
fi

# --- Supervisor (HA OS) ---
section "5. Supervisor (4357)"
SUP_CODE=$(curl -sS -m "$TIMEOUT" -o /dev/null -w "%{http_code}" "http://${TARGET}:4357/" 2>/dev/null || echo "000")
echo "Supervisor HTTP: $SUP_CODE"

# --- MAC (WoL įjungimui) ---
section "6. MAC adresas (WoL)"
MAC=$(arp -n "$TARGET" 2>/dev/null | awk '/ether/ {print $3; exit}')
if [[ -n "$MAC" && "$MAC" != "(incomplete)" ]]; then
  echo "MAC: $MAC  → galite įjungti per Instalika Power WoL"
else
  echo "MAC nerastas ARP lentelėje (serveris gali būti offline)"
fi

# --- Išvados ---
section "IŠVADOS"

if [[ "${CLOUD_FALSE_POSITIVE:-0}" -eq 1 ]]; then
  cat <<EOF

DIAGNOSTIKA IŠ DEBESIES NEGALIOJA šiam IP.
Tikrą HA serverį galima tikrinti tik iš jūsų LAN (telefonas, PC, namų tinkle).

EOF
fi

if [[ "$HTTP_CODE" != "200" ]] && ! ping -c 1 -W 2 "$TARGET" &>/dev/null; then
  cat <<EOF

Serveris $TARGET DABAR NEPASIEKIAMAS.

Galimos priežastys (HA serveriui dažniausios):

  1. Maitinimo nutraukimas / smart kištukas išjungė
  2. Perkaitimas (RPi/NUC) – ypač be ventiliatoriaus
  3. OOM (per mažai RAM) – branduolys užmušė procesus / reboot
  4. SD kortelės gedimas (Raspberry Pi)
  5. Nestabilus maitinimo blokas (RPi labai jautrus)
  6. HA OS automatinis atnaujinimas + reboot

Ką daryti:
  - Įjunkite serverį ranka arba WoL (jei MAC žinomas)
  - Prisijunkite per SSH arba HA OS konsolę ir paleiskite:
      bash ha-server-diagnose.sh
  - Patikrinkite HA automacijas su host_shutdown / reboot
EOF
else
  cat <<EOF

Serveris $TARGET PASIEKIAMAS ir HA veikia.

Jei vis tiek kartais išsijungia – paleiskite ant serverio:
  bash ha-server-diagnose.sh

Ir peržiūrėkite HA automacijas (shutdown, restart, shell_command).
EOF
fi

echo ""
echo "Ataskaita išsaugota: $REPORT"
