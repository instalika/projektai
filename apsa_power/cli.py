"""APSA Power Instalika – komandinė eilutė."""

import argparse
import sys
from pathlib import Path

from apsa_power import __app_name__, __version__
from apsa_power.config import DEFAULT_CONFIG, load_computers, resolve_target
from apsa_power.wake import send_magic_packet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="apsa-power",
        description=f"{__app_name__} – kompiuterių įjungimas per LAN",
    )
    parser.add_argument("--version", action="version", version=f"{__app_name__} {__version__}")
    parser.add_argument(
        "target",
        nargs="?",
        help="Kompiuterio vardas iš konfigūracijos arba MAC adresas",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="Kelias į kompiuterių konfigūraciją",
    )
    parser.add_argument("-b", "--broadcast", default="255.255.255.255", help="Transliacijos IP")
    parser.add_argument("-p", "--port", type=int, default=9, help="UDP prievadas")
    parser.add_argument("-i", "--interface", help="Vietinės sąsajos IP")
    parser.add_argument("-l", "--list", action="store_true", help="Kompiuterių sąrašas")
    parser.add_argument(
        "--web",
        action="store_true",
        help="Paleisti web valdymo panelę",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Web serverio adresas")
    parser.add_argument("--web-port", type=int, default=8080, help="Web serverio prievadas")

    args = parser.parse_args(argv)

    if args.web:
        from apsa_power.web import run_server

        run_server(host=args.host, port=args.web_port, config_path=args.config)
        return 0

    if args.list:
        if not args.config.exists():
            print(f"Konfigūracijos failas nerastas: {args.config}", file=sys.stderr)
            return 1
        computers = load_computers(args.config)
        print(f"\n{__app_name__} – kompiuterių sąrašas:\n")
        for name, info in computers.items():
            mac = info.get("mac", "?")
            desc = info.get("description", "")
            line = f"  {name:20} {mac}"
            if desc:
                line += f"  – {desc}"
            print(line)
        print()
        return 0

    if not args.target:
        parser.print_help()
        return 1

    name, mac, broadcast = resolve_target(args.target, args.config, args.broadcast)
    if args.broadcast != "255.255.255.255":
        broadcast = args.broadcast

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

    print(f"[{__app_name__}] Įjungimo signalas išsiųstas: {name} ({mac}) → {broadcast}:{args.port}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
