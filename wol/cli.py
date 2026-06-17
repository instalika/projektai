"""Atgalinis suderinamumas – naudokite: python -m apsa_power"""

import sys

from apsa_power.cli import main as _main


def main(argv: list[str] | None = None) -> int:
    return _main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
