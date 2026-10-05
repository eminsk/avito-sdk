"""Tests for PriceTracker (PR #334 / Issue #214 price changes)."""

import os
from avito_sdk.models import Item
from avito_sdk.tracker import PriceTracker


def test_tracker_initial_and_price_drop(tmp_path):
    db_file = tmp_path / "test_prices.db"
    tracker = PriceTracker(db_path=db_file)

    item = Item(id=1001, title="Sony PlayStation 5", price=60000, seller_name="GameStore")

    # 1. First encounter - should record price without change
    changed, old = tracker.check_and_update(item)
    assert changed is False
    assert old is None
    assert item.old_price is None

    # 2. Second encounter with same price - should not report change
    changed, old = tracker.check_and_update(item)
    assert changed is False
    assert old == 60000

    # 3. Price drops from 60,000 to 52,000
    item.price = 52000
    changed, old = tracker.check_and_update(item)
    assert changed is True
    assert old == 60000
    assert item.old_price == 60000
    assert item.price_drop == 8000
    assert item.has_price_changed is True

    # 4. Check price drops list
    drops = tracker.get_price_drops()
    assert len(drops) == 1
    assert drops[0]["item_id"] == 1001
    assert drops[0]["current_price"] == 52000
    assert drops[0]["initial_price"] == 60000

    # 5. History should have 2 entries
    history = tracker.get_history(1001)
    assert len(history) == 2
    assert history[0].price == 60000
    assert history[1].price == 52000


def test_tracker_batch_processing(tmp_path):
    db_file = tmp_path / "test_batch.db"
    tracker = PriceTracker(db_path=db_file)

    items = [
        Item(id=1, price=100),
        Item(id=2, price=200),
    ]
    tracker.track_items(items)

    # Change price of item 1
    items[0].price = 80
    tracker.track_items(items)

    assert items[0].old_price == 100
    assert items[0].price_drop == 20
    assert items[1].old_price is None
