"""
Command-line interface (CLI) for avito-sdk.
Run queries, inspect items, monitor prices, and export datasets directly from terminal.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from avito_sdk.client import AvitoClient
from avito_sdk.export import to_csv, to_excel, to_json
from avito_sdk.tracker import PriceTracker


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="avito-sdk",
        description="High-performance Avito Scraper & SDK with price tracking and parameters extraction",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Search command
    search_p = subparsers.add_parser("search", help="Search Avito listings")
    search_p.add_argument("query", help="Search query (e.g. 'ноутбук lenovo')")
    search_p.add_argument("-r", "--region", default="rossiya", help="Region slug or city (default: rossiya)")
    search_p.add_argument("--min-price", type=int, default=None, help="Minimum price filter in RUB")
    search_p.add_argument("--max-price", type=int, default=None, help="Maximum price filter in RUB")
    search_p.add_argument("-n", "--limit", type=int, default=20, help="Maximum number of items to fetch")
    search_p.add_argument("-p", "--pages", type=int, default=3, help="Max search result pages to scan")
    search_p.add_argument("-o", "--output", help="Save output to file (.json, .csv, .xlsx)")
    search_p.add_argument("--enrich", action="store_true", help="Fetch detailed parameters and full descriptions")

    # Item command
    item_p = subparsers.add_parser("item", help="Fetch detailed info for a single item")
    item_p.add_argument("item_id", type=int, help="Avito numeric item ID")
    item_p.add_argument("-o", "--output", help="Save output to JSON file")

    # Drops command
    drops_p = subparsers.add_parser("drops", help="Show all tracked items whose price has dropped")
    drops_p.add_argument("--db", default="avito_prices.db", help="Path to SQLite price database")

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "search":
        print(f"[*] Searching for '{args.query}' in '{args.region}' (limit={args.limit})...")
        client = AvitoClient()
        items = list(
            client.search(
                query=args.query,
                region=args.region,
                min_price=args.min_price,
                max_price=args.max_price,
                enrich_details=args.enrich,
                limit=args.limit,
                max_pages=args.pages,
            )
        )
        print(f"[+] Found {len(items)} items:")
        for idx, item in enumerate(items, 1):
            price_str = f"{item.price:,} ₽"
            if item.old_price:
                price_str += f" (было: {item.old_price:,} ₽, снижение на {item.price_drop:,} ₽)"
            seller_str = f" | {item.seller_name}" if item.seller_name else ""
            print(f" {idx:2d}. [{item.id}] {item.title[:45]} - {price_str}{seller_str}")

        if args.output:
            out_path = Path(args.output)
            suffix = out_path.suffix.lower()
            if suffix == ".xlsx":
                to_excel(items, out_path)
            elif suffix == ".csv":
                to_csv(items, out_path)
            else:
                to_json(items, out_path)
            print(f"[✓] Saved {len(items)} items to {out_path}")

    elif args.command == "item":
        print(f"[*] Fetching item {args.item_id}...")
        client = AvitoClient()
        item = client.get_item(args.item_id)
        print(f"\nID: {item.id}")
        print(f"Title: {item.title}")
        print(f"Price: {item.price:,} ₽")
        if item.seller_name:
            print(f"Seller: {item.seller_name} (ID: {item.seller_id})")
        if item.total_views is not None:
            print(f"Views: {item.total_views} (today: {item.today_views})")
        if item.params:
            print("Parameters:")
            for k, v in item.params.items():
                print(f"  - {k}: {v}")
        if item.description:
            print(f"\nDescription:\n{item.description[:300]}...")

        if args.output:
            to_json([item], args.output)
            print(f"[✓] Saved to {args.output}")

    elif args.command == "drops":
        tracker = PriceTracker(db_path=args.db)
        drops = tracker.get_price_drops()
        if not drops:
            print("[-] No price drops recorded yet in database.")
        else:
            print(f"[+] Found {len(drops)} items with price drops:")
            for d in drops:
                diff = d['initial_price'] - d['current_price']
                print(
                    f" - [{d['item_id']}] {d.get('title', '')[:40]}: "
                    f"{d['initial_price']:,} -> {d['current_price']:,} ₽ (-{diff:,} ₽)"
                )

    return 0


if __name__ == "__main__":
    sys.exit(main())
