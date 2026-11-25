#!/usr/bin/env python3
"""
Quick launcher for Avito SDK Pro GUI.
Can be executed directly: python run_gui.py
Or built into standalone Windows executable with PyInstaller.
"""

import os
import sys
from pathlib import Path

# Prevent crashes in PyInstaller windowed mode (where sys.stdout / sys.stderr are None)
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

# Fix SSL certificates in frozen / PyInstaller environment (prevents curl: 77)
try:
    import certifi
    ca_bundle = certifi.where()
    os.environ["SSL_CERT_FILE"] = ca_bundle
    os.environ["REQUESTS_CA_BUNDLE"] = ca_bundle
    os.environ["CURL_CA_BUNDLE"] = ca_bundle
except Exception:
    pass

# Ensure src/ is on sys.path if running from source
src_dir = Path(__file__).resolve().parent / "src"
if src_dir.exists():
    sys.path.insert(0, str(src_dir))

try:
    from avito_sdk import __version__ as _app_version
except Exception:
    _app_version = "0.4.4"

# Ensure Windows Taskbar displays custom application icon instead of default Python icon
if sys.platform.startswith("win"):
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            f"eminsk.avitosdkpro.monitor.{_app_version}"
        )
    except Exception:
        pass

from avito_sdk.gui.app import run_app

if __name__ == "__main__":
    run_app()
