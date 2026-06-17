#!/usr/bin/env bash
# Vienas prisijungimas – pilna HA diagnostika. Paleiskite ant serverio:
#   curl -fsSL "https://raw.githubusercontent.com/instalika/projektai/cursor/shutdown-diagnostics-3ac6/scripts/ha-run-now.sh" | bash
# Arba jei turite repo:
#   bash scripts/ha-run-now.sh

set -euo pipefail

REPO_RAW="${REPO_RAW:-https://raw.githubusercontent.com/instalika/projektai/cursor/shutdown-diagnostics-3ac6/scripts}"
TMPDIR="${TMPDIR:-/tmp/instalika-ha-$$}"
mkdir -p "$TMPDIR"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Instalika Power – HA serverio automatinė diagnostika    ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Atsisiųsti arba naudoti lokalius skriptus
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd)" || SCRIPT_DIR=""
if [[ -f "${SCRIPT_DIR}/ha-server-diagnose.sh" ]]; then
  DIAG="${SCRIPT_DIR}/ha-server-diagnose.sh"
else
  echo "→ Atsisiunčiami diagnostikos skriptai..."
  curl -fsSL "$REPO_RAW/ha-server-diagnose.sh" -o "$TMPDIR/ha-server-diagnose.sh"
  chmod +x "$TMPDIR/ha-server-diagnose.sh"
  DIAG="$TMPDIR/ha-server-diagnose.sh"
fi

echo "→ Paleidžiama pilna diagnostika..."
echo ""
bash "$DIAG" 7

REPORT=$(ls -t /tmp/ha-server-diagnose-*.txt 2>/dev/null | head -1)
echo ""
echo "════════════════════════════════════════════════════════════"
echo "  ATASKAITA: ${REPORT:-nerasta}"
echo "════════════════════════════════════════════════════════════"

if [[ -n "${REPORT:-}" && -f "$REPORT" ]]; then
  echo ""
  echo "── SANTRAUKA (paskutinės išvados) ──"
  sed -n '/=== IŠVADOS/,$p' "$REPORT" | head -40

  # Pasidalinimui (nebūtina)
  if command -v curl &>/dev/null; then
    UPLOAD=$(curl -fsS --upload-file "$REPORT" "https://transfer.sh/$(basename "$REPORT")" 2>/dev/null || true)
    if [[ -n "$UPLOAD" && "$UPLOAD" == http* ]]; then
      echo ""
      echo "→ Ataskaitos nuoroda (24h): $UPLOAD"
      echo "  Nukopijuokite ir įklijuokite Cursor pokalbyje."
    fi
  fi
fi

echo ""
echo "Baigta. Jei serveris vis dar išsijungia – žr. skyrių OOM ir temperatūras ataskaitoje."
