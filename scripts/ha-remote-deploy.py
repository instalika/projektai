#!/usr/bin/env python3
"""Nuotolinis HA konfigūracijos įdiegimas per Nabu Casa + File editor ingress."""

from __future__ import annotations

import asyncio
import json
import os
import ssl
import sys
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HA_URL = os.environ.get("HA_URL", "https://44w46xbp7oj71nyfrck4gkg9uuk7nfqk.ui.nabu.casa")
HA_TOKEN = os.environ["HA_TOKEN"]
CTX = ssl.create_default_context()

HOME_BUTTON = """
          - type: button
            name: HA Serveris PC
            icon: mdi:server-network
            show_state: true
            entity: sensor.ha_host_busena_santrauka
            tap_action:
              action: navigate
              navigation_path: /lovelace/ha-pc
            hold_action:
              action: call-service
              service: script.ha_host_atnaujinti_metrikas
"""

HA_PC_VIEW = """
  # ==================================================
  # HA SERVERIS PC (192.168.0.97)
  # ==================================================
  - title: HA Serveris
    path: ha-pc
    icon: mdi:server-network
    cards:
      - type: markdown
        content: |
          ## HA serveris {{ states('sensor.ha_host_ip') }}
          **{{ states('sensor.ha_host_busena_santrauka') }}**
          Veikia: **{{ states('sensor.ha_host_veikimo_laikas') }}** h | HA OS

      - type: glance
        entities:
          - entity: sensor.ha_host_cpu_naudojimas
            name: CPU
          - entity: sensor.ha_host_ram_naudojimas
            name: RAM
          - entity: sensor.ha_host_cpu_temperatura
            name: Temp
          - entity: sensor.ha_host_ventiliatorius
            name: Vent.
          - entity: sensor.ha_host_diskas_naudojimas
            name: Diskas

      - type: horizontal-stack
        cards:
          - type: gauge
            entity: sensor.ha_host_cpu_naudojimas
            name: CPU %
            min: 0
            max: 100
            severity:
              green: 0
              yellow: 60
              red: 85
          - type: gauge
            entity: sensor.ha_host_ram_naudojimas
            name: RAM %
            min: 0
            max: 100
            severity:
              green: 0
              yellow: 70
              red: 90

      - type: entities
        title: Momentiniai duomenys
        show_header_toggle: false
        entities:
          - entity: sensor.ha_host_cpu_naudojimas
          - entity: sensor.ha_host_cpu_temperatura
          - entity: sensor.ha_host_ram_naudojimas
          - entity: sensor.ha_host_ram_naudota
          - entity: sensor.ha_host_ram_viso
          - entity: sensor.ha_host_diskas_naudojimas
          - entity: sensor.ha_host_diskas_laisva
          - entity: sensor.ha_host_diskas_viso
          - entity: sensor.ha_host_apkrova_1min
          - entity: sensor.ha_host_apkrova_5min
          - entity: sensor.ha_host_veikimo_laikas
          - entity: sensor.ha_host_ventiliatorius
          - entity: sensor.ha_host_ip
          - entity: binary_sensor.ha_host_perkaitimas
          - entity: binary_sensor.ha_host_ram_kritine

      - type: button
        name: Atnaujinti dabar
        icon: mdi:refresh
        tap_action:
          action: call-service
          service: script.ha_host_atnaujinti_metrikas

      - type: statistics-graph
        title: CPU ir RAM (7 d.)
        entities:
          - sensor.ha_host_cpu_naudojimas
          - sensor.ha_host_ram_naudojimas
        stat_types:
          - mean
          - max
        chart_type: line
        period: hour
        days_to_show: 7

      - type: history-graph
        title: Istorija (24 h)
        hours_to_show: 24
        entities:
          - sensor.ha_host_cpu_naudojimas
          - sensor.ha_host_ram_naudojimas
          - sensor.ha_host_cpu_temperatura

      - type: button
        name: Atgal į Pradžią
        icon: mdi:arrow-left
        tap_action:
          action: navigate
          navigation_path: /lovelace/home
"""


async def get_ingress() -> tuple[str, str]:
    import websockets

    async with websockets.connect(HA_URL.replace("https://", "wss://") + "/api/websocket", ssl=CTX) as ws:
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


def download(ingress: str, session: str, path: str) -> str:
    req = urllib.request.Request(f"{HA_URL}{ingress}/api/file?filename=/homeassistant/{path}")
    req.add_header("Cookie", f"ingress_session={session}")
    with urllib.request.urlopen(req, timeout=60, context=CTX) as r:
        return r.read().decode()


def upload(ingress: str, session: str, path: str, content: str) -> None:
    data = urllib.parse.urlencode({"filename": f"/homeassistant/{path}", "text": content}).encode()
    req = urllib.request.Request(f"{HA_URL}{ingress}/api/save", data=data, method="POST")
    req.add_header("Cookie", f"ingress_session={session}")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=120, context=CTX) as r:
        resp = r.read().decode()
        try:
            data = json.loads(resp)
            if data.get("error"):
                raise RuntimeError(f"Upload failed {path}: {resp}")
        except json.JSONDecodeError:
            if "error" in resp.lower() and "success" not in resp.lower():
                raise RuntimeError(f"Upload failed {path}: {resp}")


def patch_configuration_yaml(cfg: str) -> str:
    old = """  minerio_sventupio_tinklo_rezimo_galia:
    name: Minerio Šventupio galia kai leidžia biržos kaina
    min: 2760
    max: 2760"""
    new = """  minerio_sventupio_tinklo_rezimo_galia:
    name: Minerio Šventupio galia kai leidžia biržos kaina
    min: 0
    max: 2760"""
    if old in cfg:
        cfg = cfg.replace(old, new)
        print("  configuration.yaml: pataisytas input_number (min/max)")
    elif "max: 2760" in cfg and "minerio_sventupio_tinklo_rezimo_galia" in cfg:
        print("  configuration.yaml: input_number jau pataisytas arba kitoks formatas")
    else:
        print("  configuration.yaml: input_number blokas nerastas – praleidžiama")
    return cfg


def call_service(domain: str, service: str) -> None:
    req = urllib.request.Request(
        f"{HA_URL}/api/services/{domain}/{service}",
        data=b"{}",
        headers={"Authorization": f"Bearer {HA_TOKEN}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60, context=CTX) as r:
        print(f"  {domain}.{service}: HTTP {r.status}")


def patch_ui_lovelace(ui: str) -> str:
    if "navigation_path: /lovelace/ha-pc" in ui:
        print("  ui-lovelace.yaml: mygtukas jau yra")
    else:
        marker = """          - type: button
            name: Sistema
            icon: mdi:server
            tap_action:
              action: navigate
              navigation_path: /lovelace/sistema"""
        if marker not in ui:
            raise RuntimeError("Nepavyko rasti Sistema mygtuko ui-lovelace.yaml")
        ui = ui.replace(marker, marker + HOME_BUTTON)
        print("  ui-lovelace.yaml: pridėtas mygtukas")

    if "\n    path: ha-pc\n" in ui or "path: ha-pc" in ui.split("HA SERVERIS PC")[-1][:200] if "HA SERVERIS PC" in ui else False:
        print("  ui-lovelace.yaml: vaizdas ha-pc jau yra")
    elif "# HA SERVERIS PC" in ui:
        print("  ui-lovelace.yaml: vaizdas jau yra")
    else:
        ui = ui.rstrip() + HA_PC_VIEW
        print("  ui-lovelace.yaml: pridėtas vaizdas ha-pc")
    return ui


def restart_ha() -> None:
    req = urllib.request.Request(
        f"{HA_URL}/api/services/homeassistant/restart",
        data=b"{}",
        headers={"Authorization": f"Bearer {HA_TOKEN}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30, context=CTX) as r:
        print(f"  HA restart: HTTP {r.status}")


def verify_sensors() -> None:
    req = urllib.request.Request(f"{HA_URL}/api/states", headers={"Authorization": f"Bearer {HA_TOKEN}"})
    with urllib.request.urlopen(req, timeout=60, context=CTX) as r:
        states = json.loads(r.read().decode())
    wanted = [
        "sensor.ha_host_cpu_naudojimas",
        "sensor.ha_host_ram_naudojimas",
        "sensor.ha_host_cpu_temperatura",
        "sensor.ha_host_ip",
    ]
    for eid in wanted:
        s = next((x for x in states if x["entity_id"] == eid), None)
        print(f"  {eid}: {s['state'] if s else 'NERASTA'}")


def main() -> int:
    print("=== HA nuotolinis įdiegimas ===")
    ingress, session = asyncio.run(get_ingress())
    print(f"File editor: OK")

    files = {
        "packages/ha_host_monitor.yaml": (REPO / "homeassistant/packages/ha_host_monitor.yaml").read_text(),
        "ha-host-metrics.sh": (REPO / "homeassistant/scripts/ha-host-metrics.sh").read_text(),
    }
    for path, content in files.items():
        upload(ingress, session, path, content)
        print(f"  Uploaded: {path}")

    cfg = download(ingress, session, "configuration.yaml")
    cfg = patch_configuration_yaml(cfg)
    upload(ingress, session, "configuration.yaml", cfg)
    print("  Uploaded: configuration.yaml")

    ui = download(ingress, session, "ui-lovelace.yaml")
    ui = patch_ui_lovelace(ui)
    upload(ingress, session, "ui-lovelace.yaml", ui)
    print("  Uploaded: ui-lovelace.yaml")

    print("\n→ Perkraunamas šablonų ir pagrindinės konfigūracijos...")
    try:
        call_service("template", "reload")
        call_service("homeassistant", "reload_core_config")
    except Exception as e:
        print(f"  Dalinė perkrova nepavyko ({e}) – daromas pilnas restart")

    print("\n→ Perkraunamas Home Assistant...")
    restart_ha()
    print("\n→ Laukiam 90s...")
    import time
    time.sleep(90)

    print("\n=== Patikra ===")
    try:
        verify_sensors()
    except Exception as e:
        print(f"  Patikra po restart: {e} (HA dar kraunasi – bandykite po minutės)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
