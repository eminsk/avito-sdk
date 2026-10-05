"""Tests for URL builder and parser functions."""

from avito_sdk.models import SearchFilter
from avito_sdk.url import (
    build_item_api_url,
    build_item_web_url,
    build_page_url,
    build_search_url,
    normalize_region,
)


def test_normalize_region():
    assert normalize_region("Москва") == "moskva"
    assert normalize_region("Санкт-Петербург") == "sankt-peterburg"
    assert normalize_region(None) == "rossiya"
    assert normalize_region("kazan") == "kazan"


def test_build_search_url():
    sf = SearchFilter(
        query="rtx 4090",
        region="Москва",
        min_price=100000,
        max_price=200000,
        sort="price_asc",
        with_delivery=True,
    )
    url = build_search_url(sf)
    assert "https://www.avito.ru/moskva" in url
    assert "q=rtx+4090" in url
    assert "pmin=100000" in url
    assert "pmax=200000" in url
    assert "s=1" in url
    assert "d=1" in url


def test_build_page_url():
    base = "https://www.avito.ru/moskva?q=macbook"
    page2 = build_page_url(base, 2)
    assert "p=2" in page2

    api_base = "https://m.avito.ru/api/1/catalog?q=macbook"
    api_page3 = build_page_url(api_base, 3)
    assert "page=3" in api_page3


def test_item_urls():
    assert build_item_api_url(12345) == "https://m.avito.ru/api/1/card/items/12345"
    assert build_item_web_url(12345) == "https://www.avito.ru/item_12345"
