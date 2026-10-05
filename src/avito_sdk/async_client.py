"""
Asynchronous high-level client for Avito (AsyncAvitoClient).
Designed for modern asyncio backends (FastAPI, aiohttp, Aiogram, Celery).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import AsyncGenerator, List, Optional, Union

from bs4 import BeautifulSoup

from avito_sdk.extractors import (
    extract_catalog_items,
    extract_description,
    extract_embedded_state,
    extract_params,
    extract_seller_id,
    extract_seller_name,
    extract_views,
)
from avito_sdk.http import AsyncHttpTransport
from avito_sdk.models import Item, SearchFilter
from avito_sdk.tracker import PriceTracker
from avito_sdk.url import (
    build_item_web_url,
    build_page_url,
    build_search_url,
)

logger = logging.getLogger("avito_sdk")


class AsyncAvitoClient:
    """
    High-level asynchronous Avito SDK client.

    Example:
        >>> async with AsyncAvitoClient() as client:
        ...     async for item in client.search("rtx 4070", limit=10):
        ...         print(item.title, item.price)
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
        self.transport = AsyncHttpTransport(
            proxy=proxy,
            proxy_change_url=proxy_change_url,
            timeout=timeout,
            max_retries=max_retries,
        )
        self.tracker = PriceTracker(db_path=tracker_db) if (enable_tracking and tracker_db) else None

    async def search(
        self,
        query: str = "",
        region: Optional[str] = "rossiya",
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        sort: str = "date",
        category: Optional[str] = None,
        with_delivery: bool = False,
        enrich_details: bool = False,
        concurrency: int = 1,
        limit: Optional[int] = None,
        max_pages: int = 5,
    ) -> AsyncGenerator[Item, None]:
        """
        Asynchronously search Avito and stream items.
        Note: When using concurrency > 1 or enrich_details=True, a mobile proxy
        (proxy + proxy_change_url) is strongly recommended to prevent IP bans.
        """
        import asyncio
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

            items = await self.scrape_page_items(url)
            if not items:
                break

            if limit:
                remaining = limit - yielded_count
                items = items[:remaining]

            enriched_in_parallel = False
            if enrich_details and concurrency > 1 and len(items) > 1:
                sem = asyncio.Semaphore(concurrency)

                async def _enrich(it: Item):
                    async with sem:
                        await self.enrich_item(it)

                await asyncio.gather(*(_enrich(it) for it in items))
                enriched_in_parallel = True

            for item in items:
                if self.tracker:
                    self.tracker.check_and_update(item)

                if enrich_details and not enriched_in_parallel:
                    await self.enrich_item(item)

                yield item
                yielded_count += 1
                if limit and yielded_count >= limit:
                    return

    async def scrape_page_items(self, url: str) -> List[Item]:
        """Fetch and extract items from a single page URL asynchronously."""
        html_text = await self.transport.fetch_html(url)
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

    async def get_item(self, item_id: int) -> Item:
        """Fetch full details for an item by ID asynchronously."""
        item = Item(id=item_id, url=build_item_web_url(item_id))
        await self.enrich_item(item)
        return item

    async def enrich_item(self, item: Item) -> Item:
        """Enrich an item with card parameters, seller, description, and views asynchronously."""
        try:
            payload = await self.transport.fetch_item_card(item.id)
            if payload:
                params = extract_params(payload)
                if params:
                    item.params = params

                if not item.seller_name:
                    item.seller_name = extract_seller_name(payload)
                if not item.seller_id:
                    item.seller_id = extract_seller_id(payload)

                desc = extract_description(payload)
                if desc:
                    item.description = desc

                total_views, today_views = extract_views(payload)
                if total_views is not None:
                    item.total_views = total_views
                if today_views is not None:
                    item.today_views = today_views
        except Exception as err:
            logger.debug(f"Async API card fetch failed for item {item.id}: {err}")
            try:
                web_url = item.url or build_item_web_url(item.id)
                html_text = await self.transport.fetch_html(web_url)
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
                logger.warning(f"Could not enrich item {item.id} asynchronously: {html_err}")

        return item

    async def close(self) -> None:
        await self.transport.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
