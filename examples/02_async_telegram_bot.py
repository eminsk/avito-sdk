"""
02_async_telegram_bot.py - Integration example for asynchronous Telegram bots (Aiogram 3 / Telethon).
"""

import asyncio
from avito_sdk import AsyncAvitoClient


async def monitor_avito_query(query: str, max_price: int, region: str = "moskva"):
    """
    Simulated background task running in an Aiogram bot handler.
    Periodically checks for newly published or price-reduced items.
    """
    async with AsyncAvitoClient(tracker_db="bot_prices.db") as client:
        print(f"[*] Monitoring Avito for '{query}'...")
        async for item in client.search(
            query=query,
            region=region,
            max_price=max_price,
            limit=5,
        ):
            if item.has_price_changed:
                msg = (
                    f"🔥 СКИДКА НА ТОВАР!\n"
                    f"📦 {item.title}\n"
                    f"💰 Новая цена: {item.price:,} ₽ (было: {item.old_price:,} ₽)\n"
                    f"📉 Выгода: -{item.price_drop:,} ₽\n"
                    f"👤 Продавец: {item.seller_name}\n"
                    f"🔗 {item.url}"
                )
                print(f"[Telegram Alert]\n{msg}\n")
            else:
                print(f"[Item Found] [{item.id}] {item.title[:40]} - {item.price:,} ₽")


if __name__ == "__main__":
    asyncio.run(monitor_avito_query("rtx 4070", max_price=65000))
