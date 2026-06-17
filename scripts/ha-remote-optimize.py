#!/usr/bin/env python3
"""Nuotolinė HA optimizacija – recorder, logger, nereikalingų integracijų išjungimas."""

from __future__ import annotations

import asyncio
import json
import os
import ssl
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
HA_URL = os.environ.get("HA_URL", "https://44w46xbp7oj71nyfrck4gkg9uuk7nfqk.ui.nabu.casa")
HA_TOKEN = os.environ["HA_TOKEN"]
CTX = ssl.create_default_context()

DISABLE_DOMAINS = {
    "dhcp",
    "ssdp",
    "dlna_dmr",
    "dlna_dms",
    "cast",
    "ibeacon",
    "analytics",
    "rpi_power",
    "speedtestdotnet",
    "upnp",
}

DISABLE_TITLE_KEYWORDS = ("speedtest", "dlna", "google cast", "upnp", "bluetooth")

RECORDER_BLOCK = """# --- našumo optimizacija ---
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
      - sensor.*_signal*
      - binary_sensor.*update*
      - camera.*
"""

LOGGER_BLOCK = """logger:
  default: warning
  logs:
    homeassistant.components.mqtt: error
    homeassistant.components.recorder: warning
    homeassistant.components.camera: error
    homeassistant.loader: error
"""

HISTORY_BLOCK = """history:
  exclude:
    domains:
      - image
      - automation
      - script
      - scene
      - updater
      - event
      - device_tracker
"""

STREAM_BLOCK = """stream:
  ll_hls: false
"""


class HAWebSocket:
    def __init__(self) -> None:
        self._ws: Any = None
        self._next_id = 1

    async def connect(self) -> None:
        import websockets

        self._ws = await websockets.connect(
            HA_URL.replace("https://", "wss://") + "/api/websocket",
            ssl=CTX,
            open_timeout=60,
        )
        await self._ws.recv()
        await self._ws.send(json.dumps({"type": "auth", "access_token": HA_TOKEN}))
        auth = json.loads(await self._ws.recv())
        if auth.get("type") != "auth_ok":
            raise RuntimeError(f"Auth failed: {auth}")

    async def call(self, msg_type: str, **kwargs: Any) -> dict:
        assert self._ws
        mid = self._next_id
        self._next_id += 1
        await self._ws.send(json.dumps({"id": mid, "type": msg_type, **kwargs}))
        while True:
            r = json.loads(await self._ws.recv())
            if r.get("id") == mid:
                return r

    async def close(self) -> None:
        if self._ws:
            await self._ws.close()


def wait_online(max_wait: int = 300) -> None:
    for i in range(max_wait // 5):
        try:
            req = urllib.request.Request(f"{HA_URL}/api/", headers={"Authorization": f"Bearer {HA_TOKEN}"})
            with urllib.request.urlopen(req, timeout=15, context=CTX) as r:
                print(f"HA pasiekiamas: {json.loads(r.read())['version']}")
                return
        except Exception:
            if i < 3 or i % 5 == 0:
                print(f"  laukiama HA... ({i + 1})")
            time.sleep(5)
    raise RuntimeError("HA nepasiekiamas")


async def get_ingress() -> tuple[str, str]:
    ws = HAWebSocket()
    await ws.connect()
    r1 = await ws.call("supervisor/api", endpoint="/addons/core_configurator/info", method="get")
    r2 = await ws.call("supervisor/api", endpoint="/ingress/session", method="post")
    await ws.close()
    return r1["result"]["ingress_entry"], r2["result"]["session"]


def download(ingress: str, session: str, path: str) -> str:
    req = urllib.request.Request(f"{HA_URL}{ingress}/api/file?filename=/homeassistant/{path}")
    req.add_header("Cookie", f"ingress_session={session}")
    with urllib.request.urlopen(req, timeout=120, context=CTX) as r:
        return r.read().decode()


def upload(ingress: str, session: str, path: str, content: str) -> None:
    data = urllib.parse.urlencode({"filename": f"/homeassistant/{path}", "text": content}).encode()
    req = urllib.request.Request(f"{HA_URL}{ingress}/api/save", data=data, method="POST")
    req.add_header("Cookie", f"ingress_session={session}")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=120, context=CTX) as r:
        resp = json.loads(r.read().decode())
        if resp.get("error"):
            raise RuntimeError(f"Upload failed {path}: {resp}")


def call_service(domain: str, service: str, data: dict | None = None) -> None:
    body = json.dumps(data or {}).encode()
    req = urllib.request.Request(
        f"{HA_URL}/api/services/{domain}/{service}",
        data=body,
        headers={"Authorization": f"Bearer {HA_TOKEN}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120, context=CTX) as r:
        print(f"  {domain}.{service}: HTTP {r.status}")


def patch_configuration_yaml(cfg: str) -> str:
    patches = [
        ("purge_keep_days:", RECORDER_BLOCK, "recorder"),
        ("\nlogger:", LOGGER_BLOCK, "logger"),
        ("\nhistory:", HISTORY_BLOCK, "history"),
        ("\nstream:", STREAM_BLOCK, "stream"),
    ]
    for marker, block, name in patches:
        if marker.strip(":") in cfg and name == "recorder" and "purge_keep_days:" in cfg:
            print(f"  {name}: jau konfigūruotas")
            continue
        if name == "logger" and "logger:" in cfg:
            print(f"  {name}: jau yra")
            continue
        if name == "history" and "history:" in cfg:
            print(f"  {name}: jau yra")
            continue
        if name == "stream" and "stream:" in cfg:
            print(f"  {name}: jau yra")
            continue
        if name == "recorder" and "recorder:" in cfg:
            print(f"  {name}: jau yra (neperrašoma)")
            continue
        cfg = cfg.rstrip() + "\n\n" + block + "\n"
        print(f"  {name}: pridėtas")
    return cfg


async def disable_heavy_integrations(ws: HAWebSocket) -> list[str]:
    r = await ws.call("config/config_entries/list")
    disabled = []
    for e in r.get("result", []):
        if e.get("disabled_by"):
            continue
        domain = e.get("domain", "")
        title = (e.get("title") or "").lower()
        if domain in DISABLE_DOMAINS or any(k in title for k in DISABLE_TITLE_KEYWORDS):
            dr = await ws.call(
                "config_entries/disable",
                entry_id=e["entry_id"],
                disabled_by="user",
            )
            if dr.get("success"):
                disabled.append(f"{domain}:{e.get('title')}")
                print(f"  Išjungta: {domain} – {e.get('title')}")
    return disabled


async def disable_entities_by_prefix(
    ws: HAWebSocket, prefix: str, keep: set[str] | None = None, limit: int = 9999
) -> int:
    r = await ws.call("config/entity_registry/list")
    keep = keep or set()
    count = 0
    for ent in r.get("result", []):
        if count >= limit:
            break
        eid = ent.get("entity_id", "")
        if not eid.startswith(prefix):
            continue
        if ent.get("disabled_by") or eid in keep:
            continue
        dr = await ws.call(
            "config/entity_registry/update",
            entity_id=eid,
            disabled_by="user",
        )
        if dr.get("success"):
            count += 1
            if count <= 8:
                print(f"  Išjungta: {eid}")
    if count > 8:
        print(f"  ... iš viso {count} {prefix}* entitetų")
    return count


async def disable_update_entities(ws: HAWebSocket) -> int:
    r = await ws.call("config/entity_registry/list")
    count = 0
    for ent in r.get("result", []):
        eid = ent.get("entity_id", "")
        if not eid.startswith("update."):
            continue
        if ent.get("disabled_by"):
            continue
        dr = await ws.call(
            "config/entity_registry/update",
            entity_id=eid,
            disabled_by="user",
        )
        if dr.get("success"):
            count += 1
    print(f"  Išjungta update.* entitetų: {count}")
    return count


def verify_metrics() -> None:
    req = urllib.request.Request(f"{HA_URL}/api/states/sensor.ha_host_metrikos", headers={"Authorization": f"Bearer {HA_TOKEN}"})
    with urllib.request.urlopen(req, timeout=60, context=CTX) as r:
        s = json.loads(r.read().decode())
    a = s.get("attributes", {})
    print(f"  CPU: {a.get('cpu_usage')}% | RAM: {a.get('ram_pct')}% | load: {a.get('load_1')}")
    req2 = urllib.request.Request(f"{HA_URL}/api/states", headers={"Authorization": f"Bearer {HA_TOKEN}"})
    with urllib.request.urlopen(req2, timeout=90, context=CTX) as r2:
        states = json.loads(r2.read().decode())
    active = sum(1 for s in states if s["state"] not in ("unavailable", "unknown"))
    print(f"  Aktyvūs entitetai: {active} / {len(states)}")


async def main_async() -> int:
    print("=== HA optimizacija ===")
    wait_online()

    ingress, session = await get_ingress()
    print("File editor: OK")

    cfg = download(ingress, session, "configuration.yaml")
    cfg = patch_configuration_yaml(cfg)
    upload(ingress, session, "configuration.yaml", cfg)

    host_pkg = (REPO / "homeassistant/packages/ha_host_monitor.yaml").read_text()
    upload(ingress, session, "packages/ha_host_monitor.yaml", host_pkg)
    print("Uploaded: packages/ha_host_monitor.yaml")

    perf = (REPO / "homeassistant/packages/ha_performance.yaml").read_text()
    upload(ingress, session, "packages/ha_performance.yaml", perf)
    print("Uploaded: packages/ha_performance.yaml")

    ws = HAWebSocket()
    await ws.connect()

    print("\n→ Integracijos...")
    n_int = len(await disable_heavy_integrations(ws))

    print("\n→ Image entitetai (DB apkrova – išjungiama iki 50/s batch)...")
    n_img = await disable_entities_by_prefix(ws, "image.", limit=220)

    print("\n→ Update entitetai (firmware – nereikalingi kas sekundę)...")
    n_upd = await disable_update_entities(ws)

    await ws.close()

    print("\n→ Perkraunama...")
    try:
        call_service("homeassistant", "reload_core_config")
        time.sleep(3)
        call_service("recorder", "purge", {"keep_days": 5, "repack": True})
    except Exception as e:
        print(f"  {e}")

    print("\n→ Pilnas restart...")
    try:
        call_service("homeassistant", "restart")
    except Exception:
        pass

    print("\n→ Laukiam 150s...")
    time.sleep(150)
    wait_online(420)
    print("\n=== Po optimizacijos ===")
    verify_metrics()
    print(f"\nSantrauka: integracijų={n_int}, image={n_img}, update={n_upd}")
    return 0


def main() -> int:
    return asyncio.run(main_async())


if __name__ == "__main__":
    sys.exit(main())
