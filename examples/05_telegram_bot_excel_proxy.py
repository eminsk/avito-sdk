"""
05_telegram_bot_excel_proxy.py - Production Avito Parser workflow:
1. Mobile Proxy with automatic IP rotation (403/429 bypass)
2. Playwright Chromium cookie harvesting ('ft' cookie + stealth JS)
3. Live visual progress bar ([████████░░░░░░░░] 50%) in Telegram & terminal
4. Automatic Excel (.xlsx) export and direct file upload to Telegram chat/channel
5. Interactive Telegram Bot controller (/search, /proxy, /workers, /playwright)
"""

from avito_sdk import AvitoClient, AvitoTelegramBot


def run_parser_to_telegram_and_excel():
    """
    Mode 1: Scrape Avito with mobile proxy + Playwright cookies,
    stream live progress bar & cards to Telegram channel, and upload final Excel (.xlsx).
    """
    client = AvitoClient(
        proxy="http://user:pass@ip:port",
        proxy_change_url="https://changeip.mobileproxy.space/?proxy_key=YOUR_KEY",
        use_playwright_cookies=True,  # Automatically harvests 'ft' cookie via Playwright Chromium
        tg_token="123456:ABC-DEF_YOUR_BOT_TOKEN",
        tg_chat_id="-1001234567890",  # Telegram channel or chat ID
        tracker_db="avito_prices.db",
    )

    items = list(
        client.search(
            query="аренда склада",
            region="moskva",
            enrich_details=True,       # Extracts full params («О помещении») & seller name
            max_workers=4,             # Multithreaded parsing over mobile proxy
            limit=50,
            notify_telegram=True,      # Sends formatted cards with 📉 Old ➔ New price
            telegram_progress=True,    # Updates live [████████░░░░░░░░] 50% bar in Telegram
            show_progress=True,        # Updates progress bar in terminal
            excel_path="avito_warehouses.xlsx",  # Saves styled .xlsx AND uploads it to Telegram!
        )
    )
    print(f"Done! Exported {len(items)} items to avito_warehouses.xlsx and uploaded to Telegram.")
    client.close()


def run_interactive_telegram_bot():
    """
    Mode 2: Start an interactive Telegram bot controller (like parser_avito).
    Send any search query or Avito URL to the bot in Telegram to see a live
    progress bar and receive the generated .xlsx file right in the chat!
    """
    bot = AvitoTelegramBot(
        bot_token="123456:ABC-DEF_YOUR_BOT_TOKEN",
        proxy="http://user:pass@ip:port",
        proxy_change_url="https://changeip.mobileproxy.space/?proxy_key=YOUR_KEY",
        channel_id="-1001234567890",
        workers=4,
        use_playwright_cookies=True,
    )
    bot.run_polling()


if __name__ == "__main__":
    print("See functions run_parser_to_telegram_and_excel() and run_interactive_telegram_bot()")
