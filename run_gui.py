#!/usr/bin/env python3
"""
Quick launcher for Avito SDK Pro GUI.
Can be executed directly: python run_gui.py
"""

import sys
from pathlib import Path

# Ensure src/ is on sys.path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from avito_sdk.gui.app import run_app

if __name__ == "__main__":
    run_app()
