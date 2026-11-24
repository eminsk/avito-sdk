"""
Unit tests for the avito-sdk GUI module and configuration persistence.
"""

import json
from pathlib import Path
import pytest

from avito_sdk.gui.app import GUIConfig


def test_gui_config_defaults_and_serialization(tmp_path, monkeypatch):
    test_cfg_path = tmp_path / "gui_config.json"
    monkeypatch.setattr(GUIConfig, "CONFIG_PATH", test_cfg_path)

    cfg = GUIConfig.load()
    assert len(cfg.urls) > 0
    assert cfg.interval_sec == 30
    assert cfg.only_new is True

    # Modify and save
    cfg.interval_sec = 45
    cfg.tg_token = "123456:ABC-DEF"
    cfg.tg_chat_id = "987654321"
    cfg.proxy_string = "http://user:pass@1.2.3.4:8080"
    cfg.save()

    assert test_cfg_path.exists()
    loaded_data = json.loads(test_cfg_path.read_text(encoding="utf-8"))
    assert loaded_data["interval_sec"] == 45
    assert loaded_data["tg_token"] == "123456:ABC-DEF"

    # Reload from disk
    reloaded_cfg = GUIConfig.load()
    assert reloaded_cfg.interval_sec == 45
    assert reloaded_cfg.tg_token == "123456:ABC-DEF"
    assert reloaded_cfg.proxy_string == "http://user:pass@1.2.3.4:8080"


def test_gui_module_exports():
    from avito_sdk.gui import main_gui
    assert callable(main_gui)
