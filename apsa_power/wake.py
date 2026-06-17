"""Wake-on-LAN magic packet siuntimas."""

import re
import socket
from typing import Union

DEFAULT_PORT = 9
BROADCAST = "255.255.255.255"

_MAC_RE = re.compile(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$")


def normalize_mac(mac: str) -> bytes:
    mac = mac.strip().replace("-", ":").upper()
    if not _MAC_RE.match(mac):
        raise ValueError(f"Neteisingas MAC adresas: {mac!r}")
    return bytes(int(part, 16) for part in mac.split(":"))


def build_magic_packet(mac: Union[str, bytes]) -> bytes:
    if isinstance(mac, str):
        mac = normalize_mac(mac)
    if len(mac) != 6:
        raise ValueError("MAC adresas turi būti 6 baitų")
    return b"\xff" * 6 + mac * 16


def send_magic_packet(
    mac: str,
    *,
    ip_address: str = BROADCAST,
    port: int = DEFAULT_PORT,
    interface: str | None = None,
) -> None:
    packet = build_magic_packet(mac)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        if interface:
            sock.bind((interface, 0))
        sock.sendto(packet, (ip_address, port))


def wake(mac: str, **kwargs) -> None:
    send_magic_packet(mac, **kwargs)
