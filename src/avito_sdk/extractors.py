"""
Extraction logic for Avito items, parameters, descriptions, and seller details.
Combines and optimizes parser algorithms from PR #334, PR #337, and Issue #305.
"""

from __future__ import annotations

import html as html_lib
import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from bs4 import BeautifulSoup

from avito_sdk.models import Item


def nested_get(data: Any, *keys: str) -> Any:
    """Safely traverse nested dictionary keys."""
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def safe_int(val: Any, default: int = 0) -> int:
    """
    Safely extract ASCII decimal digits (0-9) and convert to int.
    Filters out unicode superscripts (e.g. '²' in '2466²' or 'м²') that cause int() to raise ValueError.
    """
    if val is None or isinstance(val, bool):
        return default
    if isinstance(val, (int, float)):
        return int(val)
    # Only keep ASCII decimal digits '0'..'9'
    digits = "".join(ch for ch in str(val) if "0" <= ch <= "9")
    if not digits:
        return default
    try:
        return int(digits)
    except (ValueError, TypeError):
        return default



def extract_params(payload: Any) -> Dict[str, str]:
    """
    Extract item parameters and characteristics (e.g. «О помещении», авто, электроника).
    Supports:
    1. Beduin scenario: payload['success']['view']['scenario']['beduin']['main']['params']
    2. Mobile API: payload['success']['mobile']['params' / 'parameters' / 'properties']
    3. Flat dictionary / key-value lists
    """
    if not isinstance(payload, dict):
        return {}

    params_dict: Dict[str, str] = {}

    # 1. Beduin scenario widgets: success.view.scenario.beduin.main.params
    card_params = nested_get(
        payload, "success", "view", "scenario", "beduin", "main", "params"
    )
    if isinstance(card_params, dict):
        for _, widget_data in card_params.items():
            if isinstance(widget_data, dict):
                items = widget_data.get("items")
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, dict):
                            title = (
                                item.get("title")
                                or item.get("name")
                                or item.get("label")
                            )
                            desc = (
                                item.get("description")
                                or item.get("value")
                                or item.get("text")
                            )
                            if isinstance(title, str) and title.strip():
                                if desc is not None and str(desc).strip():
                                    params_dict[title.strip()] = str(desc).strip()

    # 2. Mobile API structures: success.mobile.params / parameters / properties
    mobile = nested_get(payload, "success", "mobile")
    if isinstance(mobile, dict):
        for container_key in ("params", "parameters", "properties"):
            container = mobile.get(container_key)
            if isinstance(container, list):
                for item in container:
                    if isinstance(item, dict):
                        title = (
                            item.get("title")
                            or item.get("name")
                            or item.get("label")
                        )
                        desc = (
                            item.get("description")
                            or item.get("value")
                            or item.get("text")
                        )
                        if isinstance(title, str) and title.strip():
                            if desc is not None and str(desc).strip():
                                params_dict[title.strip()] = str(desc).strip()
            elif isinstance(container, dict):
                # Unpack flat items list: e.g. parameters['flat']
                flat_list = container.get("flat")
                if isinstance(flat_list, list):
                    for item in flat_list:
                        if isinstance(item, dict):
                            title = item.get("title") or item.get("name") or item.get("label")
                            desc = item.get("description") or item.get("value") or item.get("text")
                            if isinstance(title, str) and title.strip():
                                if desc is not None and str(desc).strip():
                                    params_dict[title.strip()] = str(desc).strip()

                # Unpack grouped items: e.g. parameters['groups']
                groups_list = container.get("groups")
                if isinstance(groups_list, list):
                    for grp in groups_list:
                        if isinstance(grp, dict) and isinstance(grp.get("items"), list):
                            for item in grp["items"]:
                                if isinstance(item, dict):
                                    title = item.get("title") or item.get("name") or item.get("label")
                                    desc = item.get("description") or item.get("value") or item.get("text")
                                    if isinstance(title, str) and title.strip():
                                        if desc is not None and str(desc).strip():
                                            params_dict[title.strip()] = str(desc).strip()

                # Other scalar key-values, skipping UI metadata containers
                for k, v in container.items():
                    if k in ("flat", "groups", "expandButton", "flatTitle"):
                        continue
                    if isinstance(k, str) and k.strip() and isinstance(v, (str, int, float, bool)):
                        params_dict[k.strip()] = str(v).strip()

    return params_dict


def extract_params_from_html(html_text: str) -> Dict[str, str]:
    """Fallback extractor for item parameters from rendered HTML."""
    if not html_text:
        return {}
    soup = BeautifulSoup(html_text, "html.parser")
    params: Dict[str, str] = {}

    # Check for parameters list
    for li in soup.select('[data-marker*="item-params/item"], li[class*="params-item"]'):
        text = li.get_text(separator=":", strip=True)
        if ":" in text:
            parts = text.split(":", 1)
            k, v = parts[0].strip(), parts[1].strip()
            if k and v:
                params[k] = v

    # Check embedded JSON
    embedded_data = extract_embedded_state(soup)
    if embedded_data:
        item_data = nested_get(embedded_data, "loaderData", "data", "item")
        if isinstance(item_data, dict):
            params.update(extract_params({"success": {"mobile": item_data}}))

    return params


def extract_seller_name(payload: Any, html_text: Optional[str] = None) -> Optional[str]:
    """
    Extract seller name from API payload or HTML markup.
    Addresses Issue #333 and PR #334.
    """
    # 1. From payload
    if isinstance(payload, dict):
        seller = (
            nested_get(payload, "success", "mobile", "seller")
            or nested_get(payload, "seller")
            or nested_get(payload, "user")
        )
        if isinstance(seller, dict):
            name = seller.get("name") or seller.get("title")
            if isinstance(name, str) and name.strip():
                return name.strip()

    # 2. From HTML
    if html_text:
        soup = BeautifulSoup(html_text, "html.parser")
        for marker in (
            '[data-marker="seller-info/name"]',
            '[data-marker="seller-link/link"]',
            '[data-marker="seller-info/label"]',
            '[data-marker="seller-name"]',
        ):
            el = soup.select_one(marker)
            if el and el.get_text(strip=True):
                return el.get_text(strip=True)

        embedded_data = extract_embedded_state(soup)
        if embedded_data:
            seller = nested_get(embedded_data, "loaderData", "data", "item", "seller")
            if isinstance(seller, dict):
                name = seller.get("name")
                if isinstance(name, str) and name.strip():
                    return name.strip()

    return None


def extract_seller_id(payload_or_link: Any) -> Optional[str]:
    """Extract seller ID, user hash, or public slug from userLogo, seller info, or URL."""
    if not payload_or_link:
        return None

    if isinstance(payload_or_link, dict):
        seller = (
            nested_get(payload_or_link, "success", "mobile", "seller")
            or nested_get(payload_or_link, "success", "mobile", "sellerInfo")
            or payload_or_link.get("seller")
            or payload_or_link.get("sellerInfo")
            or payload_or_link
        )
        if isinstance(seller, dict):
            h = seller.get("userHash") or seller.get("userHashId") or seller.get("sellerId")
            if h and isinstance(h, str):
                return h.strip()
        link = (
            nested_get(payload_or_link, "userLogo", "link")
            or (seller.get("link") if isinstance(seller, dict) else None)
            or payload_or_link.get("sellerId")
        )
    else:
        link = str(payload_or_link)

    if link:
        match = re.search(r"userKey=([a-zA-Z0-9_\-]+)", str(link))
        if match:
            return match.group(1)
        match = re.search(r"/(?:brands|user)/([^/?#'\"\s]+)", str(link))
        if match:
            return match.group(1).rstrip("/")
        match = re.search(r"/(?:brands|user)/([a-zA-Z0-9_\-]+)", str(link))
        if match:
            return match.group(1)

    return None


def extract_description(payload: Any, html_text: Optional[str] = None) -> Optional[str]:
    """
    Extract full item description from API payload or HTML markup.
    Addresses Issue #305 (PR #329).
    """
    # 1. From API payload
    if isinstance(payload, dict):
        mobile = nested_get(payload, "success", "mobile")
        if isinstance(mobile, dict):
            desc = mobile.get("description")
            if isinstance(desc, str) and desc.strip():
                return desc.strip()

        # From scenario beduin description segments
        card_params = nested_get(
            payload, "success", "view", "scenario", "beduin", "main", "params"
        )
        if isinstance(card_params, dict):
            segments = nested_get(card_params, "description", "segments")
            if isinstance(segments, list):
                parts = [
                    s["text"]
                    for s in segments
                    if isinstance(s, dict) and isinstance(s.get("text"), str)
                ]
                text = "".join(parts).replace("\u2028", "\n").strip()
                if text:
                    return text

    # 2. From HTML
    if html_text:
        soup = BeautifulSoup(html_text, "html.parser")
        desc_el = soup.select_one('[data-marker="item-description/text"]')
        if desc_el:
            text = desc_el.get_text(separator="\n", strip=True)
            if text:
                return text

        desc_meta = soup.select_one('[itemprop="description"]')
        if desc_meta:
            text = desc_meta.get_text(separator="\n", strip=True)
            if text:
                return text

        embedded_data = extract_embedded_state(soup)
        if embedded_data:
            item_data = nested_get(embedded_data, "loaderData", "data", "item")
            if isinstance(item_data, dict):
                desc = item_data.get("description")
                if isinstance(desc, str) and desc.strip():
                    return desc.strip()

    return None


def extract_views(payload: Any, html_text: Optional[str] = None) -> Tuple[Optional[int], Optional[int]]:
    """Extract (total_views, today_views) from API payload or HTML."""
    total: Optional[int] = None
    today: Optional[int] = None

    def parse_count(val: Any) -> Optional[int]:
        if isinstance(val, bool) or val is None:
            return None
        res = safe_int(val, default=-1)
        return res if res >= 0 else None

    # 1. From payload
    if isinstance(payload, dict):
        mobile_views = nested_get(payload, "success", "mobile", "stats", "views")
        if isinstance(mobile_views, dict):
            total = parse_count(mobile_views.get("total"))
            today = parse_count(mobile_views.get("today"))

        if total is None or today is None:
            card_views = nested_get(
                payload, "success", "view", "scenario", "beduin", "main", "params", "metaDataAndStats", "views"
            )
            if isinstance(card_views, dict):
                if total is None:
                    total = parse_count(card_views.get("total"))
                if today is None:
                    today = parse_count(
                        card_views.get("today")
                        or card_views.get("todayViews")
                        or card_views.get("today_views")
                    )

    # 2. From HTML
    if (total is None or today is None) and html_text:
        soup = BeautifulSoup(html_text, "html.parser")
        total_el = soup.select_one('[data-marker="item-view/total-views"]')
        today_el = soup.select_one('[data-marker="item-view/today-views"]')
        if total is None and total_el:
            total = parse_count(total_el.get_text())
        if today is None and today_el:
            today = parse_count(today_el.get_text())

    return total, today


def extract_embedded_state(soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
    """Extract window.__initialData__ or JSON state scripts from HTML."""
    first_mfe_state = None
    try:
        for script in soup.select('script[type="mime/invalid"][data-mfe-state="true"]'):
            txt = script.text or ""
            if "sandbox" not in txt:
                try:
                    data = json.loads(html_lib.unescape(txt))
                    if isinstance(data, dict):
                        if first_mfe_state is None:
                            first_mfe_state = data
                        # Prioritize state containing catalog, search, or result payload
                        if any(k in data for k in ("search", "catalog", "items", "allItems", "result")):
                            return data
                except Exception:
                    pass
    except Exception:
        pass

    try:
        for s in soup.find_all("script"):
            text = s.string or s.text or ""
            if "__initialData__" in text:
                m = re.search(r'__initialData__\s*=\s*(["\'])(.*?)\1;', text, re.DOTALL)
                if m:
                    raw_val = m.group(2)
                    try:
                        decoded = json.loads(f'"{raw_val}"')
                        data = json.loads(decoded) if isinstance(decoded, str) else decoded
                        if isinstance(data, dict):
                            return data
                    except Exception:
                        pass
                m2 = re.search(r'__initialData__\s*=\s*({.+?});', text, re.DOTALL)
                if m2:
                    try:
                        data = json.loads(m2.group(1))
                        if isinstance(data, dict):
                            return data
                    except Exception:
                        pass
    except Exception:
        pass

    return first_mfe_state


def parse_raw_item(raw: Dict[str, Any]) -> Optional[Item]:
    """Parse a single raw JSON dictionary from Avito API into an Item dataclass."""
    if not isinstance(raw, dict):
        return None

    # Handle mobile wrapper {"type": "item", "value": {...}}
    if "value" in raw and isinstance(raw["value"], dict):
        raw = raw["value"]

    item_id_val = raw.get("id")
    if isinstance(item_id_val, bool) or item_id_val is None:
        return None
    item_id = safe_int(item_id_val, default=0)
    if not item_id:
        return None

    # Title & Price
    title = raw.get("title") or ""
    price_detailed = raw.get("priceDetailed") or {}
    price = 0
    if isinstance(price_detailed, dict) and price_detailed.get("value") is not None:
        price = safe_int(price_detailed.get("value"), default=0)
    elif isinstance(raw.get("price"), (int, float, str)):
        price = safe_int(raw["price"], default=0)
    elif isinstance(raw.get("price"), dict):
        cur = raw["price"].get("current") or raw["price"].get("value") or ""
        price = safe_int(cur, default=0)

    price_str = price_detailed.get("string") if isinstance(price_detailed, dict) else (
        raw.get("price", {}).get("current") if isinstance(raw.get("price"), dict) else None
    )

    # URL path (desktop urlPath or mobile uri) exactly as in parser_avito
    url_path = raw.get("urlPath") or raw.get("uri") or ""
    url_path_clean = url_path.split("?")[0].strip() if isinstance(url_path, str) else ""
    if url_path_clean.startswith("http://") or url_path_clean.startswith("https://"):
        full_url = url_path_clean
    elif url_path_clean:
        clean = url_path_clean.lstrip("/")
        full_url = f"https://www.avito.ru/{clean}"
    else:
        full_url = f"https://www.avito.ru/{item_id}"

    # Category & Location
    cat = raw.get("category") or {}
    cat_name = cat.get("name") if isinstance(cat, dict) else None
    cat_id = cat.get("id") or raw.get("categoryId") if isinstance(cat, dict) else raw.get("categoryId")

    loc = raw.get("location") or {}
    loc_name = loc.get("name") if isinstance(loc, dict) else None

    addr = raw.get("addressDetailed") or raw.get("geo") or {}
    formatted_addr = (
        addr.get("formattedAddress")
        or addr.get("locationName")
        if isinstance(addr, dict)
        else None
    )

    # Images (desktop gallery/images or mobile galleryItems)
    images: List[str] = []
    gallery = raw.get("gallery") or {}
    if isinstance(gallery, dict):
        for img_url in (gallery.get("image_urls") or gallery.get("image_large_urls") or []):
            if isinstance(img_url, str):
                images.append(img_url)
    if not images and isinstance(raw.get("galleryItems"), list):
        for g in raw["galleryItems"]:
            val = g.get("value", {}) if isinstance(g, dict) else {}
            if isinstance(val, dict):
                best = val.get("678x678") or val.get("372x372") or next(iter(val.values()), None)
                if isinstance(best, str):
                    images.append(best)
    if not images and isinstance(raw.get("images"), list):
        def _calc_dim(k: str) -> int:
            parts = str(k).split("x")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                return int(parts[0]) * int(parts[1])
            return 0

        for img in raw["images"]:
            if isinstance(img, dict) and img:
                best_key = max(img.keys(), key=_calc_dim)
                best = img.get(best_key)
                if isinstance(best, str):
                    images.append(best)

    # Promotion & Reserve detection
    is_promo = bool(raw.get("isPromotion", False))
    iva = raw.get("iva")
    if not is_promo and isinstance(iva, dict):
        date_steps = iva.get("DateInfoStep") or []
        for step in date_steps:
            payload = getattr(step, "payload", None) or (step.get("payload") if isinstance(step, dict) else None)
            if isinstance(payload, dict):
                vas = payload.get("vas") or []
                if any(isinstance(v, dict) and v.get("title") == "Продвинуто" for v in vas):
                    is_promo = True
                    break

    is_reserved = bool(raw.get("isReserved", False))
    contacts = raw.get("contacts")
    has_phone = bool(contacts.get("phone")) if isinstance(contacts, dict) else False

    # Seller ID & Name (desktop or mobile sellerInfo)
    seller_info = raw.get("sellerInfo") or raw.get("seller") or {}
    seller_name = raw.get("sellerName") or (seller_info.get("name") if isinstance(seller_info, dict) else None)
    seller_id = extract_seller_id(raw) or (
        str(seller_info.get("userKey")) if isinstance(seller_info, dict) and seller_info.get("userKey") else None
    )

    # Timestamp
    sort_ts = raw.get("sortTimeStamp")
    pub_dt = None
    if isinstance(sort_ts, (int, float)) and sort_ts > 0:
        try:
            pub_dt = datetime.fromtimestamp(sort_ts / 1000, tz=timezone.utc)
        except Exception:
            pass

    return Item(
        id=item_id,
        title=title,
        price=price,
        price_string=price_str,
        seller_id=seller_id,
        seller_name=seller_name,
        url=full_url,
        description=raw.get("description"),
        params=raw.get("params") or {},
        category_name=cat_name,
        category_id=cat_id if isinstance(cat_id, int) else None,
        location_name=loc_name,
        address=formatted_addr,
        coords=raw.get("coords") if isinstance(raw.get("coords"), dict) else None,
        images=images,
        images_count=len(images) or (gallery.get("imagesCount") if isinstance(gallery, dict) else 0),
        is_promotion=is_promo,
        is_reserved=is_reserved,
        phone=raw.get("phone"),
        has_phone=has_phone,
        published_at=pub_dt,
        raw_data=raw,
    )


def extract_catalog_items(payload: Any) -> List[Item]:
    """Extract a list of Item models from search / catalog JSON response."""
    if not isinstance(payload, dict):
        return []

    result = payload.get("result")
    search_cand = payload.get("search") if isinstance(payload, dict) else None
    candidates = [
        payload.get("catalog"),
        result.get("catalog") if isinstance(result, dict) else None,
        search_cand,
        result,
        payload,
    ]

    items_list: List[Any] = []
    for cand in candidates:
        if isinstance(cand, dict):
            if isinstance(cand.get("items"), list):
                items_list = cand["items"]
                break
            if isinstance(cand.get("allItems"), dict):
                items_list = list(cand["allItems"].values())
                break
            if isinstance(cand.get("allItems"), list):
                items_list = cand["allItems"]
                break

    parsed_items: List[Item] = []
    for raw in items_list:
        if isinstance(raw, dict):
            item = parse_raw_item(raw)
            if item:
                parsed_items.append(item)

    return parsed_items

