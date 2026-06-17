"""Komandinės eilutės sąsaja Wake-on-LAN įrankiui."""

import argparse
import json
import sys
from pathlib import Path

from wol.wake import send_magic_packet


def load_computers(config_path: Path) -> dict[str, dict]:
    with config_path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("Konfigūracija turi būti JSON objektas")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="wol",
        description="Kompiuterių įjungimas per LAN (Wake-on-LAN)",
    )
    parser.add_argument(
        "target",
        nargs="?",
        help="Kompiuterio vardas iš konfigūracijos arba MAC adresas",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=Path("computers.json"),
        help="Kelias į kompiuterių konfigūraciją (numatyta: computers.json)",
    )
    parser.add_argument(
        "-b",
        "--broadcast",
        default="255.255.255.255",
        help="Transliacijos IP adresas",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=9,
        help="UDP prievadas (numatytasis: 9)",
    )
    parser.add_argument(
        "-i",
        "--interface",
        help="Vietinės sąsajos IP (subnet broadcast)",
    )
    parser.add_argument(
        "-l",
        "--list",
        action="store_true",
        help="Parodyti kompiuterių sąrašą iš konfigūracijos",
    )

    args = parser.parse_args(argv)

    if args.list:
        if not args.config.exists():
            print(f"Konfigūracijos failas nerastas: {args.config}", file=sys.stderr)
            return 1
        computers = load_computers(args.config)
        for name, info in computers.items():
            mac = info.get("mac", "?")
            desc = info.get("description", "")
            line = f"  {name:20} {mac}"
            if desc:
                line += f"  – {desc}"
            print(line)
        return 0

    if not args.target:
        parser.print_help()
        return 1

    mac = args.target
    broadcast = args.broadcast
    name = args.target

    if args.config.exists() and not _looks_like_mac(args.target):
        computers = load_computers(args.config)
        if args.target in computers:
            entry = computers[args.target]
            mac = entry["mac"]
            broadcast = entry.get("broadcast", broadcast)
            name = args.target

    try:
        send_magic_packet(
            mac,
            ip_address=broadcast,
            port=args.port,
            interface=args.interface,
        )
    except (ValueError, OSError) as exc:
        print(f"Klaida: {exc}", file=sys.stderr)
        return 1

    print(f"Magic packet išsiųstas: {name} ({mac}) → {broadcast}:{args.port}")
    return 0


def _looks_like_mac(value: str) -> bool:
    cleaned = value.replace(":", "").replace("-", "")
    return len(cleaned) == 12 and all(c in "0123456789abcdefABCDEF" for c in cleaned)


if __name__ == "__main__":
    raise SystemExit(main())
