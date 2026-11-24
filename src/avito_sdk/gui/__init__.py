"""
Graphical User Interface (GUI) for avito-sdk.
Modern, dark-themed, resilient desktop application for Windows, macOS and Linux.
"""

from __future__ import annotations

def main_gui() -> None:
    """Entry point for the avito-gui command."""
    from avito_sdk.gui.app import run_app
    run_app()

__all__ = ["main_gui"]
