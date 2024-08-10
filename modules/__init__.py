# modules/__init__.py

from .plugin_scanner import scan_plugins_in_code

print("Initializing the polar-patch modules package")

__all__ = ["scan_plugins_in_code"]
