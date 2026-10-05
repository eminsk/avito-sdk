"""
Synchronous high-level client for Avito (AvitoClient).
Provides intuitive methods for search, item enrichment, price tracking, and export.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Generator, Iterable, List, Optional, Union

from bs4 import BeautifulSoup

from avito_sdk.export import to_csv, to_dataframe, to_excel, to_json, to_jsonl
from avito_sdk.extractors import (
    extract_catalog_items,
    extract_description,
    extract_embedded_state,
    extract_params,
    extract_seller_id,
    extract_seller_name,
    extract_views,
    parse_raw_item,
)
from avito_sdk.http import SyncHttpTransport
from avito_sdk.models import Item, SearchFilter, SearchPage
from avito_sdk.tracker import PriceTracker
from avito_sdk.url import (
    build_item_api_url,
    build_item_web_url,
    build_page_url,
    build_search_url,
)

logger = logging.getLogger("avito_sdk")


class AvitoClient:
    """
    High-level synchronous Avito SDK client.

    Example:
        >>> from avito_sdk import AvitoClient
        >>> client = AvitoClient()
        >>> for item in client.search("ThinkPad", region="moskva", limit=10):
        ...     print(item.title, item.price, item.seller_name)
    """

    def __init__(
        self,
        proxy: Optional[str] = None,
        proxy_change_url: Optional[str] = None,
        timeout: int = 25,
        max_retries: int = 3,
        tracker_db: Optional[Union[str, Path]] = "avito_prices.db",
        enable_tracking: bool = True,
    ):
        self.transport = SyncHttpTransport(
            proxy=proxy,
            proxy_change_url=proxy_change_url,
            timeout=timeout,
            max_retries=max_retries,
        )
        self.tracker = PriceTracker(db_path=tracker_db) if (enable_tracking and tracker_db) else None

    def search(
        self,
        query: str = "",
        region: Optional[str] = "rossiya",
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        sort: str = "date",
        category: Optional[str] = None,
        with_delivery: bool = False,
        enrich_details: bool = False,
        max_workers: int = 1,
        limit: Optional[int] = None,
        max_pages: int = 5,
    ) -> Generator[Item, None, None]:
        """
        Search Avito for items matching specified criteria.
        Yields Item objects one by one.
        Note: When using max_workers > 1 or enrich_details=True, a mobile proxy
        (proxy + proxy_change_url) is strongly recommended to prevent IP bans.
        """
        search_filter = SearchFilter(
            query=query,
            region=region,
            min_price=min_price,
            max_price=max_price,
            sort=sort,
            category=category,
            with_delivery=with_delivery,
            page=1,
        )

        yielded_count = 0
        for page_num in range(1, max_pages + 1):
            search_filter.page = page_num
            url = build_search_url(search_filter)
            logger.debug(f"Fetching search page {page_num}: {url}")

            items = self.scrape_page_items(url)
            if not items:
                break

            if limit:
                remaining = limit - yielded_count
                items = items[:remaining]

            enriched_in_parallel = False
            if enrich_details and max_workers > 1 and len(items) > 1:
                from concurrent.futures import ThreadPoolExecutor
                with ThreadPoolExecutor(max_workers=max_workers) as pool:
                    list(pool.map(self.enrich_item, items))
                enriched_in_parallel = True

            for item in items:
                if self.tracker:
                    self.tracker.check_and_update(item)

                if enrich_details and not enriched_in_parallel:
                    self.enrich_item(item)

                yield item
                yielded_count += 1
                if limit and yielded_count >= limit:
                    return

    def scrape_url(
        self,
        url: str,
        max_pages: int = 1,
        enrich_details: bool = False,
        max_workers: int = 1,
    ) -> List[Item]:
        """Scrape items from an existing Avito search or catalog URL across multiple pages."""
        results: List[Item] = []
        for page in range(1, max_pages + 1):
            page_url = build_page_url(url, page)
            page_items = self.scrape_page_items(page_url)
            if not page_items:
                break

            enriched_in_parallel = False
            if enrich_details and max_workers > 1 and len(page_items) > 1:
                from concurrent.futures import ThreadPoolExecutor
                with ThreadPoolExecutor(max_workers=max_workers) as pool:
                    list(pool.map(self.enrich_item, page_items))
                enriched_in_parallel = True

            for item in page_items:
                if self.tracker:
                    self.tracker.check_and_update(item)
                if enrich_details and not enriched_in_parallel:
                    self.enrich_item(item)
                results.append(item)

        return results

    def scrape_page_items(self, url: str) -> List[Item]:
        """Fetch and extract items from a single page URL."""
        html_text = self.transport.fetch_html(url)
        soup = BeautifulSoup(html_text, "html.parser")
        embedded = extract_embedded_state(soup)

        if embedded:
            items = extract_catalog_items(embedded)
            if items:
                return items

        # Fallback to HTML elements
        items: List[Item] = []
        for el in soup.select('[data-marker="item"]'):
            item_id_str = el.get("data-item-id") or el.get("id")
            if not item_id_str:
                continue
            digits = "".join(filter(str.isdigit, str(item_id_str)))
            if not digits:
                continue
            item_id = int(digits)

            title_el = el.select_one('[data-marker="item-title"]') or el.select_one("h3")
            title = title_el.get_text(strip=True) if title_el else ""

            price_el = el.select_one('[data-marker="item-price"]') or el.select_one('[itemprop="price"]')
            price = 0
            if price_el:
                price_digits = "".join(filter(str.isdigit, price_el.get_text()))
                price = int(price_digits) if price_digits else 0

            url_el = el.select_one('a[data-marker="item-title"]') or el.select_one('a[itemprop="url"]')
            link = url_el.get("href") if url_el else ""
            if link and link.startswith("/"):
                link = f"https://www.avito.ru{link}"

            seller_name = extract_seller_name({}, html_text=str(el))

            items.append(
                Item(
                    id=item_id,
                    title=title,
                    price=price,
                    url=link,
                    seller_name=seller_name,
                )
            )

        return items

    def get_item(self, item_id: int) -> Item:
        """
        Fetch full details for an item by ID, including:
        - Full description (Issue #305)
        - Parameters and specs (PR #337)
        - Seller name and ID (PR #334)
        - View counts (total and today)
        """
        item = Item(id=item_id, url=build_item_web_url(item_id))
        self.enrich_item(item)
        return item

    def enrich_item(self, item: Item) -> Item:
        """Enrich an existing Item instance with deep card parameters and views."""
        try:
            payload = self.transport.fetch_item_card(item.id)
            if payload:
                # Parameters (PR #337)
                params = extract_params(payload)
                if params:
                    item.params = params

                # Seller info (PR #334)
                if not item.seller_name:
                    item.seller_name = extract_seller_name(payload)
                if not item.seller_id:
                    item.seller_id = extract_seller_id(payload)

                # Description and views
                desc = extract_description(payload)
                if desc:
                    item.description = desc

                total_views, today_views = extract_views(payload)
                if total_views is not None:
                    item.total_views = total_views
                if today_views is not None:
                    item.today_views = today_views
        except Exception as err:
            logger.debug(f"API card fetch failed for item {item.id}, attempting HTML fallback: {err}")
            try:
                web_url = item.url or build_item_web_url(item.id)
                html_text = self.transport.fetch_html(web_url)
                if not item.seller_name:
                    item.seller_name = extract_seller_name({}, html_text=html_text)
                if not item.description:
                    item.description = extract_description({}, html_text=html_text)
                total_views, today_views = extract_views({}, html_text=html_text)
                if total_views is not None:
                    item.total_views = total_views
                if today_views is not None:
                    item.today_views = today_views
            except Exception as html_err:
                logger.warning(f"Could not enrich item {item.id}: {html_err}")

        return item

    # Export helper shortcuts
    def export_excel(self, items: List[Item], filepath: Union[str, Path]) -> None:
        to_excel(items, filepath)

    def export_json(self, items: List[Item], filepath: Union[str, Path], indent: int = 2) -> None:
        to_json(items, filepath, indent=indent)

    def export_csv(self, items: List[Item], filepath: Union[str, Path]) -> None:
        to_csv(items, filepath)

    def export_dataframe(self, items: List[Item]) -> Any:
        return to_dataframe(items)

    def close(self) -> None:
        self.transport.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
