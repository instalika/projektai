"""Kompiuterių konfigūracijos valdymas."""

import json
from pathlib import Path

DEFAULT_CONFIG = Path("computers.json")


def load_computers(config_path: Path = DEFAULT_CONFIG) -> dict[str, dict]:
    with config_path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("Konfigūracija turi būti JSON objektas")
    return data


def looks_like_mac(value: str) -> bool:
    cleaned = value.replace(":", "").replace("-", "")
    return len(cleaned) == 12 and all(c in "0123456789abcdefABCDEF" for c in cleaned)


def resolve_target(
    target: str,
    config_path: Path = DEFAULT_CONFIG,
    default_broadcast: str = "255.255.255.255",
) -> tuple[str, str, str]:
    """Grąžina (vardas, mac, broadcast)."""
    if config_path.exists() and not looks_like_mac(target):
        computers = load_computers(config_path)
        if target in computers:
            entry = computers[target]
            return (
                target,
                entry["mac"],
                entry.get("broadcast", default_broadcast),
            )
    return target, target, default_broadcast
