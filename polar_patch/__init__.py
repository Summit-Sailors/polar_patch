# modules/__init__.py

from .monkey_patcher import PolarsMonkeyPatcher

def apply_patches():
    patcher = PolarsMonkeyPatcher()
    patcher.apply_patches()

