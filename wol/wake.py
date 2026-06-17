"""Atgalinis suderinamumas – naudokite apsa_power paketą."""

from apsa_power.wake import build_magic_packet, normalize_mac, send_magic_packet, wake

__all__ = ["build_magic_packet", "normalize_mac", "send_magic_packet", "wake"]
