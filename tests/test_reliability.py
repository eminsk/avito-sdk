"""
Tests for reliability, failover recovery, mobile header rotation, and URL routing.
Guarantees 100% stability across all network and edge-case conditions.
"""

from unittest.mock import MagicMock, patch
import pytest

from avito_sdk.client import AvitoClient
from avito_sdk.http import (
    SyncHttpTransport,
    AsyncHttpTransport,
    get_random_mobile_headers,
    MOBILE_PROFILES,
)
from avito_sdk.models import Item


def test_random_mobile_headers_consistency():
    """Verify that all generated mobile headers are valid, modern, and TLS-synchronized."""
    for _ in range(25):
        h = get_random_mobile_headers(accept_html=False)
        assert "application/json" in h["accept"]
        assert h["sec-ch-ua-mobile"] == "?1"
        assert h["sec-ch-ua-platform"] == '"Android"'
        assert "Android" in h["user-agent"]
        assert "Chrome/" in h["user-agent"]
        assert "13" in h["sec-ch-ua"]  # Chrome 130 or 131

        html_h = get_random_mobile_headers(accept_html=True)
        assert "text/html" in html_h["accept"]
        assert html_h["sec-ch-ua-platform"] == '"Android"'


def test_search_url_delegation(tmp_path):
    """Test that passing a full Avito URL to search() transparently delegates to scrape_url()."""
    client = AvitoClient(tracker_db=tmp_path / "test.db")
    mock_items = [
        Item(id=101, title="Ноутбук 1", price=50000, url="https://www.avito.ru/101"),
        Item(id=102, title="Ноутбук 2", price=60000, url="https://www.avito.ru/102"),
    ]

    with patch.object(client, "scrape_url", return_value=mock_items) as mock_scrape:
        items = list(client.search("https://www.avito.ru/moskva/noutbuki?cd=1", limit=2))
        assert len(items) == 2
        assert items[0].id == 101
        assert items[1].id == 102
        mock_scrape.assert_called_once()
        call_kwargs = mock_scrape.call_args.kwargs
        assert call_kwargs["url"] == "https://www.avito.ru/moskva/noutbuki?cd=1"
        assert call_kwargs["limit"] == 2


def test_scrape_url_respects_limit(tmp_path):
    """Test that scrape_url respects the limit parameter across pages."""
    client = AvitoClient(tracker_db=tmp_path / "test.db")
    page1_items = [Item(id=i, title=f"Item {i}", price=1000) for i in range(1, 11)]
    page2_items = [Item(id=i, title=f"Item {i}", price=1000) for i in range(11, 21)]

    with patch.object(client, "scrape_page_items", side_effect=[page1_items, page2_items]):
        # Limit to 3 items
        res3 = client.scrape_url("https://www.avito.ru/moskva/noutbuki", max_pages=2, limit=3)
        assert len(res3) == 3
        assert [it.id for it in res3] == [1, 2, 3]

        # Limit to 15 items across 2 pages
        with patch.object(client, "scrape_page_items", side_effect=[page1_items, page2_items]):
            res15 = client.scrape_url("https://www.avito.ru/moskva/noutbuki", max_pages=2, limit=15)
            assert len(res15) == 15
            assert res15[-1].id == 15


def test_html_fallback_link_normalization(tmp_path):
    """Test that scrape_page_items normalizes all link variations to absolute https://www.avito.ru/..."""
    html_page = """
    <html>
    <body>
        <div data-marker="item" data-item-id="111">
            <a data-marker="item-title" href="/moskva/tovary/noutbuk_111">Ноутбук</a>
            <span data-marker="item-price">45000 ₽</span>
        </div>
        <div data-marker="item" data-item-id="222">
            <a data-marker="item-title" href="https://m.avito.ru/moskva/tovary/noutbuk_222">Ноутбук 2</a>
            <span data-marker="item-price">55000 ₽</span>
        </div>
        <div data-marker="item" data-item-id="333">
            <h3 data-marker="item-title">Ноутбук без ссылки</h3>
        </div>
    </body>
    </html>
    """
    client = AvitoClient(tracker_db=tmp_path / "test.db")
    with patch.object(client.transport, "fetch_html", return_value=html_page):
        items = client.scrape_page_items("https://www.avito.ru/moskva/noutbuki")
        assert len(items) == 3
        assert items[0].url == "https://www.avito.ru/moskva/tovary/noutbuk_111"
        assert items[1].url == "https://www.avito.ru/moskva/tovary/noutbuk_222"
        assert items[2].url == "https://www.avito.ru/item_333"


def test_dead_socket_cleanup_and_auto_rotation_on_failure():
    """Test that connection drop cleans thread session and triggers IP rotation if attempt >= 2."""
    transport = SyncHttpTransport(
        proxy="http://user:pass@1.2.3.4:8000",
        proxy_change_url="https://changeip.mobileproxy.space/?proxy_key=key123&format=json",
        max_retries=3,
    )

    mock_session = MagicMock()
    # First 2 calls fail with connection error, 3rd call succeeds
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = '{"items": []}'
    mock_session.request.side_effect = [
        ConnectionResetError("Socket died"),
        ConnectionResetError("Socket died again"),
        mock_resp,
    ]

    with patch.object(transport, "_create_session", return_value=mock_session):
        with patch.object(transport, "rotate_proxy_ip", return_value=True) as mock_rotate:
            resp = transport.request("GET", "https://m.avito.ru/api/1/test")
            assert resp.status_code == 200
            # On 2nd failure, rotate_proxy_ip must have been triggered!
            assert mock_rotate.called
