"""
01_simple_search.py - Basic synchronous search with avito-sdk.
"""

from avito_sdk import AvitoClient


def main():
    client = AvitoClient()

    print("[*] Searching for laptops under 70,000 RUB in Moscow...")
    for item in client.search("ноутбук thinkpad", region="Москва", max_price=70000, limit=10):
        print(f"[{item.id}] {item.title}")
        print(f"  Цена: {item.price:,} ₽")
        print(f"  Продавец: {item.seller_name or 'Частное лицо'}")
        print(f"  Ссылка: {item.url}\n")


if __name__ == "__main__":
    main()
