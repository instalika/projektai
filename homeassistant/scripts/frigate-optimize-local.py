#!/usr/bin/env python3
"""Frigate optimizacija lokaliai ant HA OS – mažesnis CPU, judesio įrašymas išlieka."""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

CONFIG_PATHS = [
    Path("/addon_configs/ccab4aaf_frigate/config.yml"),
    Path("/config/addon_configs/ccab4aaf_frigate/config.yml"),
]
MARKER = "# Optimizuota (instalika)"


def find_config() -> Path:
    for p in CONFIG_PATHS:
        if p.is_file():
            return p
    raise FileNotFoundError(f"Frigate config nerastas: {CONFIG_PATHS}")


def optimize_config(cfg: str) -> tuple[str, list[str]]:
    changes: list[str] = []
    orig = cfg

    if MARKER not in cfg:
        cfg = f"{MARKER}: CPU mažiau, motion įrašymas išliko\n" + cfg
        changes.append("pridėtas optimizacijos žymeklis")

    if "num_threads" not in cfg.split("detectors:")[1][:300]:
        cfg = cfg.replace(
            "detectors:\n  cpu1:\n    type: cpu",
            "detectors:\n  cpu1:\n    type: cpu\n    num_threads: 3",
        )
        changes.append("CPU detector: 3 gijos")

    cfg_new, n = re.subn(
        r"objects:\n  track:\n(?:  - .+\n)+",
        "objects:\n  track:\n  - person\n  - car\n  - dog\n  - cat\n",
        cfg,
        count=1,
    )
    if n:
        cfg = cfg_new
        changes.append("objektai: person, car, dog, cat")

    if "hwaccel_args" not in cfg:
        cfg = cfg.replace(
            "mqtt:\n",
            "ffmpeg:\n  hwaccel_args: preset-vaapi\n\nmqtt:\n",
            1,
        )
        changes.append("VAAPI hwaccel")

    cfg = re.sub(
        r"(\n    detect:\n      width: )960(\n      height: )540(\n      fps: )8",
        r"\g<1>640\g<2>360\g<3>4",
        cfg,
    )
    cfg = re.sub(
        r"(\n    detect:\n      width: )640(\n      height: )360(\n      fps: )5",
        r"\g<1>640\g<2>360\g<3>3",
        cfg,
    )
    if cfg != orig:
        changes.append("detect FPS/rezoliucija sumažinta")

    if "quality:" not in cfg.split("snapshots:")[-1][:400]:
        cfg = cfg.replace(
            "snapshots:\n  enabled: true",
            "snapshots:\n  enabled: true\n  quality: 75",
        )
        changes.append("snapshots quality 75")
    cfg = re.sub(r"retain:\n    default: 14", "retain:\n    default: 7", cfg)

    if "stationary:" not in cfg:
        cfg = cfg.replace(
            "detect:\n  enabled: true",
            "detect:\n  enabled: true\n  stationary:\n    interval: 50\n    threshold: 50\n    max_frames:\n      default: 300\n      objects:\n        person: 600\n        car: 900",
        )
        changes.append("stationary filtras")

    if "live:\n  height:" not in cfg:
        cfg = cfg.replace(
            "record:\n  enabled: true",
            "live:\n  height: 480\n  quality: 8\n\nrecord:\n  enabled: true",
        )
        changes.append("live view 480p")

    if not changes:
        changes = ["jau optimizuota"]
    return cfg, changes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    cfg_path = find_config()
    cfg = cfg_path.read_text(encoding="utf-8")
    backup = cfg_path.with_name(
        f"config.yml.backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    )
    shutil.copy2(cfg_path, backup)

    optimized, changes = optimize_config(cfg)
    if optimized != cfg:
        cfg_path.write_text(optimized, encoding="utf-8")

    if not args.quiet:
        print(f"Frigate config: {cfg_path}")
        print(f"Backup: {backup}")
        for c in changes:
            print(f"  - {c}")
        if "motion:\n    days: 3" in optimized and "continuous:\n    days: 0" in optimized:
            print("✓ Judesio įrašymas: motion 3d, continuous 0d")
    return 0


if __name__ == "__main__":
    sys.exit(main())
