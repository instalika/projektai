"""APSA Power Instalika – kompiuterių įjungimas per LAN."""

__version__ = "1.0.0"
__app_name__ = "APSA Power Instalika"

from apsa_power.wake import send_magic_packet, wake

__all__ = ["send_magic_packet", "wake", "__version__", "__app_name__"]
