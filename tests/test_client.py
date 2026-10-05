"""Tests for AvitoClient and AsyncAvitoClient with mocked network transport."""

import pytest
from avito_sdk.client import AvitoClient
from avito_sdk.async_client import AsyncAvitoClient
from avito_sdk.models import Item


MOCK_CARD_PAYLOAD = {
    "success": {
        "mobile": {
            "seller": {"name": "ООО Спецтехника"},
            "description": "Полное описание из мобильного API",
            "stats": {"views": {"total": 450, "today": 15}},
            "params": [
                {"title": "Мощность", "description": "150 л.с."},
                {"title": "Год выпуска", "description": "2023"},
            ],
        }
    }
}

MOCK_HTML_PAGE = """
<html>
<body>
    <script type="mime/invalid" data-mfe-state="true">
    {"result": {"catalog": {"items": [
        {"id": 555666, "title": "Телефон Google Pixel 8", "price": 45000, "sellerName": "PixelShop"}
    ]}}}
    </script>
</body>
</html>
"""


def test_sync_client_enrich_item(monkeypatch, tmp_path):
    client = AvitoClient(tracker_db=tmp_path / "test.db")

    # Mock fetch_item_card
    monkeypatch.setattr(
        client.transport,
        "fetch_item_card",
        lambda item_id: MOCK_CARD_PAYLOAD,
    )

    item = Item(id=777)
    client.enrich_item(item)

    assert item.seller_name == "ООО Спецтехника"
    assert item.description == "Полное описание из мобильного API"
    assert item.total_views == 450
    assert item.today_views == 15
    assert item.params["Мощность"] == "150 л.с."
    assert item.params["Год выпуска"] == "2023"


def test_sync_client_scrape_page_items(monkeypatch, tmp_path):
    client = AvitoClient(tracker_db=tmp_path / "test.db")

    monkeypatch.setattr(
        client.transport,
        "fetch_html",
        lambda url: MOCK_HTML_PAGE,
    )

    items = client.scrape_page_items("https://www.avito.ru/moskva?q=pixel")
    assert len(items) == 1
    assert items[0].id == 555666
    assert items[0].title == "Телефон Google Pixel 8"
    assert items[0].price == 45000
    assert items[0].seller_name == "PixelShop"


def test_async_client_enrich_item(monkeypatch, tmp_path):
    import asyncio

    async def _test():
        client = AsyncAvitoClient(tracker_db=tmp_path / "async_test.db")

        async def mock_card(item_id):
            return MOCK_CARD_PAYLOAD

        monkeypatch.setattr(client.transport, "fetch_item_card", mock_card)

        item = Item(id=888)
        await client.enrich_item(item)

        assert item.seller_name == "ООО Спецтехника"
        assert item.params["Год выпуска"] == "2023"
        await client.close()

    asyncio.run(_test())


def test_mobile_proxy_and_multithreading(monkeypatch, tmp_path):
    client = AvitoClient(
        proxy="user:pass@127.0.0.1:8080",
        proxy_change_url="https://changeip.example.com/rotate",
        tracker_db=tmp_path / "proxy_test.db",
    )
    assert client.transport.proxy == "http://user:pass@127.0.0.1:8080"
    assert client.transport.proxy_change_url == "https://changeip.example.com/rotate"

    monkeypatch.setattr(client.transport, "fetch_html", lambda url: MOCK_HTML_PAGE)
    monkeypatch.setattr(client.transport, "fetch_item_card", lambda item_id: MOCK_CARD_PAYLOAD)

    items = list(client.search("pixel", enrich_details=True, max_workers=2, limit=1, max_pages=1))
    assert len(items) == 1
    assert items[0].params["Мощность"] == "150 л.с."
    client.close()


def test_parse_proxy_config_formats():
    from avito_sdk.cookies import parse_proxy_config

    p1 = parse_proxy_config("user1:pass1@10.0.0.1:8000")
    assert p1["server"] == "http://10.0.0.1:8000"
    assert p1["username"] == "user1"
    assert p1["password"] == "pass1"

    p2 = parse_proxy_config("10.0.0.1:8000@user2:pass2")
    assert p2["server"] == "http://10.0.0.1:8000"
    assert p2["username"] == "user2"
    assert p2["password"] == "pass2"

    p3 = parse_proxy_config("10.0.0.1:8000:user3:pass3")
    assert p3["server"] == "http://10.0.0.1:8000"
    assert p3["username"] == "user3"
    assert p3["password"] == "pass3"


def test_telegram_notifier_formatting_and_progress():
    from avito_sdk.telegram import TelegramNotifier, render_progress_bar

    bar = render_progress_bar(5, 10, width=10)
    assert "50%" in bar
    assert "(5/10)" in bar
    assert "█████░░░░░" in bar

    notifier = TelegramNotifier(bot_token="123:ABC", chat_id="999")
    item = Item(
        id=101,
        title="Складское помещение 250 м²",
        price=45000,
        old_price=50000,
        url="https://www.avito.ru/moskva/101",
        seller_name="АрендаПлюс",
        address="Москва",
        params={"Площадь": "250 м²", "Высота потолков": "6 м"},
    )
    msg = notifier.format_item(item)
    assert "50 000" in msg
    assert "45 000" in msg
    assert "АрендаПлюс" in msg
    assert "Площадь" in msg


def test_search_with_excel_and_telegram_progress(monkeypatch, tmp_path):
    excel_file = tmp_path / "results.xlsx"
    client = AvitoClient(
        proxy="user:pass@127.0.0.1:8080",
        proxy_change_url="https://changeip.example.com/rotate",
        tg_token="123:FAKE_TOKEN",
        tg_chat_id="999888",
        tracker_db=tmp_path / "tg_test.db",
    )

    monkeypatch.setattr(client.transport, "fetch_html", lambda url: MOCK_HTML_PAGE)
    monkeypatch.setattr(client.transport, "fetch_item_card", lambda item_id: MOCK_CARD_PAYLOAD)

    sent_items = []
    sent_excels = []
    monkeypatch.setattr(client.notifier, "notify", lambda item=None, **kw: sent_items.append(item))
    monkeypatch.setattr(client.notifier, "start_progress", lambda *a, **kw: {"999888": 42})
    monkeypatch.setattr(client.notifier, "update_progress", lambda *a, **kw: None)
    monkeypatch.setattr(
        client.notifier,
        "finish_progress",
        lambda *a, **kw: sent_excels.append(kw.get("excel_path")),
    )

    items = list(
        client.search(
            "pixel",
            enrich_details=True,
            max_workers=2,
            limit=1,
            max_pages=1,
            notify_telegram=True,
            telegram_progress=True,
            excel_path=excel_file,
        )
    )
    assert len(items) == 1
    assert len(sent_items) == 1
    assert excel_file.exists()
    assert len(sent_excels) == 1
    client.close()


def test_telegram_bot_commands(monkeypatch):
    from avito_sdk.telegram import AvitoTelegramBot, TelegramNotifier

    replies = []
    monkeypatch.setattr(TelegramNotifier, "send_message", lambda self, text, **kw: replies.append(text) or {})

    bot = AvitoTelegramBot(bot_token="123:BOT")

    bot.handle_update({"message": {"chat": {"id": 777}, "text": "/proxy user:pass@1.2.3.4:8080 https://rotate.url"}})
    assert bot.proxy == "user:pass@1.2.3.4:8080"
    assert bot.proxy_change_url == "https://rotate.url"

    bot.handle_update({"message": {"chat": {"id": 777}, "text": "/workers 5"}})
    assert bot.workers == 5

    bot.handle_update({"message": {"chat": {"id": 777}, "text": "/playwright"}})
    assert bot.use_playwright_cookies is True

    bot.handle_update({"message": {"chat": {"id": 777}, "text": "/limit 25"}})
    assert bot.limit == 25
    assert len(replies) == 4

