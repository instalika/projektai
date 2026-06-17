#!/usr/bin/env python3
"""Kas apkrauna HA – procesai, entitetų atnaujinimai, integracijos."""

from __future__ import annotations

import asyncio
import json
import os
import ssl
import sys
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta

HA_URL = os.environ.get("HA_URL", "https://44w46xbp7oj71nyfrck4gkg9uuk7nfqk.ui.nabu.casa")
HA_TOKEN = os.environ["HA_TOKEN"]
CTX = ssl.create_default_context()


def api_get(path: str):
    req = urllib.request.Request(f"{HA_URL}{path}", headers={"Authorization": f"Bearer {HA_TOKEN}"})
    with urllib.request.urlopen(req, timeout=120, context=CTX) as r:
        return json.loads(r.read().decode())


async def fe_session():
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


async def supervisor_get(endpoint: str):
    import websockets

    async with websockets.connect(
        HA_URL.replace("https://", "wss://") + "/api/websocket", ssl=CTX, open_timeout=45
    ) as ws:
        await ws.recv()
        await ws.send(json.dumps({"type": "auth", "access_token": HA_TOKEN}))
        await ws.recv()
        await ws.send(json.dumps({"id": 1, "type": "supervisor/api", "endpoint": endpoint, "method": "get"}))
        while True:
            r = json.loads(await ws.recv())
            if r.get("id") == 1:
                return r.get("result", {})


def main() -> int:
    print("=" * 64)
    print("KAS APKRAUNA HA SERVERĮ (192.168.0.97)")
    print("=" * 64)

    # 1. Metrikos
    print("\n## 1. HOST METRIKOS")
    try:
        m = api_get("/api/states/sensor.ha_host_metrikos")
        a = m["attributes"]
        print(
            f"CPU: {a.get('cpu_usage')}% | RAM: {a.get('ram_pct')}% "
            f"({a.get('ram_used_mb')}/{a.get('ram_total_mb')} MB)\n"
            f"Load: {a.get('load_1')} / {a.get('load_5')} / {a.get('load_15')} | "
            f"Temp: {a.get('cpu_temp')}C | Uptime: {a.get('uptime_h')}h"
        )
    except Exception as e:
        print(f"  Klaida: {e}")
        return 1

    states = api_get("/api/states")
    now = datetime.now(timezone.utc)

    # 2. Dažniausi atnaujinimai
    print("\n## 2. DAŽNIAUSIAI ATNAUJINAMI ENTITETAI (pask. 5 min)")
    recent = []
    for s in states:
        try:
            lc = datetime.fromisoformat(s["last_changed"].replace("Z", "+00:00"))
            if now - lc < timedelta(minutes=5):
                recent.append((s["entity_id"], (now - lc).total_seconds(), s["state"]))
        except Exception:
            pass
    recent.sort(key=lambda x: x[1])
    print(f"  Atnaujinta per 5 min: {len(recent)} entitetų")
    by_domain = Counter(eid.split(".")[0] for eid, _, _ in recent)
    print("  Pagal domeną:")
    for dom, cnt in by_domain.most_common(12):
        print(f"    {dom}: {cnt}")

    # Top individual entities
    ent_counts = Counter(eid for eid, _, _ in recent)
    print("\n  Top 25 entitetai (dažniausi last_changed):")
    for eid, cnt in ent_counts.most_common(25):
        st = next((x["state"] for x in states if x["entity_id"] == eid), "?")
        print(f"    {cnt:3d}x | {eid} = {st}")

    # 3. Kameros / image / stream
    print("\n## 3. KAMEROS IR VAIZDAI")
    cams = [s for s in states if s["entity_id"].startswith("camera.")]
    imgs = [s for s in states if s["entity_id"].startswith("image.")]
    active_cams = [s for s in cams if s["state"] not in ("unavailable", "unknown")]
    streaming = [s for s in cams if s["state"] == "streaming"]
    print(f"  Kameros: {len(cams)} (aktyvios: {len(active_cams)}, streaming: {len(streaming)})")
    for s in streaming[:10]:
        print(f"    STREAMING: {s['entity_id']}")
    recent_cams = [eid for eid, _, _ in recent if eid.startswith("camera.") or eid.startswith("image.")]
    print(f"  Kamera/image atnaujinimų 5min: {len(recent_cams)}")

    # 4. Modbus / SNMP / command_line
    print("\n## 4. SENSORIAI (modbus, snmp, command_line)")
    keywords = ("modbus", "huawei", "solax", "miner", "mikrotik", "snmp", "braiins", "shelly", "sonoff", "esphome")
    recent_sensors = [
        (eid, sec, st)
        for eid, sec, st in recent
        if eid.startswith("sensor.") and any(k in eid.lower() for k in keywords)
    ]
    recent_sensors.sort(key=lambda x: x[1])
    print(f"  Energetikos/IoT sensorių atnaujinimų 5min: {len(recent_sensors)}")
    for eid, sec, st in recent_sensors[:20]:
        print(f"    {eid} = {st} ({sec:.0f}s ago)")

    # 5. Integracijos
    print("\n## 5. INTEGRACIJOS (aktyvios)")
    async def get_entries():
        import websockets

        async with websockets.connect(
            HA_URL.replace("https://", "wss://") + "/api/websocket", ssl=CTX, open_timeout=45
        ) as ws:
            await ws.recv()
            await ws.send(json.dumps({"type": "auth", "access_token": HA_TOKEN}))
            await ws.recv()
            await ws.send(json.dumps({"id": 1, "type": "config/config_entries/list"}))
            while True:
                r = json.loads(await ws.recv())
                if r.get("id") == 1:
                    return r.get("result", [])

    entries = asyncio.run(get_entries())
    active = [e for e in entries if not e.get("disabled_by")]
    by_dom = Counter(e.get("domain") for e in active)
    print(f"  Aktyvių integracijų: {len(active)}")
    heavy = {"camera", "frigate", "mqtt", "modbus", "sonoff", "shelly", "esphome", "ble", "bluetooth", "stream", "recorder", "image", "rest", "command_line", "template", "nordpool", "mikrotik"}
    for dom, cnt in sorted(by_dom.items()):
        if dom in heavy or cnt > 2:
            print(f"    {dom}: {cnt}")

    # 6. Supervisor / addons
    print("\n## 6. SUPERVISOR / ADDONAI")
    try:
        info = asyncio.run(supervisor_get("/info"))
        data = info.get("data", info) if isinstance(info, dict) else {}
        for k in ("version", "channel", "arch"):
            if k in data:
                print(f"  {k}: {data[k]}")
        host = asyncio.run(supervisor_get("/host/info"))
        hd = host.get("data", host) if isinstance(host, dict) else {}
        for k in ("operating_system", "kernel", "chassis", "disk_total", "disk_used"):
            if k in hd:
                print(f"  host {k}: {hd[k]}")
        addons = asyncio.run(supervisor_get("/addons"))
        ad = addons.get("data", {}).get("addons", addons.get("addons", []))
        if isinstance(ad, list):
            started = [a for a in ad if a.get("state") == "started"]
            print(f"  Paleisti addonai ({len(started)}):")
            for a in started:
                print(f"    - {a.get('name')} ({a.get('slug')})")
    except Exception as e:
        print(f"  supervisor: {type(e).__name__}")

    # 7. scan_interval check in config
    print("\n## 7. MODBUS INTERVALAI (configuration.yaml)")
    try:
        ingress, session = asyncio.run(fe_session())
        cfg = fe_download(ingress, session, "configuration.yaml")
        n5 = cfg.count("scan_interval: 5")
        n10 = cfg.count("scan_interval: 10")
        n30 = cfg.count("scan_interval: 30")
        n300 = cfg.count("scan_interval: 300")
        print(f"  scan_interval 5s: {n5} | 10s: {n10} | 30s: {n30} | 300s: {n300}")
        if n5 or n10:
            print("  ⚠ Vis dar yra greitų intervalų!")
    except Exception as e:
        print(f"  {e}")

    # 8. Template / automation triggers
    print("\n## 8. AUTOMATIZACIJOS IR ŠABLONAI")
    auto_on = sum(1 for s in states if s["entity_id"].startswith("automation.") and s["state"] == "on")
    recent_auto = [eid for eid, _, _ in recent if eid.startswith("automation.")]
    print(f"  Automatizacijų ON: {auto_on} | trigger 5min: {len(recent_auto)}")

    # 9. History CPU/RAM 2h if available
    print("\n## 9. CPU/RAM ISTORIJA (2h)")
    try:
        start = (now - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%S+00:00")
        for eid in ["sensor.ha_host_cpu_naudojimas", "sensor.ha_host_ram_naudojimas"]:
            hist = api_get(f"/api/history/period/{start}?filter_entity_id={eid}&minimal_response")
            pts = hist[0] if hist else []
            vals = [float(p["state"]) for p in pts if str(p.get("state", "")).replace(".", "", 1).isdigit()]
            if vals:
                print(f"  {eid}: min={min(vals):.0f}% max={max(vals):.0f}% avg={sum(vals)/len(vals):.0f}%")
    except Exception as e:
        print(f"  {e}")

    print("\n" + "=" * 64)
    return 0


if __name__ == "__main__":
    sys.exit(main())
