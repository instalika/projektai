#!/usr/bin/env python3
"""HA optimizacija – žingsnis po žingsnio su retry kiekvienam veiksmui."""

from __future__ import annotations

import asyncio
import json
import os
import ssl
import sys
import time
import urllib.parse
import urllib.request
import re
from pathlib import Path

HA_URL = os.environ.get("HA_URL", "https://44w46xbp7oj71nyfrck4gkg9uuk7nfqk.ui.nabu.casa")
HA_TOKEN = os.environ["HA_TOKEN"]
CTX = ssl.create_default_context()
REPO = Path(__file__).resolve().parents[1]


def patch_modbus_and_snmp(cfg: str) -> tuple[str, bool]:
    orig = cfg
    cfg = cfg.replace("scan_interval: 5", "scan_interval: 30")
    cfg = cfg.replace("scan_interval: 10", "scan_interval: 30")
    cfg = re.sub(
        r'(  - platform: snmp\n    name: "MikroTik[^"]+"\n)',
        r"\1    scan_interval: 300\n",
        cfg,
    )
    return cfg, cfg != orig

DISABLE_INTEGRATIONS = {"dhcp", "ssdp", "dlna_dmr", "dlna_dms", "cast", "analytics", "speedtestdotnet", "upnp", "ibeacon"}

RECORDER_APPEND = """
# --- našumo optimizacija ---
recorder:
  purge_keep_days: 5
  commit_interval: 45
  auto_purge: true
  exclude:
    domains:
      - image
      - automation
      - script
      - scene
      - updater
      - event
      - button
      - device_tracker
    entity_globs:
      - sensor.*_rssi
      - sensor.*_linkquality
      - sensor.*_last_seen
      - sensor.*_uptime
      - binary_sensor.*update*
      - camera.*

logger:
  default: warning
  logs:
    homeassistant.components.mqtt: error
    homeassistant.components.recorder: warning
    homeassistant.components.camera: error

history:
  exclude:
    domains:
      - image
      - automation
      - script
      - scene
      - updater
      - event
      - device_tracker

stream:
  ll_hls: false
"""


def retry(label: str, fn, attempts: int = 12, delay: float = 5):
    for i in range(attempts):
        try:
            return fn()
        except Exception as e:
            print(f"  {label} [{i + 1}/{attempts}]: {type(e).__name__}")
            time.sleep(delay)
    raise RuntimeError(f"{label} nepavyko")


def api_get(path: str):
    req = urllib.request.Request(f"{HA_URL}{path}", headers={"Authorization": f"Bearer {HA_TOKEN}"})
    with urllib.request.urlopen(req, timeout=60, context=CTX) as r:
        return json.loads(r.read().decode())


def api_post(domain: str, service: str, data: dict | None = None):
    body = json.dumps(data or {}).encode()
    req = urllib.request.Request(
        f"{HA_URL}/api/services/{domain}/{service}",
        data=body,
        method="POST",
        headers={"Authorization": f"Bearer {HA_TOKEN}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=90, context=CTX) as r:
        return r.status


async def file_editor():
    import websockets

    async with websockets.connect(HA_URL.replace("https://", "wss://") + "/api/websocket", ssl=CTX, open_timeout=45) as ws:
        await ws.recv()
        await ws.send(json.dumps({"type": "auth", "access_token": HA_TOKEN}))
        await ws.recv()
        out = {}
        for i, (ep, method) in enumerate([("/addons/core_configurator/info", "get"), ("/ingress/session", "post")], 1):
            await ws.send(json.dumps({"id": i, "type": "supervisor/api", "endpoint": ep, "method": method}))
            while True:
                r = json.loads(await ws.recv())
                if r.get("id") == i:
                    out["ingress" if i == 1 else "session"] = r["result"]["ingress_entry" if i == 1 else "session"]
                    break
    return out["ingress"], out["session"]


def fe_download(ingress: str, session: str, path: str) -> str:
    req = urllib.request.Request(f"{HA_URL}{ingress}/api/file?filename=/homeassistant/{path}")
    req.add_header("Cookie", f"ingress_session={session}")
    with urllib.request.urlopen(req, timeout=120, context=CTX) as r:
        return r.read().decode()


def fe_upload(ingress: str, session: str, path: str, content: str) -> None:
    data = urllib.parse.urlencode({"filename": f"/homeassistant/{path}", "text": content}).encode()
    req = urllib.request.Request(f"{HA_URL}{ingress}/api/save", data=data, method="POST")
    req.add_header("Cookie", f"ingress_session={session}")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=120, context=CTX) as r:
        resp = json.loads(r.read().decode())
        if resp.get("error"):
            raise RuntimeError(resp)


async def ws_disable():
    import websockets

    stats = {"integrations": 0, "image": 0, "update": 0}
    async with websockets.connect(HA_URL.replace("https://", "wss://") + "/api/websocket", ssl=CTX, open_timeout=45) as ws:
        await ws.recv()
        await ws.send(json.dumps({"type": "auth", "access_token": HA_TOKEN}))
        await ws.recv()
        n = 1

        async def call(msg_type: str, **kwargs):
            nonlocal n
            i = n
            n += 1
            await ws.send(json.dumps({"id": i, "type": msg_type, **kwargs}))
            while True:
                r = json.loads(await ws.recv())
                if r.get("id") == i:
                    return r

        entries = (await call("config/config_entries/list")).get("result", [])
        for e in entries:
            if e.get("disabled_by"):
                continue
            if e.get("domain") in DISABLE_INTEGRATIONS:
                if (await call("config_entries/disable", entry_id=e["entry_id"], disabled_by="user")).get("success"):
                    stats["integrations"] += 1
                    print(f"    integracija: {e.get('domain')}")

        entities = (await call("config/entity_registry/list")).get("result", [])
        for ent in entities:
            eid = ent.get("entity_id", "")
            if ent.get("disabled_by"):
                continue
            if eid.startswith("image."):
                if (await call("config/entity_registry/update", entity_id=eid, disabled_by="user")).get("success"):
                    stats["image"] += 1
            elif eid.startswith("update."):
                if (await call("config/entity_registry/update", entity_id=eid, disabled_by="user")).get("success"):
                    stats["update"] += 1
        if stats["image"]:
            print(f"    image entitetų: {stats['image']}")
        if stats["update"]:
            print(f"    update entitetų: {stats['update']}")
    return stats


def main() -> int:
    print("=== HA optimizacija (dabar) ===")

    retry("HA API", lambda: api_get("/api/"))
    print("HA API: OK")

    ingress, session = retry("File editor", lambda: asyncio.run(file_editor()))
    print("File editor: OK")

    cfg = retry("download configuration.yaml", lambda: fe_download(ingress, session, "configuration.yaml"))
    cfg, modbus_changed = patch_modbus_and_snmp(cfg)
    if "purge_keep_days:" not in cfg:
        cfg = cfg.rstrip() + "\n" + RECORDER_APPEND + "\n"
    if modbus_changed:
        print("configuration.yaml: modbus/snmp intervalai padidinti")
    retry("upload configuration.yaml", lambda: fe_upload(ingress, session, "configuration.yaml", cfg))
    print("configuration.yaml: atnaujintas")

    retry(
        "upload packages",
        lambda: (
            fe_upload(ingress, session, "packages/ha_host_monitor.yaml", (REPO / "homeassistant/packages/ha_host_monitor.yaml").read_text()),
            fe_upload(ingress, session, "packages/ha_performance.yaml", (REPO / "homeassistant/packages/ha_performance.yaml").read_text()),
        ),
    )
    print("packages: įkelti")

    print("Išjungiami nereikalingi entitetai...")
    try:
        stats = retry("disable entities", lambda: asyncio.run(ws_disable()), attempts=3, delay=3)
    except Exception:
        stats = {"integrations": 0, "image": 0, "update": 0}
        print("  entitetų išjungimas praleistas (serveris per apkrautas)")

    print("Perkraunama...")
    retry("reload_core_config", lambda: api_post("homeassistant", "reload_core_config"))
    time.sleep(4)
    try:
        api_post("modbus", "reload")
    except Exception:
        pass
    try:
        api_post("recorder", "purge", {"keep_days": 5, "repack": True})
        print("recorder.purge: OK")
    except Exception as e:
        print(f"recorder.purge: {e}")

    try:
        api_post("homeassistant", "restart")
        print("restart: OK")
    except Exception:
        print("restart: inicijuotas")

    print("Laukiama 120s...")
    time.sleep(120)

    def metrics():
        s = api_get("/api/states/sensor.ha_host_metrikos")
        a = s["attributes"]
        total = len(api_get("/api/states"))
        print(f"CPU: {a.get('cpu_usage')}% | RAM: {a.get('ram_pct')}% | load: {a.get('load_1')} | entitetai: {total}")
        return a

    retry("metrics", metrics, attempts=15, delay=10)
    print(f"Santrauka: integracijos={stats['integrations']}, image={stats['image']}, update={stats['update']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
