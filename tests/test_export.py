"""Tests for export utilities (Excel, JSON, JSONL, CSV)."""

import json
from pathlib import Path
from avito_sdk.export import to_csv, to_excel, to_json, to_jsonl
from avito_sdk.models import Item


def _sample_items():
    return [
        Item(
            id=101,
            title="Тестовый товар 1",
            price=15000,
            old_price=18000,
            seller_name="Иван",
            seller_id="ivan_shop",
            url="https://www.avito.ru/item_101",
            params={"Память": "8 ГБ", "Цвет": "Черный"},
            description="Отличное состояние",
        ),
        Item(
            id=102,
            title="Тестовый товар 2",
            price=30000,
            seller_name="Ольга",
            seller_id="olga_99",
            url="https://www.avito.ru/item_102",
        ),
    ]


def test_to_json(tmp_path):
    out = tmp_path / "items.json"
    items = _sample_items()
    to_json(items, out)

    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert len(data) == 2
    assert data[0]["id"] == 101
    assert data[0]["price_drop"] == 3000
    assert data[0]["params"]["Память"] == "8 ГБ"


def test_to_jsonl(tmp_path):
    out = tmp_path / "items.jsonl"
    items = _sample_items()
    to_jsonl(items, out)

    assert out.exists()
    lines = out.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 2
    row1 = json.loads(lines[0])
    assert row1["id"] == 101


def test_to_csv(tmp_path):
    out = tmp_path / "items.csv"
    items = _sample_items()
    to_csv(items, out)

    assert out.exists()
    content = out.read_text(encoding="utf-8-sig")
    assert "Тестовый товар 1" in content
    assert "Иван" in content
    assert "ivan_shop" in content
    assert "Память: 8 ГБ" in content


def test_to_excel(tmp_path):
    out = tmp_path / "items.xlsx"
    items = _sample_items()
    to_excel(items, out)

    assert out.exists()
    assert out.stat().st_size > 0
