"""
Price tracking and change detection engine (PR #334 / Issue #214).
Stores historical item prices in SQLite and detects price drops.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import List, Optional, Tuple, Union

from avito_sdk.models import Item, PriceRecord


class PriceTracker:
    """
    Tracks price changes over time for Avito listings.
    Supports in-memory tracking or persistent SQLite storage.
    """

    def __init__(self, db_path: Union[str, Path] = "avito_prices.db"):
        self.db_path = str(db_path)
        self._lock = Lock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            # Current price cache for fast lookup
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS current_prices (
                    item_id INTEGER PRIMARY KEY,
                    price INTEGER NOT NULL,
                    title TEXT,
                    seller_name TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            # Full historical log
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id INTEGER NOT NULL,
                    price INTEGER NOT NULL,
                    title TEXT,
                    seller_name TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_history_item ON price_history(item_id, timestamp)"
            )
            conn.commit()

    def check_and_update(self, item: Item) -> Tuple[bool, Optional[int]]:
        """
        Check if an item's price has changed compared to last known price.
        If changed:
            - sets `item.old_price = saved_price`
            - logs new price in history
            - updates current_prices
            - returns `(True, old_price)`
        If new item:
            - records into database
            - returns `(False, None)`
        If unchanged:
            - returns `(False, current_price)`
        """
        item_id = item.id
        current_price = item.price
        title = item.title
        seller_name = item.seller_name

        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT price FROM current_prices WHERE item_id = ?", (item_id,)
            )
            row = cursor.fetchone()

            if row is None:
                # First time seeing this item
                item.is_new = True
                cursor.execute(
                    """
                    INSERT INTO current_prices (item_id, price, title, seller_name, last_updated)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (item_id, current_price, title, seller_name),
                )
                cursor.execute(
                    """
                    INSERT INTO price_history (item_id, price, title, seller_name, timestamp)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (item_id, current_price, title, seller_name),
                )
                conn.commit()
                return False, None

            item.is_new = False
            saved_price = int(row["price"])
            if saved_price != current_price:
                # Price changed!
                item.old_price = saved_price
                cursor.execute(
                    """
                    UPDATE current_prices
                    SET price = ?, title = ?, seller_name = ?, last_updated = CURRENT_TIMESTAMP
                    WHERE item_id = ?
                    """,
                    (current_price, title, seller_name, item_id),
                )
                cursor.execute(
                    """
                    INSERT INTO price_history (item_id, price, title, seller_name, timestamp)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (item_id, current_price, title, seller_name),
                )
                conn.commit()
                return True, saved_price

            return False, saved_price

    def track_items(self, items: List[Item]) -> List[Item]:
        """Process a list of items, updating each item's old_price if changed."""
        for item in items:
            self.check_and_update(item)
        return items

    def get_history(self, item_id: int) -> List[PriceRecord]:
        """Return full price history for a given item ordered by timestamp."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT item_id, price, timestamp, title, seller_name
                FROM price_history
                WHERE item_id = ?
                ORDER BY timestamp ASC
                """,
                (item_id,),
            )
            rows = cursor.fetchall()
            return [
                PriceRecord(
                    item_id=row["item_id"],
                    price=row["price"],
                    timestamp=datetime.fromisoformat(row["timestamp"])
                    if "T" in str(row["timestamp"])
                    else datetime.strptime(str(row["timestamp"]), "%Y-%m-%d %H:%M:%S"),
                    seller_name=row["seller_name"],
                    title=row["title"],
                )
                for row in rows
            ]

    def get_price_drops(self) -> List[dict]:
        """Find items whose latest price is strictly lower than their initial recorded price."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT c.item_id, c.title, c.seller_name, c.price as current_price, h.price as initial_price
                FROM current_prices c
                JOIN (
                    SELECT item_id, price, MIN(timestamp)
                    FROM price_history
                    GROUP BY item_id
                ) h ON c.item_id = h.item_id
                WHERE c.price < h.price
                ORDER BY (h.price - c.price) DESC
                """
            )
            return [dict(row) for row in cursor.fetchall()]
