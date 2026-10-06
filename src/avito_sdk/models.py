"""
Data models for avito-sdk.
Pure dataclasses with full type hinting, JSON serialization, and high performance.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Item:
    """
    Representation of an Avito item/listing.
    Includes enhancements from PR #334 (price tracking, seller name)
    and PR #337 (parameters / characteristics).
    """

    id: int
    title: str = ""
    price: int = 0
    old_price: Optional[int] = None
    price_string: Optional[str] = None
    seller_name: Optional[str] = None
    seller_id: Optional[str] = None
    url: str = ""
    description: Optional[str] = None
    params: Dict[str, str] = field(default_factory=dict)
    category_name: Optional[str] = None
    category_id: Optional[int] = None
    location_name: Optional[str] = None
    address: Optional[str] = None
    coords: Optional[Dict[str, float]] = None
    images: List[str] = field(default_factory=list)
    images_count: int = 0
    total_views: Optional[int] = None
    today_views: Optional[int] = None
    is_promotion: bool = False
    is_reserved: bool = False
    is_favorite: bool = False
    is_new: bool = True
    phone: Optional[str] = None
    has_phone: bool = False
    published_at: Optional[datetime] = None
    raw_data: Optional[Dict[str, Any]] = None

    @property
    def price_drop(self) -> Optional[int]:
        """Returns the price drop amount if the price decreased, else None."""
        if self.old_price is not None and self.old_price > self.price:
            return self.old_price - self.price
        return None

    @property
    def has_price_changed(self) -> bool:
        """True if the item has an old price recorded that differs from current."""
        return self.old_price is not None and self.old_price != self.price

    def to_dict(self, include_raw: bool = False) -> Dict[str, Any]:
        """Convert item to a plain dictionary."""
        data = asdict(self)
        if not include_raw:
            data.pop("raw_data", None)
        if self.published_at is not None:
            data["published_at"] = self.published_at.isoformat()
        data["price_drop"] = self.price_drop
        data["has_price_changed"] = self.has_price_changed
        return data

    def to_json(self, indent: Optional[int] = None, include_raw: bool = False) -> str:
        """Convert item to a JSON string."""
        return json.dumps(self.to_dict(include_raw=include_raw), ensure_ascii=False, indent=indent)

    def __repr__(self) -> str:
        price_part = f"{self.price:,} ₽"
        if self.old_price is not None:
            price_part += f" (was {self.old_price:,} ₽)"
        seller_part = f", seller='{self.seller_name}'" if self.seller_name else ""
        return f"<Item id={self.id} title='{self.title[:30]}...' price={price_part}{seller_part}>"


@dataclass
class SearchFilter:
    """Search query parameters and filters."""

    query: str = ""
    region: Optional[str] = None  # e.g. "moskva", "sankt-peterburg", "rossiya"
    category: Optional[str] = None
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    sort: str = "date"  # "date", "price_asc", "price_desc", "default"
    with_delivery: bool = False
    only_private: bool = False
    only_company: bool = False
    page: int = 1


@dataclass
class SearchPage:
    """Result page containing items and pagination info."""

    items: List[Item]
    page: int
    has_next: bool
    total_found: Optional[int] = None


@dataclass
class PriceRecord:
    """Historical price entry for an item."""

    item_id: int
    price: int
    timestamp: datetime = field(default_factory=datetime.utcnow)
    seller_name: Optional[str] = None
    title: Optional[str] = None
