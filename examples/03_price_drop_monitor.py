"""
03_price_drop_monitor.py - Monitor historical price changes using PriceTracker.
"""

from avito_sdk import AvitoClient


def main():
    # Tracker database stores history across application restarts
    client = AvitoClient(tracker_db="prices_history.db")

    print("[*] Checking PlayStation 5 listings...")
    items = list(client.search("PlayStation 5", region="moskva", limit=20))

    drops = client.tracker.get_price_drops()
    if not drops:
        print("[-] No price drops recorded yet. Run the script periodically to accumulate history.")
    else:
        print(f"[+] Found {len(drops)} listings with lower prices:")
        for drop in drops:
            savings = drop["initial_price"] - drop["current_price"]
            print(
                f"  - [{drop['item_id']}] {drop['title'][:40]}\n"
                f"    {drop['initial_price']:,} ₽ -> {drop['current_price']:,} ₽ (Скидка: {savings:,} ₽)\n"
            )


if __name__ == "__main__":
    main()
