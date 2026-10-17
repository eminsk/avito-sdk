"""
avito-sdk: High-performance Avito scraping & data extraction SDK for Python.

Includes enhancements from Duff89/parser_avito:
- PR #334: Real-time price change tracking and seller name extraction
- PR #337: Deep parameters and characteristics parsing («О помещении», авто, etc.)
- PR #329 / Issue #305: Full description parsing from microdata & mobile API
- Asynchronous and Synchronous clients
- Headless execution (Zero GUI / Zero Tkinter dependencies)
- Universal runtime support (Python 3.8-3.16, Free-Threaded No-GIL, PyPy)
"""

from __future__ import annotations

from avito_sdk.async_client import AsyncAvitoClient
from avito_sdk.client import AvitoClient
from avito_sdk.config import AvitoConfig, load_avito_config
from avito_sdk.cookies import (
    AvitoUrlConverter,
    ExternalApiCookiesProvider,
    ParsePhone,
    PlaywrightCookieProvider,
    parse_proxy_config,
)
from avito_sdk.export import (
    to_csv,
    to_dataframe,
    to_excel,
    to_json,
    to_jsonl,
)
from avito_sdk.extractors import (
    extract_all_embedded_states,
    extract_catalog_items,
    extract_description,
    extract_embedded_state,
    extract_params,
    extract_seller_id,
    extract_seller_name,
    extract_views,
    parse_raw_item,
)
from avito_sdk.filters import AdsFilter
from avito_sdk.models import (
    Item,
    PriceRecord,
    SearchFilter,
    SearchPage,
)
from avito_sdk.telegram import (
    AvitoTelegramBot,
    TelegramNotifier,
    render_progress_bar,
    render_telegram_progress_bar,
)
from avito_sdk.tracker import PriceTracker
from avito_sdk.url import (
    build_item_api_url,
    build_item_web_url,
    build_page_url,
    build_search_url,
    normalize_region,
)
from avito_sdk.vk import VKNotifier
from avito_sdk.mcp_server import AvitoMCPServer
from avito_sdk.logging_utils import PrivacyFilter, setup_logging
from avito_sdk.mobileproxy import MobileProxySpace
from avito_sdk.process_guard import (
    SingleInstanceGuard,
    ensure_single_instance,
    is_pid_alive,
    release_instance_lock,
    single_instance,
)

__version__ = "0.3.4"
__author__ = "eminsk"

__all__ = [
    "__version__",
    "AvitoClient",
    "AsyncAvitoClient",
    "SingleInstanceGuard",
    "ensure_single_instance",
    "release_instance_lock",
    "single_instance",
    "is_pid_alive",
    "AvitoConfig",
    "load_avito_config",
    "MobileProxySpace",
    "setup_logging",
    "PrivacyFilter",
    "AdsFilter",
    "AvitoMCPServer",
    "TelegramNotifier",
    "VKNotifier",
    "AvitoTelegramBot",
    "PlaywrightCookieProvider",
    "ExternalApiCookiesProvider",
    "AvitoUrlConverter",
    "ParsePhone",
    "parse_proxy_config",
    "render_progress_bar",
    "render_telegram_progress_bar",
    "Item",
    "SearchFilter",
    "SearchPage",
    "PriceRecord",
    "PriceTracker",
    "extract_params",
    "extract_seller_name",
    "extract_seller_id",
    "extract_description",
    "extract_views",
    "parse_raw_item",
    "extract_catalog_items",
    "extract_embedded_state",
    "extract_all_embedded_states",
    "build_search_url",
    "build_item_api_url",
    "build_item_web_url",
    "build_page_url",
    "normalize_region",
    "to_excel",
    "to_json",
    "to_jsonl",
    "to_csv",
    "to_dataframe",
]
