"""
Avito URL builders, parsers, and API endpoint converters.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit

from avito_sdk.models import SearchFilter

SORT_MAP = {
    "default": "101",
    "date": "104",
    "price_asc": "1",
    "price_desc": "2",
}

REGION_SLUGS = {
    "москва": "moskva",
    "санкт-петербург": "sankt-peterburg",
    "россия": "rossiya",
    "новосибирск": "novosibirsk",
    "екатеринбург": "ekaterinburg",
    "казань": "kazan",
    "нижний новгород": "nizhniy_novgorod",
    "краснодар": "krasnodar",
    "самара": "samara",
    "уфа": "ufa",
    "ростов-на-дону": "rostov-na-donu",
    "воронеж": "voronezh",
}


def normalize_region(region: Optional[str]) -> str:
    """Normalize a region name to an Avito URL path slug."""
    if not region:
        return "rossiya"
    slug = region.lower().strip()
    return REGION_SLUGS.get(slug, slug)


def build_search_url(search: SearchFilter) -> str:
    """
    Construct a canonical Avito search URL from SearchFilter parameters.
    Example output: https://www.avito.ru/moskva?q=macbook&pmin=50000&s=104
    """
    region = normalize_region(search.region)
    path = f"/{region}"
    if search.category:
        cat = search.category.strip("/")
        path = f"{path}/{cat}"

    query_params = []
    if search.query:
        query_params.append(("q", search.query))
    if search.min_price is not None:
        query_params.append(("pmin", str(search.min_price)))
    if search.max_price is not None:
        query_params.append(("pmax", str(search.max_price)))
    if search.sort in SORT_MAP:
        query_params.append(("s", SORT_MAP[search.sort]))
    if search.with_delivery:
        query_params.append(("d", "1"))
    if search.only_private:
        query_params.append(("user", "1"))
    elif search.only_company:
        query_params.append(("user", "2"))
    if search.page > 1:
        query_params.append(("p", str(search.page)))

    query_str = urlencode(query_params)
    return f"https://www.avito.ru{path}{'?' + query_str if query_str else ''}"


def build_page_url(base_url: str, page: int) -> str:
    """Update or add page number to an Avito search or API URL."""
    parts = urlsplit(base_url)
    query = parse_qsl(parts.query, keep_blank_values=True)
    page_param = "page" if "api" in parts.path else "p"
    filtered = [(k, v) for k, v in query if k not in ("p", "page")]
    if page > 1 or page_param == "page":
        filtered.append((page_param, str(page)))
    new_query = urlencode(filtered)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))


def build_item_api_url(item_id: int) -> str:
    """Generate mobile API endpoint for fetching rich item card data."""
    return f"https://m.avito.ru/api/1/card/items/{item_id}"


def build_item_web_url(item_id: int, slug: str = "item") -> str:
    """Generate canonical public web URL for an Avito item."""
    return f"https://www.avito.ru/{slug}_{item_id}"
