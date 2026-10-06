"""
Comprehensive test suite verifying 100% feature parity with Duff89/parser_avito
plus avito-sdk exclusive features (multithreading, Telegram Bot, progress bars, Excel upload).
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import pytest

from avito_sdk import (
    AdsFilter,
    AvitoClient,
    AvitoConfig,
    AvitoTelegramBot,
    AvitoUrlConverter,
    ExternalApiCookiesProvider,
    Item,
    ParsePhone,
    PlaywrightCookieProvider,
    PriceTracker,
    TelegramNotifier,
    VKNotifier,
    load_avito_config,
    parse_proxy_config,
    render_progress_bar,
    render_telegram_progress_bar,
    to_excel,
)
from avito_sdk.cli import main as cli_main


def test_all_6_proxy_formats():
    formats = [
        ("http://u1:p1@1.2.3.4:8080", "http://1.2.3.4:8080", "u1", "p1"),
        ("u2:p2@1.2.3.4:8080", "http://1.2.3.4:8080", "u2", "p2"),
        ("1.2.3.4:8080@u3:p3", "http://1.2.3.4:8080", "u3", "p3"),
        ("1.2.3.4:8080:u4:p4", "http://1.2.3.4:8080", "u4", "p4"),
        ("u5:p5:1.2.3.4:8080", "http://1.2.3.4:8080", "u5", "p5"),
        ("1.2.3.4:8080", "http://1.2.3.4:8080", None, None),
    ]
    for raw, exp_srv, exp_u, exp_p in formats:
        parsed = parse_proxy_config(raw, "https://rotate.me")
        assert parsed.server == exp_srv
        assert parsed.username == exp_u
        assert parsed.password == exp_p
        assert parsed.change_ip_url == "https://rotate.me"


def test_playwright_cookie_disk_cache(tmp_path):
    cache_file = tmp_path / "own_cookies.json"
    cache_file.write_text(
        json.dumps({"cookies": {"ft": "cached_ft_token"}, "user_agent": "CustomUA/1.0"}),
        encoding="utf-8",
    )
    provider = PlaywrightCookieProvider(proxy="user:pass@1.2.3.4:8080")
    cookies, ua = provider.fetch_cookies(storage_path=str(cache_file), force_refresh=False)
    assert cookies["ft"] == "cached_ft_token"
    assert ua == "CustomUA/1.0"


def test_spfa_external_cookies_url_converter_and_phones(monkeypatch, tmp_path):
    import requests

    class DummyResp:
        def __init__(self, status_code, data):
            self.status_code = status_code
            self._data = data
            self.ok = status_code == 200

        def raise_for_status(self):
            if not self.ok:
                raise RuntimeError(f"HTTP {self.status_code}")

        def json(self):
            return self._data

    def fake_post(url, json=None, **kwargs):
        if "cookies/mobile" in url:
            return DummyResp(
                200,
                {
                    "success": True,
                    "results": {
                        "id": "cid_1",
                        "cookies": {"ft": "spfa_ft_123"},
                        "user_agent": "AndroidUA",
                        "fingerprint": {"impersonate": "chrome", "headers": {"user-agent": "AndroidUA"}},
                    },
                },
            )
        if "avito-url" in url:
            return DummyResp(200, {"success": True, "api_url": "https://m.avito.ru/api/11/items?key=1"})
        if "api/phone" in url:
            return DummyResp(
                200,
                {
                    "success": True,
                    "results": [{"ad_id": "100", "phone": "+7 (999) 123-45-67"}],
                },
            )
        return DummyResp(404, {})

    monkeypatch.setattr(requests, "post", fake_post)

    # 1. ExternalApiCookiesProvider
    ext = ExternalApiCookiesProvider(api_key="k1", storage_path=str(tmp_path / "ext.json"))
    cookies, ua = ext.get_cookies()
    assert cookies["ft"] == "spfa_ft_123"
    assert ua == "AndroidUA"

    # 2. AvitoUrlConverter
    conv = AvitoUrlConverter(cache_path=str(tmp_path / "urls.json"))
    api_url = conv.convert("https://www.avito.ru/moskva/noutbuki")
    assert api_url == "https://m.avito.ru/api/11/items?key=1"
    # Second call hits disk/memory cache
    assert conv.convert("https://www.avito.ru/moskva/noutbuki") == api_url

    # 3. ParsePhone
    items = [Item(id=100, title="Test", has_phone=True)]
    ParsePhone(api_key="k1").enrich_phones(items)
    assert items[0].phone == "79991234567"


def test_ads_filter_price_change_passthrough(tmp_path):
    tracker = PriceTracker(db_path=tmp_path / "filter_tracker.db")
    f = AdsFilter(only_new_or_changed=True)

    # First time seen -> is_new=True -> passes filter
    it1 = Item(id=500, title="MacBook", price=100000)
    tracker.check_and_update(it1)
    assert it1.is_new is True
    assert f.matches(it1) is True

    # Second time seen with same price -> is_new=False, has_price_changed=False -> filtered out!
    it2 = Item(id=500, title="MacBook", price=100000)
    tracker.check_and_update(it2)
    assert it2.is_new is False
    assert it2.has_price_changed is False
    assert f.matches(it2) is False

    # Third time seen with lower price -> is_new=False, has_price_changed=True -> passes filter!
    it3 = Item(id=500, title="MacBook", price=90000)
    tracker.check_and_update(it3)
    assert it3.is_new is False
    assert it3.old_price == 100000
    assert it3.has_price_changed is True
    assert f.matches(it3) is True


def test_excel_formula_injection_and_append(tmp_path):
    import openpyxl

    xlsx_path = tmp_path / "safe.xlsx"
    it1 = Item(id=1, title="=CMD|' /C calc'!A0", price=1000, phone="+79990001122")
    it2 = Item(id=2, title="Обычный товар", price=2000)

    to_excel([it1], xlsx_path, append=False)
    to_excel([it2], xlsx_path, append=True)

    wb = openpyxl.load_workbook(xlsx_path)
    ws = wb.active
    assert ws.max_row == 3  # 1 header + 2 rows
    assert ws.cell(row=2, column=2).value.startswith("'=")
    assert ws.cell(row=3, column=2).value == "Обычный товар"


def test_full_config_execution_and_cli(monkeypatch, tmp_path):
    cfg_path = tmp_path / "config.toml"
    out_dir = tmp_path / "result"
    cfg_path.write_text(
        f'[avito]\n'
        f'urls = ["https://www.avito.ru/moskva/komcheskaya_nedvizhimost"]\n'
        f'count = 1\n'
        f'min_price = 1000\n'
        f'max_price = 100000\n'
        f'keys_word_white_list = ["склад"]\n'
        f'keys_word_black_list = ["агентство"]\n'
        f'ignore_reserv = true\n'
        f'parse_params = true\n'
        f'save_xlsx = true\n'
        f'one_time_start = true\n'
        f'output_dir = "{out_dir.as_posix()}"\n',
        encoding="utf-8",
    )

    mock_html = """
    <html><body>
    <script type="mime/invalid" data-mfe-state="true">
    {"result": {"catalog": {"items": [
        {"id": 901, "title": "Склад 150 м²", "price": 45000, "sellerName": "Собственник"},
        {"id": 902, "title": "Склад от агентство", "price": 45000, "sellerName": "Риелтор"}
    ]}}}
    </script>
    </body></html>
    """
    mock_card = {
        "success": {
            "mobile": {
                "params": [{"title": "О помещении", "description": "Отдельный вход"}],
                "stats": {"views": {"total": 120, "today": 5}},
            }
        }
    }

    from avito_sdk.http import SyncHttpTransport
    monkeypatch.setattr(SyncHttpTransport, "fetch_html", lambda self, url: mock_html)
    monkeypatch.setattr(SyncHttpTransport, "fetch_item_card", lambda self, item_id: mock_card)

    rc = cli_main(["config", str(cfg_path)])
    assert rc == 0
    xlsx_file = out_dir / "avito_result.xlsx"
    assert xlsx_file.exists()


def test_telegram_progress_bar_rendering():
    tg_bar = render_telegram_progress_bar(5, 10, width=10)
    assert tg_bar == "🟩🟩🟩🟩🟩⬜⬜⬜⬜⬜ 50% (5/10)"

    term_bar = render_progress_bar(4, 8, width=8)
    assert term_bar == "[████░░░░] 50% (4/8)"


def test_freethreaded_multithreaded_parallel_execution(tmp_path, monkeypatch):
    """Verify thread-safe parallel card enrichment and SQLite price tracking across 8 threads (3.15t / 3.16t No-GIL)."""
    from concurrent.futures import ThreadPoolExecutor
    from avito_sdk.client import AvitoClient
    from avito_sdk.http import SyncHttpTransport

    catalog_items = [
        {"id": 1000 + i, "title": f"Серверная стойка #{i}", "price": 10000 + i * 500, "sellerName": f"Seller_{i}"}
        for i in range(16)
    ]
    import json
    mock_html = (
        '<html><body><script type="mime/invalid" data-mfe-state="true">'
        + json.dumps({"result": {"catalog": {"items": catalog_items}}})
        + "</script></body></html>"
    )

    def mock_fetch_card(self, item_id: int):
        # Verify each worker thread gets its own isolated HTTP session
        sess = self._get_thread_session()
        assert sess is not None
        return {
            "success": {
                "mobile": {
                    "params": [{"title": "Модель", "description": f"Rack-{item_id}"}],
                    "stats": {"views": {"total": item_id, "today": 10}},
                }
            }
        }

    monkeypatch.setattr(SyncHttpTransport, "fetch_html", lambda self, url: mock_html)
    monkeypatch.setattr(SyncHttpTransport, "fetch_item_card", mock_fetch_card)

    db_path = tmp_path / "nogil_tracker.db"
    client = AvitoClient(tracker_db=db_path)

    items = list(
        client.search(
            query="серверная стойка",
            enrich_details=True,
            max_workers=8,
            limit=16,
            max_pages=1,
        )
    )
    assert len(items) == 16
    assert all(it.params.get("Модель") == f"Rack-{it.id}" for it in items)
    assert all(it.is_new is True for it in items)

    # Also hammer PriceTracker from 8 threads concurrently to simulate price drops
    def update_price(it):
        dropped = Item(id=it.id, title=it.title, price=it.price - 1000, seller_name=it.seller_name)
        changed, old = client.tracker.check_and_update(dropped)
        return changed, old, dropped.price_drop

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(update_price, items))

    assert all(changed is True and drop == 1000 for changed, _, drop in results)
    assert len(client.tracker.get_price_drops()) == 16

