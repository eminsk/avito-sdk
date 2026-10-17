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
    res = to_excel(items, out)

    assert res == out
    assert out.exists()
    assert out.stat().st_size > 0


def test_telegram_send_excel_xlsx_and_csv_fallback(monkeypatch, tmp_path):
    from unittest.mock import MagicMock
    import requests
    from avito_sdk.telegram import TelegramNotifier

    notifier = TelegramNotifier(bot_token="123:test_token", chat_id="999888")

    posted_files = []

    def mock_post(url, data=None, files=None, proxies=None, timeout=None):
        doc_tuple = files.get("document")
        filename, fileobj, mime = doc_tuple
        posted_files.append({"filename": filename, "mime": mime, "caption": data.get("caption")})
        m = MagicMock()
        m.status_code = 200
        m.json.return_value = {"ok": True}
        return m

    monkeypatch.setattr(requests, "post", mock_post)

    # 1. Normal XLSX upload
    xlsx_path = tmp_path / "test.xlsx"
    xlsx_path.write_bytes(b"dummy_xlsx")
    notifier.send_excel(xlsx_path, caption="XLSX Caption")
    assert len(posted_files) == 1
    assert posted_files[0]["filename"] == "test.xlsx"
    assert posted_files[0]["mime"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert posted_files[0]["caption"] == "XLSX Caption"

    # 2. Fallback: requested test2.xlsx does not exist, but test2.csv exists
    csv_path = tmp_path / "test2.csv"
    csv_path.write_text("id,title\n1,phone", encoding="utf-8")
    notifier.send_excel(tmp_path / "test2.xlsx", caption="CSV Fallback Caption")
    assert len(posted_files) == 2
    assert posted_files[1]["filename"] == "test2.csv"
    assert posted_files[1]["mime"] == "text/csv"
    assert posted_files[1]["caption"] == "CSV Fallback Caption"

    # 3. Direct CSV upload
    notifier.send_excel(csv_path, caption="Direct CSV")
    assert len(posted_files) == 3
    assert posted_files[2]["filename"] == "test2.csv"
    assert posted_files[2]["mime"] == "text/csv"

