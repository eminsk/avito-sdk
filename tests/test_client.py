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


@pytest.mark.asyncio
async def test_async_client_enrich_item(monkeypatch, tmp_path):
    client = AsyncAvitoClient(tracker_db=tmp_path / "async_test.db")

    async def mock_card(item_id):
        return MOCK_CARD_PAYLOAD

    monkeypatch.setattr(client.transport, "fetch_item_card", mock_card)

    item = Item(id=888)
    await client.enrich_item(item)

    assert item.seller_name == "ООО Спецтехника"
    assert item.params["Год выпуска"] == "2023"
    await client.close()
