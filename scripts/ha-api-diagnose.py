#!/usr/bin/env python3
"""Home Assistant API diagnostika – naudoja HA_TOKEN ir HA_URL."""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from ssl import create_default_context

HA_URL = os.environ.get("HA_URL", "http://192.168.0.97:8123").rstrip("/")
HA_TOKEN = os.environ.get("HA_TOKEN", "")
SUSPICIOUS = re.compile(
    r"shutdown|reboot|poweroff|host_shutdown|systemctl|halt|turn_off.*192\.168|wake_on_lan",
    re.I,
)


def request(path: str, method: str = "GET", data: dict | None = None) -> tuple[int, str]:
    ctx = create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = 0  # CERT_NONE for self-signed

    headers = {"Authorization": f"Bearer {HA_TOKEN}", "Content-Type": "application/json"}
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(f"{HA_URL}{path}", data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20, context=ctx) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except Exception as e:
        return 0, str(e)


def main() -> int:
    if not HA_TOKEN:
        print("KLAIDA: nustatykite HA_TOKEN aplinkos kintamąjį")
        return 1

    print("=" * 60)
    print("Instalika Power – HA API diagnostika")
    print(f"URL: {HA_URL}")
    print(f"Laikas: {datetime.now().isoformat()}")
    print("=" * 60)

    # 1. API
    code, body = request("/api/")
    print(f"\n[1] API: HTTP {code}")
    if code != 200:
        print(f"    KLAIDA: {body[:300]}")
        print("\n!! Nepavyko prisijungti. Galimos priežastys:")
        print("   - Serveris išjungtas")
        print("   - Reikia Nabu Casa URL: HA_URL=https://xxx.ui.nabu.casa")
        print("   - Paleiskite skriptą iš namų tinklo (ne debesyje)")
        return 2
    print(f"    {body.strip()}")

    # 2. Config
    code, body = request("/api/config")
    if code == 200:
        cfg = json.loads(body)
        print(f"\n[2] HA versija: {cfg.get('version', '?')}")
        print(f"    Vieta: {cfg.get('location_name', '?')}")
        print(f"    Laiko juosta: {cfg.get('time_zone', '?')}")
        print(f"    Valstybė: {cfg.get('country', '?')}")

    # 3. System health
    code, body = request("/api/system_health")
    if code == 200:
        print("\n[3] System health:")
        for item in json.loads(body):
            print(f"    {item.get('type')}: {item.get('status')} – {item.get('error', 'OK')}")

    # 4. Hass.io host (HA OS)
    for ep, label in [
        ("/api/hassio/host/info", "Host info"),
        ("/api/hassio/supervisor/info", "Supervisor"),
        ("/api/hassio/core/info", "Core"),
    ]:
        code, body = request(ep)
        if code == 200:
            print(f"\n[4] {label}:")
            info = json.loads(body).get("data", json.loads(body))
            for k in ("operating_system", "kernel", "chassis", "cpu_percent", "memory_percent",
                      "disk_used", "disk_total", "version", "ip_address", "broadcast"):
                if k in info:
                    print(f"    {k}: {info[k]}")

    # 5. States – įtartinos entitetės
    code, body = request("/api/states")
    if code == 200:
        states = json.loads(body)
        print(f"\n[5] Entitetės: {len(states)} viso")
        suspicious = []
        for s in states:
            eid = s.get("entity_id", "")
            attrs = json.dumps(s.get("attributes", {}), ensure_ascii=False)
            if SUSPICIOUS.search(eid) or SUSPICIOUS.search(attrs):
                suspicious.append(s)
        if suspicious:
            print("    !! ĮTARTINOS entitetės (shutdown/reboot/power):")
            for s in suspicious[:30]:
                print(f"      {s['entity_id']} = {s['state']}")
        else:
            print("    Įtartinų entitetų pagal pavadinimą nerasta")

        # Temperatūros
        temps = [s for s in states if s.get("attributes", {}).get("device_class") == "temperature"
                 or "temperature" in s["entity_id"]]
        if temps:
            print("\n    Temperatūros:")
            for t in temps[:15]:
                print(f"      {t['entity_id']}: {t['state']} {t.get('attributes', {}).get('unit_of_measurement', '')}")

    # 6. Logbook – paskutinės 24h
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=24)
    lb_url = (
        f"/api/logbook/{start.isoformat()}?end_time={end.isoformat()}"
        "&entity=automation.&entity=script."
    )
    code, body = request(lb_url)
    if code == 200:
        entries = json.loads(body)
        shutdown_entries = [
            e for e in entries
            if SUSPICIOUS.search(json.dumps(e, ensure_ascii=False))
        ]
        print(f"\n[6] Logbook (24h): {len(entries)} įrašų")
        if shutdown_entries:
            print("    !! Įtartiniai logbook įrašai:")
            for e in shutdown_entries[:20]:
                print(f"      {e.get('when')} {e.get('name', e.get('entity_id'))} – {e.get('message', '')}")
        else:
            print("    Shutdown/reboot veiksmų logbook'e nerasta")

    # 7. Error log
    code, body = request("/api/error_log")
    if code == 200:
        lines = body.strip().splitlines()
        print(f"\n[7] Error log: {len(lines)} eilučių")
        critical = [l for l in lines if re.search(r"error|critical|shutdown|reboot|oom", l, re.I)]
        for line in critical[-15:]:
            print(f"    {line[:120]}")

    # Išvados
    print("\n" + "=" * 60)
    print("IŠVADOS")
    print("=" * 60)
    print("""
Jei matote įtartinas automacijas/script – jos gali išjungti serverį.
Jei host memory_percent > 90% – OOM rizika.
Jei temperatūros > 80°C – perkaitimo rizika.
Instalika Power WoL tik ĮJUNGIA – neišjungia.
""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
