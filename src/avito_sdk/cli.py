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
    search_p.add_argument("--proxy", default=None, help="Mobile proxy URL (e.g. http://user:pass@ip:port)")
    search_p.add_argument("--proxy-change-url", default=None, help="Mobile proxy IP rotation URL")
    search_p.add_argument("--playwright", action="store_true", help="Use Playwright Chromium to harvest session cookies ('ft')")
    search_p.add_argument("--workers", type=int, default=1, help="Number of parallel threads for card enrichment (requires mobile proxy)")
    search_p.add_argument("--tg-token", default=None, help="Telegram bot token for sending notifications & Excel report")
    search_p.add_argument("--tg-chat-id", default=None, help="Telegram channel (@channel or -100...) or chat ID")

    # Bot controller command
    bot_p = subparsers.add_parser("bot", help="Start interactive Telegram Bot controller with live progress bar and Excel export")
    bot_p.add_argument("--tg-token", required=True, help="Telegram Bot Token")
    bot_p.add_argument("--channel-id", default=None, help="Target Telegram channel ID for forwarding listings")
    bot_p.add_argument("--proxy", default=None, help="Mobile proxy URL (e.g. http://user:pass@ip:port)")
    bot_p.add_argument("--proxy-change-url", default=None, help="Mobile proxy IP rotation URL")
    bot_p.add_argument("--playwright", action="store_true", help="Enable Playwright Chromium cookie harvesting")
    bot_p.add_argument("--workers", type=int, default=4, help="Parallel worker threads for card enrichment")
    bot_p.add_argument("-n", "--limit", type=int, default=30, help="Default item limit per search")

    # Item command
    item_p = subparsers.add_parser("item", help="Fetch detailed info for a single item")
    item_p.add_argument("item_id", type=int, help="Avito numeric item ID")
    item_p.add_argument("-o", "--output", help="Save output to JSON file")
    item_p.add_argument("--proxy", default=None, help="Mobile proxy URL")
    item_p.add_argument("--proxy-change-url", default=None, help="Mobile proxy IP rotation URL")

    # Drops command
    drops_p = subparsers.add_parser("drops", help="Show all tracked items whose price has dropped")
    drops_p.add_argument("--db", default="avito_prices.db", help="Path to SQLite price database")

    # Config command (100% compatible with parser_avito config.toml)
    cfg_p = subparsers.add_parser("config", help="Run full parser_avito workflow from a config.toml file")
    cfg_p.add_argument("path", nargs="?", default="config.toml", help="Path to config.toml (default: config.toml)")

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "config":
        client = AvitoClient.from_config(args.path)
        items = client.run_config(args.path)
        print(f"[✓] Finished config run: collected {len(items)} items.")
        return 0

    if args.command == "bot":
        from avito_sdk.telegram import AvitoTelegramBot
        bot = AvitoTelegramBot(
            bot_token=args.tg_token,
            proxy=args.proxy,
            proxy_change_url=args.proxy_change_url,
            channel_id=args.channel_id,
            workers=args.workers,
            limit=args.limit,
            use_playwright_cookies=args.playwright,
        )
        bot.run_polling()
        return 0

    if args.command == "search":
        print(f"[*] Searching for '{args.query}' in '{args.region}' (limit={args.limit})...")
        has_tg = bool(args.tg_token and args.tg_chat_id)
        excel_out = args.output if (args.output and args.output.lower().endswith(".xlsx")) else None
        client = AvitoClient(
            proxy=args.proxy,
            proxy_change_url=args.proxy_change_url,
            use_playwright_cookies=args.playwright,
            tg_token=args.tg_token,
            tg_chat_id=args.tg_chat_id,
        )
        items = list(
            client.search(
                query=args.query,
                region=args.region,
                min_price=args.min_price,
                max_price=args.max_price,
                enrich_details=args.enrich,
                max_workers=args.workers,
                notify_telegram=has_tg,
                telegram_progress=has_tg,
                show_progress=True,
                excel_path=excel_out,
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
            if suffix == ".xlsx" and not excel_out:
                to_excel(items, out_path)
            elif suffix == ".csv":
                to_csv(items, out_path)
            elif suffix != ".xlsx":
                to_json(items, out_path)
            print(f"[✓] Saved {len(items)} items to {out_path}")

    elif args.command == "item":
        print(f"[*] Fetching item {args.item_id}...")
        client = AvitoClient(proxy=args.proxy, proxy_change_url=args.proxy_change_url)
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
