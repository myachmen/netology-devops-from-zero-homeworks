#!/usr/bin/env python3
"""Delegate unchanged protected dynamic inventory; load adjacent project group_vars."""
from pathlib import Path
import runpy

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parent.parent / "kubespray-current" / "inventory.py"), run_name="__main__")
