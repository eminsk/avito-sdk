"""Tests for CLI entrypoint."""

from avito_sdk.cli import main
from avito_sdk.models import Item


import pytest

def test_cli_help(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "High-performance Avito Scraper" in captured.out


def test_cli_drops(tmp_path, capsys):
    db_path = tmp_path / "test_cli.db"
    ret = main(["drops", "--db", str(db_path)])
    assert ret == 0
    captured = capsys.readouterr()
    assert "No price drops recorded yet" in captured.out


def test_cli_item_mock(monkeypatch, capsys):
    from avito_sdk.client import AvitoClient

    mock_item = Item(
        id=999888,
        title="Тестовый товар CLI",
        price=12500,
        seller_name="Иван Тест",
        params={"Цвет": "Синий"},
        description="Краткое описание товара",
    )

    monkeypatch.setattr(AvitoClient, "get_item", lambda self, item_id: mock_item)

    ret = main(["item", "999888"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "999888" in captured.out
    assert "Тестовый товар CLI" in captured.out
    assert "12,500 ₽" in captured.out
    assert "Иван Тест" in captured.out
    assert "Цвет: Синий" in captured.out
