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
from avito_sdk.telegram import TelegramNotifier
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
        cookies: Optional[dict] = None,
        use_playwright_cookies: bool = False,
        timeout: int = 25,
        max_retries: int = 3,
        tracker_db: Optional[Union[str, Path]] = "avito_prices.db",
        enable_tracking: bool = True,
        tg_token: Optional[str] = None,
        tg_chat_id: Optional[Union[str, int, List[Union[str, int]]]] = None,
        telegram_notifier: Optional[TelegramNotifier] = None,
        vk_token: Optional[str] = None,
        vk_user_id: Optional[Union[str, int, List[Union[str, int]]]] = None,
    ):
        from avito_sdk.vk import VKNotifier

        self.transport = SyncHttpTransport(
            proxy=proxy,
            proxy_change_url=proxy_change_url,
            cookies=cookies,
            use_playwright_cookies=use_playwright_cookies,
            timeout=timeout,
            max_retries=max_retries,
        )
        self.tracker = PriceTracker(db_path=tracker_db) if (enable_tracking and tracker_db) else None
        if telegram_notifier is not None:
            self.notifier: Optional[TelegramNotifier] = telegram_notifier
        elif tg_token and tg_chat_id:
            self.notifier = TelegramNotifier(bot_token=tg_token, chat_id=tg_chat_id)
        else:
            self.notifier = None

        self.vk_notifier: Optional[VKNotifier] = (
            VKNotifier(vk_token=vk_token, user_id=vk_user_id) if (vk_token and vk_user_id) else None
        )

    @classmethod
    def from_config(
        cls,
        config_or_path: Union[str, Path, "AvitoConfig"] = "config.toml",
        tracker_db: Optional[Union[str, Path]] = None,
    ) -> "AvitoClient":
        """Create an AvitoClient instance configured from a parser_avito config.toml file."""
        from avito_sdk.config import AvitoConfig, load_avito_config

        cfg = load_avito_config(config_or_path) if not isinstance(config_or_path, AvitoConfig) else config_or_path
        cfg.output_dir.mkdir(parents=True, exist_ok=True)
        resolved_db = tracker_db or (cfg.output_dir / "avito_prices.db")
        client = cls(
            proxy=cfg.proxy_string,
            proxy_change_url=cfg.proxy_change_url,
            use_playwright_cookies=cfg.use_webdriver,
            timeout=cfg.timeout,
            max_retries=cfg.max_count_of_retry,
            tracker_db=resolved_db,
            tg_token=cfg.tg_token,
            tg_chat_id=cfg.tg_chat_id if cfg.tg_chat_id else None,
            vk_token=cfg.vk_token,
            vk_user_id=cfg.vk_user_id if cfg.vk_user_id else None,
        )
        client._avito_config = cfg
        return client

    def notify_telegram(self, item: Item) -> None:
        """Send an item notification to the configured Telegram channel/chat."""
        if not self.notifier:
            raise ValueError("Telegram notifier is not configured. Pass tg_token and tg_chat_id to AvitoClient.")
        self.notifier.notify(item=item)

    def search(
        self,
        query: str = "",
        region: Optional[str] = "rossiya",
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        sort: str = "date",
        category: Optional[str] = None,
        with_delivery: bool = False,
        white_keywords: Optional[List[str]] = None,
        black_keywords: Optional[List[str]] = None,
        seller_blacklist: Optional[List[str]] = None,
        geo: Optional[str] = None,
        max_age: Optional[int] = None,
        ignore_reserved: bool = False,
        ignore_promotion: bool = False,
        only_new_or_changed: bool = False,
        enrich_details: bool = False,
        max_workers: int = 1,
        notify_telegram: bool = False,
        notify_vk: bool = False,
        telegram_progress: bool = False,
        show_progress: bool = False,
        excel_path: Optional[Union[str, Path]] = None,
        limit: Optional[int] = None,
        max_pages: int = 5,
    ) -> Generator[Item, None, None]:
        """
        Search Avito for items matching specified criteria and all 9 AdsFilter rules.
        Yields Item objects one by one.
        Note: When using max_workers > 1 or enrich_details=True, a mobile proxy
        (proxy + proxy_change_url) is strongly recommended to prevent IP bans.
        """
        from avito_sdk.filters import AdsFilter
        from avito_sdk.telegram import render_progress_bar

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
        ads_filter = AdsFilter(
            min_price=min_price,
            max_price=max_price,
            white_keywords=white_keywords,
            black_keywords=black_keywords,
            seller_blacklist=seller_blacklist,
            geo=geo,
            max_age=max_age,
            ignore_reserved=ignore_reserved,
            ignore_promotion=ignore_promotion,
            only_new_or_changed=only_new_or_changed,
        )

        collected_for_excel: List[Item] = []
        drops_count = 0
        yielded_count = 0
        total_expected = limit or (max_pages * 50)
        use_mob_proxy = bool(self.transport.proxy)

        progress_ids = {}
        if telegram_progress and self.notifier:
            progress_ids = self.notifier.start_progress(
                query=query or region or "Avito",
                total=total_expected,
                use_mobile_proxy=use_mob_proxy,
                workers=max_workers,
            )

        try:
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

                    if not ads_filter.matches(item):
                        continue

                    if item.price_drop and item.price_drop > 0:
                        drops_count += 1

                    if notify_telegram and self.notifier:
                        try:
                            self.notifier.notify(item=item)
                        except Exception as tg_err:
                            logger.warning(f"Failed to send Telegram notification for {item.id}: {tg_err}")

                    if notify_vk and self.vk_notifier:
                        try:
                            self.vk_notifier.notify(item=item)
                        except Exception as vk_err:
                            logger.warning(f"Failed to send VK notification for {item.id}: {vk_err}")

                    collected_for_excel.append(item)
                    yielded_count += 1

                    if show_progress:
                        bar = render_progress_bar(yielded_count, limit or max(yielded_count, len(items)))
                        print(f"\r[*] {bar} | Ротаций IP: {self.transport.ip_rotations}", end="", flush=True)

                    if progress_ids and self.notifier and (yielded_count % 5 == 0 or yielded_count == limit):
                        self.notifier.update_progress(
                            progress_ids=progress_ids,
                            query=query or region or "Avito",
                            current=yielded_count,
                            total=limit or max(yielded_count, len(items)),
                            use_mobile_proxy=use_mob_proxy,
                            workers=max_workers,
                            drops_count=drops_count,
                            ip_rotations=self.transport.ip_rotations,
                        )

                    yield item
                    if limit and yielded_count >= limit:
                        break
                if limit and yielded_count >= limit:
                    break
        finally:
            if show_progress and yielded_count > 0:
                print()
            if excel_path and collected_for_excel:
                to_excel(collected_for_excel, excel_path)
            if progress_ids and self.notifier:
                self.notifier.finish_progress(
                    progress_ids=progress_ids,
                    query=query or region or "Avito",
                    total_found=yielded_count,
                    use_mobile_proxy=use_mob_proxy,
                    drops_count=drops_count,
                    ip_rotations=self.transport.ip_rotations,
                    excel_path=excel_path if collected_for_excel else None,
                )

    def scrape_url(
        self,
        url: str,
        max_pages: int = 1,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        white_keywords: Optional[List[str]] = None,
        black_keywords: Optional[List[str]] = None,
        seller_blacklist: Optional[List[str]] = None,
        geo: Optional[str] = None,
        max_age: Optional[int] = None,
        ignore_reserved: bool = False,
        ignore_promotion: bool = False,
        only_new_or_changed: bool = False,
        enrich_details: bool = False,
        max_workers: int = 1,
        notify_telegram: bool = False,
        notify_vk: bool = False,
        telegram_progress: bool = False,
        show_progress: bool = False,
        excel_path: Optional[Union[str, Path]] = None,
    ) -> List[Item]:
        """Scrape items from an existing Avito search or catalog URL across multiple pages with full filtering."""
        from avito_sdk.filters import AdsFilter
        from avito_sdk.telegram import render_progress_bar

        ads_filter = AdsFilter(
            min_price=min_price,
            max_price=max_price,
            white_keywords=white_keywords,
            black_keywords=black_keywords,
            seller_blacklist=seller_blacklist,
            geo=geo,
            max_age=max_age,
            ignore_reserved=ignore_reserved,
            ignore_promotion=ignore_promotion,
            only_new_or_changed=only_new_or_changed,
        )

        results: List[Item] = []
        drops_count = 0
        use_mob_proxy = bool(self.transport.proxy)

        progress_ids = {}
        if telegram_progress and self.notifier:
            progress_ids = self.notifier.start_progress(
                query=url[:50],
                total=max_pages * 50,
                use_mobile_proxy=use_mob_proxy,
                workers=max_workers,
            )

        try:
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
                    if not ads_filter.matches(item):
                        continue
                    if item.price_drop and item.price_drop > 0:
                        drops_count += 1
                    if notify_telegram and self.notifier:
                        try:
                            self.notifier.notify(item=item)
                        except Exception as tg_err:
                            logger.warning(f"Failed to send Telegram notification for {item.id}: {tg_err}")
                    if notify_vk and self.vk_notifier:
                        try:
                            self.vk_notifier.notify(item=item)
                        except Exception as vk_err:
                            logger.warning(f"Failed to send VK notification for {item.id}: {vk_err}")
                    results.append(item)

                    if show_progress:
                        bar = render_progress_bar(len(results), max(len(results), len(page_items) * max_pages))
                        print(f"\r[*] {bar} | Ротаций IP: {self.transport.ip_rotations}", end="", flush=True)

                if progress_ids and self.notifier:
                    self.notifier.update_progress(
                        progress_ids=progress_ids,
                        query=url[:50],
                        current=len(results),
                        total=max(len(results), len(page_items) * max_pages),
                        use_mobile_proxy=use_mob_proxy,
                        workers=max_workers,
                        drops_count=drops_count,
                        ip_rotations=self.transport.ip_rotations,
                    )
        finally:
            if show_progress and results:
                print()
            if excel_path and results:
                to_excel(results, excel_path)
            if progress_ids and self.notifier:
                self.notifier.finish_progress(
                    progress_ids=progress_ids,
                    query=url[:50],
                    total_found=len(results),
                    use_mobile_proxy=use_mob_proxy,
                    drops_count=drops_count,
                    ip_rotations=self.transport.ip_rotations,
                    excel_path=excel_path if results else None,
                )

        return results

    def run_config(self, config_or_path: Optional[Union[str, Path, "AvitoConfig"]] = None) -> List[Item]:
        """
        Execute a full parser_avito cycle (or continuous loop if one_time_start=False)
        using a config.toml file or AvitoConfig object.
        """
        import time
        from avito_sdk.config import AvitoConfig, load_avito_config
        from avito_sdk.cookies import ParsePhone

        if config_or_path is not None:
            cfg = load_avito_config(config_or_path) if not isinstance(config_or_path, AvitoConfig) else config_or_path
        elif hasattr(self, "_avito_config"):
            cfg = self._avito_config
        else:
            cfg = load_avito_config("config.toml")

        enrich = bool(cfg.parse_views or cfg.parse_description or cfg.parse_params)
        all_collected: List[Item] = []

        while True:
            for idx, url in enumerate(cfg.urls):
                out_file = None
                if cfg.save_xlsx:
                    cfg.output_dir.mkdir(parents=True, exist_ok=True)
                    fname = f"avito_link_{idx + 1}.xlsx" if cfg.one_file_for_link else "avito_result.xlsx"
                    out_file = cfg.output_dir / fname

                items = self.scrape_url(
                    url=url,
                    max_pages=cfg.count,
                    min_price=cfg.min_price,
                    max_price=cfg.max_price,
                    white_keywords=cfg.keys_word_white_list,
                    black_keywords=cfg.keys_word_black_list,
                    seller_blacklist=cfg.seller_black_list,
                    geo=cfg.geo,
                    max_age=cfg.max_age,
                    ignore_reserved=cfg.ignore_reserv,
                    ignore_promotion=cfg.ignore_promotion,
                    only_new_or_changed=True,
                    enrich_details=enrich,
                    max_workers=cfg.max_workers,
                    notify_telegram=bool(self.notifier),
                    notify_vk=bool(self.vk_notifier),
                    telegram_progress=bool(self.notifier),
                    show_progress=True,
                    excel_path=out_file,
                )

                if cfg.parse_phone and cfg.cookies_api_key and items:
                    ParsePhone(api_key=cfg.cookies_api_key).enrich_phones(items)
                    if out_file:
                        to_excel(items, out_file)

                all_collected.extend(items)
                if idx < len(cfg.urls) - 1 and cfg.pause_between_links > 0:
                    time.sleep(cfg.pause_between_links)

            if cfg.one_time_start:
                if self.notifier:
                    self.notifier.notify(message="Парсинг Авито завершён. Все ссылки обработаны")
                break
            time.sleep(max(cfg.pause_general, 1))

        return all_collected

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
