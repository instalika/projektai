# Kaip paleisti diagnostiką ant HA serverio

## Su jūsų HA token (API)

Cursor **negali pasiekti** `192.168.0.97` iš debesies (net su token). Token bandytas – `Connection reset`.

### Variantas A – Nabu Casa (nuotolinis URL)

Jei turite **Nabu Casa**, nustatykite URL ir paleiskite **iš savo PC**:

```bash
export HA_URL="https://JUSU-ADRESAS.ui.nabu.casa"
export HA_TOKEN="jūsų-long-lived-token"
python3 scripts/ha-api-diagnose.py
```

Nabu Casa URL: HA → Settings → Home Assistant Cloud → Remote access.

### Variantas B – tas pats Wi-Fi (PC/telefonas)

```bash
export HA_URL="http://192.168.0.97:8123"
export HA_TOKEN="jūsų-token"
python3 scripts/ha-api-diagnose.py
```

### Variantas C – SSH ant serverio

```bash
curl -fsSL "https://raw.githubusercontent.com/instalika/projektai/cursor/shutdown-diagnostics-3ac6/scripts/ha-run-now.sh" | bash
```

---

## Saugumas

**Niekada nedėkite token į viešą chat ar GitHub.** Jei jau pateikėte – HA → Profilis → Long-Lived Access Tokens → **ištrinkite** ir sukurkite naują.

---

## Ką atsiųsti atgal

Paleidus `ha-api-diagnose.py`, nukopijuokite visą terminalo išvestį – tada galima tiksliai pasakyti kas vyksta.
