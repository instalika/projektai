# Kaip paleisti diagnostiką ant HA serverio

Cursor agentas **negali prisijungti** prie `192.168.0.97` iš debesies – nėra SSH rakto, HA token ir namų tinklo prieigos.

## Vienas veiksmas (nukopijuokite į HA SSH)

Prisijunkite prie HA serverio:
- **HA OS:** Settings → Add-ons → **Terminal & SSH** → atidarykite terminalą
- Arba: `ssh root@192.168.0.97` (slaptažodis iš HA)

Tada įklijuokite **vieną eilutę**:

```bash
curl -fsSL "https://raw.githubusercontent.com/instalika/projektai/cursor/shutdown-diagnostics-3ac6/scripts/ha-run-now.sh" | bash
```

Skriptas automatiškai:
1. Nuskaito temperatūras, RAM, diską
2. Ieško OOM / reboot logų
3. Tikrina HA automacijas (`shutdown`, `reboot`)
4. Išveda išvadas lietuviškai
5. (Jei įmanoma) sugeneruoja nuorodą ataskaitai pasidalinti

---

## Alternatyva – jei turite repo

```bash
cd /config  # arba kur klonavote
bash scripts/ha-run-now.sh
```

---

## Ką atsiųsti atgal

Po paleidimo nukopijuokite:
- terminalo išvestį nuo `SANTRAUKA`
- arba nuorodą `transfer.sh/...` jei rodo

Tada galima tiksliai pasakyti kas išjungia serverį.
