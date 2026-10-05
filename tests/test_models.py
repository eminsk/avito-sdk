"""Tests for avito_sdk data models."""

from avito_sdk.models import Item, PriceRecord, SearchFilter


def test_item_creation_and_properties():
    item = Item(
        id=123456,
        title="Ноутбук Apple MacBook Air M2",
        price=85000,
        old_price=95000,
        seller_name="Иван Продавец",
        seller_id="user_12345",
        url="https://www.avito.ru/item_123456",
        params={"Оперативная память": "16 ГБ", "SSD": "512 ГБ"},
    )

    assert item.id == 123456
    assert item.has_price_changed is True
    assert item.price_drop == 10000

    d = item.to_dict()
    assert d["id"] == 123456
    assert d["price_drop"] == 10000
    assert d["has_price_changed"] is True
    assert d["params"]["SSD"] == "512 ГБ"

    json_str = item.to_json()
    assert "Apple MacBook" in json_str
    assert "10000" in json_str


def test_item_no_price_change():
    item = Item(id=999, price=5000)
    assert item.has_price_changed is False
    assert item.price_drop is None


def test_search_filter():
    sf = SearchFilter(query="iPhone 15", region="moskva", min_price=50000, max_price=80000)
    assert sf.query == "iPhone 15"
    assert sf.region == "moskva"
    assert sf.page == 1
