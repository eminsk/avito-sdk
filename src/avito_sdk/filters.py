"""
Comprehensive ad filtering engine (AdsFilter), ported and enhanced from Duff89/parser_avito.
Supports all 9 filters:
1. only_new_or_changed (viewed filter with price-drop pass-through)
2. min_price / max_price
3. black_keywords (keys_word_black_list)
4. white_keywords (keys_word_white_list)
5. geo (address / location substring match)
6. seller_blacklist (seller_black_list by seller_id or seller_name)
7. max_age (maximum age in seconds from published_at)
8. ignore_reserved (ignore_reserv)
9. ignore_promotion (ignore_promotion)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterable, List, Optional, Sequence

from avito_sdk.models import Item


class AdsFilter:
    """
    Applies a pipeline of 9 configurable filters to a list or stream of Avito Item objects.
    """

    def __init__(
        self,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        white_keywords: Optional[Sequence[str]] = None,
        black_keywords: Optional[Sequence[str]] = None,
        seller_blacklist: Optional[Sequence[str]] = None,
        geo: Optional[str] = None,
        max_age: Optional[int] = None,
        ignore_reserved: bool = False,
        ignore_promotion: bool = False,
        only_new_or_changed: bool = False,
    ):
        self.min_price = min_price
        self.max_price = max_price
        self.white_keywords = [w.strip().lower() for w in (white_keywords or []) if w and w.strip()]
        self.black_keywords = [b.strip().lower() for b in (black_keywords or []) if b and b.strip()]
        self.seller_blacklist = {s.strip().lower() for s in (seller_blacklist or []) if s and s.strip()}
        self.geo = geo.strip().lower() if (geo and geo.strip()) else None
        self.max_age = max_age if (max_age and max_age > 0) else None
        self.ignore_reserved = ignore_reserved
        self.ignore_promotion = ignore_promotion
        self.only_new_or_changed = only_new_or_changed

    def matches(self, item: Item) -> bool:
        """Return True if a single Item passes all configured filters."""
        # 1. Viewed / price-change filter
        if self.only_new_or_changed:
            if not getattr(item, "is_new", True) and not item.has_price_changed:
                return False

        # 2. Price range
        price = item.price or 0
        if self.min_price is not None and self.min_price > 0 and price < self.min_price:
            return False
        if self.max_price is not None and self.max_price > 0 and price > self.max_price:
            return False

        # 3 & 4. Keywords (title + description + params)
        if self.black_keywords or self.white_keywords:
            params_text = " ".join(f"{k} {v}" for k, v in (item.params or {}).items())
            full_text = f"{item.title or ''} {item.description or ''} {params_text}".lower()
            if self.black_keywords and any(phrase in full_text for phrase in self.black_keywords):
                return False
            if self.white_keywords and not any(phrase in full_text for phrase in self.white_keywords):
                return False

        # 5. Geo / Address filter
        if self.geo:
            addr_text = f"{item.address or ''} {item.location_name or ''}".lower()
            if self.geo not in addr_text:
                return False

        # 6. Seller blacklist (matches seller_id or seller_name)
        if self.seller_blacklist:
            sid = (item.seller_id or "").strip().lower()
            sname = (item.seller_name or "").strip().lower()
            if (sid and sid in self.seller_blacklist) or (sname and sname in self.seller_blacklist):
                return False

        # 7. Max age (in seconds)
        if self.max_age and item.published_at is not None:
            now = datetime.now(timezone.utc)
            pub = item.published_at
            if pub.tzinfo is None:
                pub = pub.replace(tzinfo=timezone.utc)
            if (now - pub) > timedelta(seconds=self.max_age):
                return False

        # 8. Ignore reserved
        if self.ignore_reserved and getattr(item, "is_reserved", False):
            return False

        # 9. Ignore promotion
        if self.ignore_promotion and getattr(item, "is_promotion", False):
            return False

        return True

    def apply(self, items: Iterable[Item]) -> List[Item]:
        """Filter an iterable of Item objects and return the matching list."""
        return [item for item in items if self.matches(item)]
