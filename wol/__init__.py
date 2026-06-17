"""Wake-on-LAN (WoL) – kompiuterių įjungimas per tinklą."""

from wol.wake import send_magic_packet, wake

__all__ = ["send_magic_packet", "wake"]
