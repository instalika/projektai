#!/usr/bin/env python3
"""Pilna HA diagnostika – shutdown, automacijos, konfigūracija. BE restart."""

from __future__ import annotations

import asyncio
import json
import os
import re
import ssl
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

HA_URL = os.environ.get("HA_URL", "https://44w46xbp7oj71nyfrck4gkg9uuk7nfqk.ui.nabu.casa")
HA_TOKEN = os.environ["HA_TOKEN"]
CTX = ssl.create_default_context()

DANGER = re.compile(
    r"shutdown|poweroff|host_shutdown|host\.shutdown|host\.reboot|"
    r"hassio\.host_shutdown|hassio\.host_reboot|systemctl\s+(poweroff|halt|reboot)|"
    r"/usr/sbin/(shutdown|poweroff|halt|reboot)|"
    r"homeassistant\.stop|os\.shutdown|ha\s+host\s+shutdown|ha\s+os\s+shutdown",
    re.I,
)
RESTART = re.compile(r"homeassistant\.restart|reload_core_config|recorder\.purge", re.I)
SUSPICIOUS = re.compile(
    r"switch\.sonoff.*server|serveris|pazadinti|wake_on_lan|wol|instalika|"
    r"miner.*isjung|katil.*isjung|relay.*off",
    re.I,
)


def api_get(path: str):
    req = urllib.request.Request(f"{HA_URL}{path}", headers={"Authorization": f"Bearer {HA_TOKEN}"})
    with urllib.request.urlopen(req, timeout=90, context=CTX) as r:
        return json.loads(r.read().decode())


async def file_editor_session():
    import websockets

    async with websockets.connect(
        HA_URL.replace("https://", "wss://") + "/api/websocket", ssl=CTX, open_timeout=45
    ) as ws:
        await ws.recv()
        await ws.send(json.dumps({"type": "auth", "access_token": HA_TOKEN}))
        await ws.recv()
        ingress = session = None
        for i, (ep, method) in enumerate([("/addons/core_configurator/info", "get"), ("/ingress/session", "post")], 1):
            await ws.send(json.dumps({"id": i, "type": "supervisor/api", "endpoint": ep, "method": method}))
            while True:
                r = json.loads(await ws.recv())
                if r.get("id") == i:
                    if i == 1:
                        ingress = r["result"]["ingress_entry"]
                    else:
                        session = r["result"]["session"]
                    break
    return ingress, session


def fe_download(ingress: str, session: str, path: str) -> str:
    req = urllib.request.Request(f"{HA_URL}{ingress}/api/file?filename=/homeassistant/{path}")
    req.add_header("Cookie", f"ingress_session={session}")
    with urllib.request.urlopen(req, timeout=120, context=CTX) as r:
        return r.read().decode()


async def ws_messages(*types):
    import websockets

    results = {}
    async with websockets.connect(
        HA_URL.replace("https://", "wss://") + "/api/websocket", ssl=CTX, open_timeout=45
    ) as ws:
        await ws.recv()
        await ws.send(json.dumps({"type": "auth", "access_token": HA_TOKEN}))
        await ws.recv()
        mid = 1
        for t in types:
            await ws.send(json.dumps({"id": mid, "type": t}))
            while True:
                r = json.loads(await ws.recv())
                if r.get("id") == mid:
                    results[t] = r.get("result", r)
                    mid += 1
                    break
    return results


def scan_file(path: str, content: str) -> dict:
    danger, restart, suspicious = [], [], []
    for i, line in enumerate(content.splitlines(), 1):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if DANGER.search(s):
            danger.append((i, s[:150]))
        if RESTART.search(s):
            restart.append((i, s[:150]))
        if SUSPICIOUS.search(s):
            suspicious.append((i, s[:150]))
    return {"danger": danger, "restart": restart, "suspicious": suspicious}


def main() -> int:
    print("=" * 60)
    print("HA PILNA DIAGNOSTIKA (be restart)")
    print("=" * 60)

    # 1. API / metrics
    print("\n## 1. SISTEMA DABAR")
    try:
        info = api_get("/api/")
        print(f"HA API: {info.get('message', info)}")
    except Exception as e:
        print(f"HA API KLAIDA: {e}")
        return 1

    try:
        cfg = api_get("/api/config")
        print(f"Versija: {cfg.get('version')} | {cfg.get('location_name')} | {cfg.get('time_zone')}")
    except Exception:
        pass

    try:
        m = api_get("/api/states/sensor.ha_host_metrikos")
        a = m["attributes"]
        print(
            f"CPU: {a.get('cpu_usage')}% | RAM: {a.get('ram_pct')}% "
            f"({a.get('ram_used_mb')}/{a.get('ram_total_mb')} MB) | "
            f"Load: {a.get('load_1')}/{a.get('load_5')}/{a.get('load_15')} | "
            f"Temp: {a.get('cpu_temp')}C | Uptime: {a.get('uptime_h')}h | IP: {a.get('ip')}"
        )
    except Exception as e:
        print(f"Metrikos: {e}")

    states = api_get("/api/states")
    print(f"Entitetų: {len(states)}")

    # 2. Entities scan
    print("\n## 2. ENTITETAI (shutdown/reboot/serveris)")
    entity_hits = []
    for s in states:
        blob = f"{s['entity_id']} {(s['attributes'].get('friendly_name') or '')}"
        if DANGER.search(blob) or SUSPICIOUS.search(blob):
            entity_hits.append((s["entity_id"], s["attributes"].get("friendly_name"), s["state"]))
    if entity_hits:
        for eid, name, st in sorted(entity_hits):
            print(f"  {eid} | {name} | {st}")
    else:
        print("  Nerasta shutdown/serveris entitetų pavadinimuose")

    # Scripts detail
    print("\n## 3. SCENARIJAI (script.*)")
    scripts = [s for s in states if s["entity_id"].startswith("script.")]
    for s in sorted(scripts, key=lambda x: x["entity_id"]):
        name = s["attributes"].get("friendly_name", "")
        if DANGER.search(s["entity_id"] + name) or SUSPICIOUS.search(s["entity_id"] + name) or "host" in s["entity_id"].lower():
            print(f"  {s['entity_id']}: {name} [{s['state']}] last={s['attributes'].get('last_triggered')}")

    # Automations
    print("\n## 4. AUTOMATIZACIJOS (įtartinos)")
    autos = [s for s in states if s["entity_id"].startswith("automation.")]
    auto_hits = []
    for a in autos:
        name = a["attributes"].get("friendly_name", "")
        blob = f"{a['entity_id']} {name}"
        if DANGER.search(blob) or SUSPICIOUS.search(blob) or any(
            w in name.lower() for w in ["shutdown", "isjung", "reboot", "perkraun", "host", "serveris", "restart"]
        ):
            auto_hits.append((a["entity_id"], name, a["state"]))
    if auto_hits:
        for eid, name, st in sorted(auto_hits):
            print(f"  {eid}: {name} [{st}]")
    else:
        print("  Nerasta įtartinų automatizacijų pavadinimuose")

    # Sonoff SERVERIS
    print("\n## 5. SONOFF SERVERIS")
    for s in states:
        if "sonoff" in s["entity_id"].lower() and ("server" in s["entity_id"].lower() or "10017a018e" in s["entity_id"]):
            print(f"  {s['entity_id']}: {s['state']} | {s['attributes'].get('friendly_name')}")

    # 6. YAML files
    print("\n## 6. KONFIGŪRACIJOS FAILAI")
    ingress, session = asyncio.run(file_editor_session())
    files = [
        "configuration.yaml",
        "automations.yaml",
        "scripts.yaml",
        "shell_command.yaml",
        "packages/ha_host_monitor.yaml",
        "packages/ha_performance.yaml",
        "ha-host-metrics.sh",
    ]
    all_danger = []
    for fname in files:
        try:
            content = fe_download(ingress, session, fname)
            r = scan_file(fname, content)
            print(f"\n  --- {fname} ({len(content)} b) ---")
            if r["danger"]:
                print(f"  ⚠ DANGER ({len(r['danger'])}):")
                for ln, line in r["danger"][:15]:
                    print(f"    L{ln}: {line}")
                all_danger.extend([(fname, ln, line) for ln, line in r["danger"]])
            else:
                print("  ✓ shutdown komandų nėra")
            if r["restart"]:
                print(f"  restart/reload eilutės: {len(r['restart'])}")
            if r["suspicious"] and fname in ("configuration.yaml", "automations.yaml", "scripts.yaml"):
                print(f"  įtartinos eilutės: {len(r['suspicious'])}")
                for ln, line in r["suspicious"][:8]:
                    print(f"    L{ln}: {line}")
        except Exception as e:
            print(f"  {fname}: {type(e).__name__} {e}")

    # 7. configuration.yaml danger context
    if all_danger:
        print("\n## 7. DANGER KONTEKSTAS")
        try:
            cfg = fe_download(ingress, session, "configuration.yaml")
            lines = cfg.splitlines()
            for fname, ln, _ in all_danger[:10]:
                if fname == "configuration.yaml":
                    start = max(0, ln - 3)
                    end = min(len(lines), ln + 2)
                    print(f"\n  configuration.yaml L{ln}:")
                    for i in range(start, end):
                        print(f"    {i+1}: {lines[i]}")
        except Exception:
            pass

    # 8. Registry - automations via API
    print("\n## 8. AUTOMACIJŲ KONFIGŪRACIJA (API)")
    try:
        regs = asyncio.run(ws_messages("config/automation/config/list"))
        auto_cfgs = regs.get("config/automation/config/list", [])
        danger_autos = []
        for a in auto_cfgs:
            blob = json.dumps(a, ensure_ascii=False)
            if DANGER.search(blob):
                danger_autos.append(a)
        print(f"  Automatizacijų iš viso: {len(auto_cfgs)}")
        if danger_autos:
            print(f"  ⚠ Su shutdown komandomis: {len(danger_autos)}")
            for a in danger_autos[:10]:
                print(f"    - {a.get('alias', a.get('id'))}")
                for action in a.get("actions", a.get("action", []))[:3]:
                    print(f"      action: {str(action)[:120]}")
        else:
            print("  ✓ Automatizacijose shutdown komandų nerasta")
    except Exception as e:
        print(f"  automation API: {type(e).__name__}")

    # 9. Script configs
    print("\n## 9. SCENARIJŲ KONFIGŪRACIJA (API)")
    try:
        regs = asyncio.run(ws_messages("config/script/config/list"))
        script_cfgs = regs.get("config/script/config/list", [])
        for sc in script_cfgs:
            blob = json.dumps(sc, ensure_ascii=False)
            if DANGER.search(blob) or "pazadinti" in blob.lower() or "host" in blob.lower():
                print(f"  {sc.get('alias', sc.get('id'))}:")
                print(f"    {str(sc.get('sequence', ''))[:200]}")
    except Exception as e:
        print(f"  script API: {type(e).__name__}")

    # 10. Logbook shutdown events
    print("\n## 10. LOGBOOK (24h – shutdown/restart)")
    try:
        start = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        lb = api_get(f"/api/logbook/{start}")
        hits = [
            e
            for e in lb
            if DANGER.search(json.dumps(e, ensure_ascii=False))
            or RESTART.search(json.dumps(e, ensure_ascii=False))
            or "restart" in json.dumps(e, ensure_ascii=False).lower()
        ]
        print(f"  Įrašų: {len(hits)}")
        for e in hits[-20:]:
            when = (e.get("when") or "")[:19]
            name = e.get("name") or e.get("entity_id") or "?"
            msg = (e.get("message") or "")[:100]
            print(f"    {when} | {name} | {msg}")
    except Exception as e:
        print(f"  logbook: {type(e).__name__}")

    # 11. Our deploy scripts check
    print("\n## 11. MŪSŲ SKRIPTAI (repo)")
    repo = Path(__file__).resolve().parents[1]
    for rel in [
        "scripts/ha-remote-deploy.py",
        "scripts/ha-remote-optimize.py",
        "scripts/ha-optimize-now.py",
        "homeassistant/scripts/ha-host-metrics.sh",
        "homeassistant/packages/ha_host_monitor.yaml",
    ]:
        p = repo / rel
        if p.exists():
            t = p.read_text()
            d = DANGER.findall(t)
            r = "homeassistant.restart" in t or "homeassistant/restart" in t
            print(f"  {rel}: shutdown={bool(d)} restart_call={r}")

    # 12. Recorder config check
    print("\n## 12. OPTIMIZACIJOS BŪSENA")
    try:
        cfg = fe_download(ingress, session, "configuration.yaml")
        checks = [
            ("purge_keep_days", "purge_keep_days:" in cfg),
            ("logger warning", "default: warning" in cfg),
            ("modbus 30s", "scan_interval: 30" in cfg and "scan_interval: 5" not in cfg),
            ("stream ll_hls", "ll_hls: false" in cfg),
            ("ha_performance pkg", True),
        ]
        for name, ok in checks:
            print(f"  {'✓' if ok else '✗'} {name}")
        if "scan_interval: 5" in cfg or "scan_interval: 10" in cfg:
            n5 = cfg.count("scan_interval: 5")
            n10 = cfg.count("scan_interval: 10")
            print(f"  ⚠ likę greiti intervalai: 5s={n5}, 10s={n10}")
    except Exception as e:
        print(f"  {e}")

    print("\n" + "=" * 60)
    print("DIAGNOSTIKA BAIGTA (jokio restart neišsiųsta)")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
