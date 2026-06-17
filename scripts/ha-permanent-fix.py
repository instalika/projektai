#!/usr/bin/env python3
"""Pilna ilgalaikė HA optimizacija – nuotolinis diegimas per Nabu Casa."""

from __future__ import annotations

import asyncio
import json
import os
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HA_URL = os.environ.get("HA_URL", "https://44w46xbp7oj71nyfrck4gkg9uuk7nfqk.ui.nabu.casa")
HA_TOKEN = os.environ["HA_TOKEN"]
CTX = ssl.create_default_context()

FRIGATE_SLUG = "ccab4aaf_frigate"
FRIGATE_CONFIG = f"/addon_configs/{FRIGATE_SLUG}/config.yml"
VOICE_ADDONS = ("core_whisper", "core_piper", "core_openwakeword")

PERF_BEGIN = "# === INSTALIKA_PERFORMANCE_BEGIN ==="
PERF_END = "# === INSTALIKA_PERFORMANCE_END ==="
PERF_BLOCK = """# === INSTALIKA_PERFORMANCE_BEGIN ===
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
# === INSTALIKA_PERFORMANCE_END ===
"""

DISABLE_INTEGRATIONS = {"dhcp", "ssdp", "dlna_dmr", "dlna_dms", "cast", "analytics", "speedtestdotnet", "upnp", "ibeacon"}


def retry(label: str, fn, attempts: int = 12, delay: float = 5):
    for i in range(attempts):
        try:
            return fn()
        except Exception as e:
            print(f"  {label} [{i + 1}/{attempts}]: {type(e).__name__}: {e}")
            time.sleep(delay)
    raise RuntimeError(f"{label} nepavyko")


def api_get(path: str):
    req = urllib.request.Request(f"{HA_URL}{path}", headers={"Authorization": f"Bearer {HA_TOKEN}"})
    with urllib.request.urlopen(req, timeout=90, context=CTX) as r:
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


def patch_configuration(cfg: str) -> str:
    cfg = cfg.replace("scan_interval: 5", "scan_interval: 30")
    cfg = cfg.replace("scan_interval: 10", "scan_interval: 30")
    if PERF_BEGIN in cfg:
        cfg = re.sub(
            rf"{re.escape(PERF_BEGIN)}.*?{re.escape(PERF_END)}",
            PERF_BLOCK.strip(),
            cfg,
            flags=re.DOTALL,
        )
    elif "purge_keep_days:" not in cfg:
        cfg = cfg.rstrip() + "\n\n" + PERF_BLOCK + "\n"
    return cfg


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


async def supervisor_post(endpoint: str):
    import websockets

    async with websockets.connect(HA_URL.replace("https://", "wss://") + "/api/websocket", ssl=CTX, open_timeout=45) as ws:
        await ws.recv()
        await ws.send(json.dumps({"type": "auth", "access_token": HA_TOKEN}))
        await ws.recv()
        await ws.send(json.dumps({"id": 1, "type": "supervisor/api", "endpoint": endpoint, "method": "post"}))
        while True:
            r = json.loads(await ws.recv())
            if r.get("id") == 1:
                return r


async def supervisor_get(endpoint: str):
    import websockets

    async with websockets.connect(HA_URL.replace("https://", "wss://") + "/api/websocket", ssl=CTX, open_timeout=45) as ws:
        await ws.recv()
        await ws.send(json.dumps({"type": "auth", "access_token": HA_TOKEN}))
        await ws.recv()
        await ws.send(json.dumps({"id": 1, "type": "supervisor/api", "endpoint": endpoint, "method": "get"}))
        while True:
            r = json.loads(await ws.recv())
            if r.get("id") == 1:
                return r


async def set_addon_boot_manual(slug: str):
    import websockets

    async with websockets.connect(HA_URL.replace("https://", "wss://") + "/api/websocket", ssl=CTX, open_timeout=45) as ws:
        await ws.recv()
        await ws.send(json.dumps({"type": "auth", "access_token": HA_TOKEN}))
        await ws.recv()
        info = None
        await ws.send(json.dumps({"id": 1, "type": "supervisor/api", "endpoint": f"/addons/{slug}/info", "method": "get"}))
        while True:
            r = json.loads(await ws.recv())
            if r.get("id") == 1:
                info = r.get("result", {}).get("data", r.get("result", {}))
                break
        options = info.get("options", {}) if isinstance(info, dict) else {}
        options["boot"] = "manual"
        await ws.send(
            json.dumps(
                {
                    "id": 2,
                    "type": "supervisor/api",
                    "endpoint": f"/addons/{slug}/options",
                    "method": "post",
                    "data": options,
                }
            )
        )
        while True:
            r = json.loads(await ws.recv())
            if r.get("id") == 2:
                return r


async def ws_disable_heavy_entities():
    import websockets

    stats = {"integrations": 0, "image": 0}
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

        for e in (await call("config/config_entries/list")).get("result", []):
            if e.get("disabled_by") or e.get("domain") not in DISABLE_INTEGRATIONS:
                continue
            if (await call("config_entries/disable", entry_id=e["entry_id"], disabled_by="user")).get("success"):
                stats["integrations"] += 1
                print(f"    integracija išjungta: {e.get('domain')}")

        for ent in (await call("config/entity_registry/list")).get("result", []):
            eid = ent.get("entity_id", "")
            if ent.get("disabled_by") or not eid.startswith("image."):
                continue
            if (await call("config/entity_registry/update", entity_id=eid, disabled_by="user")).get("success"):
                stats["image"] += 1
    return stats


def optimize_frigate(cfg: str) -> str:
    sys.path.insert(0, str(REPO / "homeassistant" / "scripts"))
    from importlib.util import spec_from_loader, module_from_spec
    from importlib.machinery import SourceFileLoader

    mod_path = REPO / "homeassistant" / "scripts" / "frigate-optimize-local.py"
    spec = spec_from_loader("fol", SourceFileLoader("fol", str(mod_path)))
    mod = module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    optimized, _ = mod.optimize_config(cfg)
    return optimized


def metrics():
    s = api_get("/api/states/sensor.ha_host_metrikos")
    a = s["attributes"]
    return a.get("cpu_usage"), a.get("ram_pct"), a.get("load_1")


def main() -> int:
    print("=== HA ilgalaikė optimizacija ===")

    retry("HA API", lambda: api_get("/api/"))
    cpu0, ram0, load0 = retry("metrics", metrics)
    print(f"PRIEŠ: CPU {cpu0}% | RAM {ram0}% | load {load0}")

    ingress, session = retry("File editor", lambda: asyncio.run(file_editor()))

    cfg = retry("configuration.yaml", lambda: fe_download(ingress, session, "configuration.yaml"))
    cfg = patch_configuration(cfg)
    retry("upload configuration.yaml", lambda: fe_upload(ingress, session, "configuration.yaml", cfg))
    print("✓ configuration.yaml")

    uploads = [
        ("packages/ha_host_monitor.yaml", REPO / "homeassistant/packages/ha_host_monitor.yaml"),
        ("packages/ha_performance.yaml", REPO / "homeassistant/packages/ha_performance.yaml"),
        ("packages/ha_performance_guard.yaml", REPO / "homeassistant/packages/ha_performance_guard.yaml"),
        ("ha-host-metrics.sh", REPO / "homeassistant/scripts/ha-host-metrics.sh"),
        ("frigate-optimize-local.py", REPO / "homeassistant/scripts/frigate-optimize-local.py"),
    ]
    for remote, local in uploads:
        retry(f"upload {remote}", lambda r=remote, l=local: fe_upload(ingress, session, r, l.read_text()))
        print(f"✓ {remote}")

    try:
        frigate_cfg = fe_download(ingress, session, FRIGATE_CONFIG)
        optimized = optimize_frigate(frigate_cfg)
        fe_upload(ingress, session, FRIGATE_CONFIG, optimized)
        print("✓ Frigate config optimizuotas")
    except Exception as e:
        print(f"!! Frigate: {e}")

    print("Balso addonai...")
    for slug in VOICE_ADDONS:
        try:
            asyncio.run(supervisor_post(f"/addons/{slug}/stop"))
            asyncio.run(set_addon_boot_manual(slug))
            print(f"  ✓ {slug} stop + boot manual")
        except Exception as e:
            print(f"  !! {slug}: {e}")

    print("Frigate perkrovimas...")
    r = asyncio.run(supervisor_post(f"/addons/{FRIGATE_SLUG}/restart"))
    print(f"  {r.get('success', r)}")

    print("Išjungiami image.* entitetai (jei įmanoma)...")
    try:
        stats = asyncio.run(ws_disable_heavy_entities())
        print(f"  integracijos={stats['integrations']}, image={stats['image']}")
    except Exception as e:
        print(f"  praleista: {e}")

    print("Perkraunama (tik reload, ne restart)...")
    retry("reload_core_config", lambda: api_post("homeassistant", "reload_core_config"))
    time.sleep(4)
    for dom, svc in [("template", "reload"), ("modbus", "reload")]:
        try:
            api_post(dom, svc)
        except Exception:
            pass
    try:
        api_post("recorder", "purge", {"keep_days": 5})
    except Exception:
        pass

    print("Laukiama 90s...")
    time.sleep(90)
    cpu1, ram1, load1 = retry("metrics po", metrics, attempts=15, delay=10)
    print(f"PO:   CPU {cpu1}% | RAM {ram1}% | load {load1}")
    print("\nĮjungta automatinė apsauga (ha_performance_guard.yaml)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
