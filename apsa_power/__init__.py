"""Instalika Power – kompiuterių įjungimas per LAN."""

__version__ = "1.1.0"
__app_name__ = "Instalika Power"

from apsa_power.wake import send_magic_packet, wake

__all__ = ["send_magic_packet", "wake", "__version__", "__app_name__"]
