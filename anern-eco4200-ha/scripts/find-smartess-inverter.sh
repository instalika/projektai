#!/usr/bin/env bash
# Anern ECO-4200 / SmartESS Wi-Fi Plug Pro — tinklo paieska (Linux / HA SSH)
set -euo pipefail

detect_subnet() {
  local ip=""
  ip="$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{for (i=1;i<=NF;i++) if ($i=="src") print $(i+1)}' | head -n1)"
  if [[ -z "${ip}" ]]; then
    echo "Nepavyko nustatyti vietinio IPv4 tinklo." >&2
    exit 1
  fi
  echo "${ip%.*}"
}

check_port() {
  local host="$1"
  local port="$2"
  timeout 1 bash -c "echo >/dev/tcp/${host}/${port}" 2>/dev/null
}

SUBNET="${1:-$(detect_subnet)}"

echo ""
echo "=== Anern ECO-4200 / SmartESS tinklo paieska ==="
echo "Tinklas: ${SUBNET}.0/24"
echo ""

FOUND=0
CANDIDATE=""

for i in $(seq 1 254); do
  IP="${SUBNET}.${i}"
  if ping -c 1 -W 1 "${IP}" >/dev/null 2>&1; then
    OPEN8899="NE"
    OPEN502="NE"
    if check_port "${IP}" 8899; then OPEN8899="TAIP"; fi
    if check_port "${IP}" 502; then OPEN502="TAIP"; fi

    if [[ "${OPEN8899}" == "TAIP" ]]; then
      echo ">>> SMARTESS LOGGERIS: ${IP}  (TCP 8899=TAIP, TCP 502=${OPEN502})"
      FOUND=1
      [[ -z "${CANDIDATE}" ]] && CANDIDATE="${IP}"
    else
      echo "Aktyvus: ${IP}  (8899=NE, 502=${OPEN502})"
    fi
  fi
done

echo ""
if [[ "${FOUND}" -eq 1 ]]; then
  echo "Rekomenduojamas IP Home Assistant: ${CANDIDATE}"
  echo "${CANDIDATE}" > "$(dirname "$0")/found-smartess-ip.txt"
  echo "IP issaugotas: $(dirname "$0")/found-smartess-ip.txt"
else
  echo "SmartESS loggerio su atviru 8899 portu nerasta."
  exit 1
fi
