# avito-sdk

[ 🇬🇧 English ] | [ 🇷🇺 Документация на русском ](README_RU.md)

[![PyPI Version](https://img.shields.io/pypi/v/avito-sdk.svg?color=blue)](https://pypi.org/project/avito-sdk/)
[![Python Versions](https://img.shields.io/pypi/pyversions/avito-sdk.svg)](https://pypi.org/project/avito-sdk/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Conda Forge](https://img.shields.io/badge/conda--forge-PR%20%2335071-orange.svg)](https://github.com/conda-forge/staged-recipes/pull/35071)
[![eminsk PPA](https://img.shields.io/badge/APT%20PPA-python3--avito--sdk-blueviolet.svg)](https://eminsk.github.io/ppa/)
[![Free-Threaded No-GIL](https://img.shields.io/badge/PEP%20703-No--GIL%20Ready-brightgreen)](https://peps.python.org/pep-0703/)
[![CI](https://github.com/eminsk/avito-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/eminsk/avito-sdk/actions)

> **High-performance headless Avito scraping and data extraction SDK for Python.**  
> Developed by core contributor to [`Duff89/parser_avito`](https://github.com/Duff89/parser_avito).

---

## 🚀 Key Features

- 🚀 **100% Headless & Lightweight**: Zero desktop window / GUI dependencies (No Tkinter, CustomTkinter, or Flet). Runs out of the box in Linux, Docker, AWS, Raspberry Pi, Windows, and macOS.
- ⚡ **Dual Sync & Async API**: `AsyncAvitoClient` for high-throughput asyncio backends (Aiogram 3, FastAPI, aiohttp) and `AvitoClient` for scripts and automation.
- 📉 **Real-time Price Tracking (PR #334 / Issue #214)**: Built-in `PriceTracker` engine with SQLite persistence, historical logs, and automatic price drop calculation (`item.price_drop`).
- 👤 **Seller Details & Store Slugs (PR #334 / Issue #333)**: Extracts verified seller name (`seller_name`) and seller profile/brand ID (`seller_id`).
- 📋 **Deep Parameters & Specs Parsing (PR #337 / Issue #335)**: Extracts full item characteristics («О помещении», floor, area, auto specs, electronics) from Beduin mobile scenarios and Mobile API.
- 📝 **Full Multiline Descriptions (PR #329 / Issue #305)**: Extracts complete uncut descriptions from JSON scenarios and Schema.org microdata.
- 🛡️ **Anti-Bot TLS Fingerprinting**: Browser impersonation (Chrome/Safari TLS fingerprints) via `curl_cffi` with transparent fallback to standard HTTP transport.
- 📊 **Multi-Format Exporters**: Direct export to styled Excel (`.xlsx` with automatic column sizing via openpyxl), CSV, JSON, JSONL, and Pandas/Polars `DataFrame`.
- 💻 **Command-Line Interface (CLI)**: Built-in CLI commands `avito-sdk` and `avito-parser` for instant terminal searches and exports.
- 🌐 **Universal Python Support**: Full compatibility with Python 3.8 – 3.16+, Free-Threaded No-GIL (PEP 703: 3.13t–3.15t), and PyPy.

---

## 📦 Installation

```bash
# Standard installation via PyPI
pip install avito-sdk

# With anti-bot TLS impersonation (recommended)
pip install "avito-sdk[tls]"

# Full installation (Excel, TLS, Async, DataFrames)
pip install "avito-sdk[all]"
```

### Via Debian / Ubuntu APT (eminsk PPA)
```bash
curl -sS https://eminsk.github.io/ppa/setup.sh | sudo bash
sudo apt install python3-avito-sdk
```

Or via Conda / Mamba:
```bash
conda install -c conda-forge avito-sdk
```

---

## ⚡ Quickstart

### 1. Synchronous Search

```python
from avito_sdk import AvitoClient

client = AvitoClient()

# Search laptops in Moscow with price filter
for item in client.search("thinkpad", region="moskva", max_price=80000, limit=10):
    print(f"[{item.id}] {item.title} — {item.price:,} ₽ | Seller: {item.seller_name}")
    if item.has_price_changed:
        print(f"  🔥 Price drop detected! Was {item.old_price:,} ₽ (Drop: {item.price_drop:,} ₽)")
```

---

### 2. Asynchronous Streaming (Telegram Bots & FastAPI)

```python
import asyncio
from avito_sdk import AsyncAvitoClient

async def main():
    async with AsyncAvitoClient() as client:
        async for item in client.search("rtx 4070", region="sankt-peterburg", limit=20):
            print(f"Found: {item.title} ({item.price:,} ₽) -> {item.url}")

asyncio.run(main())
```

---

### 3. Extracting Detailed Parameters & Specs (PR #337)

```python
from avito_sdk import AvitoClient

client = AvitoClient()

# Fetch rich item card with all specs
item = client.get_item(1234567890)

print("Title:", item.title)
print("Price:", item.price)
print("Seller:", item.seller_name)
print("Views:", f"{item.total_views} total, {item.today_views} today")

print("\nParameters (PR #337):")
for param_name, param_val in item.params.items():
    print(f"  • {param_name}: {param_val}")

print("\nDescription (PR #329):")
print(item.description)
```

---

### 4. Tracking Price Drops (PR #334)

```python
from avito_sdk import AvitoClient

client = AvitoClient(tracker_db="prices.db")

# Scrape listings with automated price tracking
items = list(client.search("iPhone 15 Pro", region="moskva", limit=50))

# Query recorded price drops:
drops = client.tracker.get_price_drops()
for drop in drops:
    diff = drop["initial_price"] - drop["current_price"]
    print(f"📉 Deal! {drop['title']}: {drop['initial_price']:,} -> {drop['current_price']:,} ₽ (-{diff:,} ₽)")
```

---

### 5. Export to Excel, JSON & Pandas

```python
from avito_sdk import AvitoClient, to_excel, to_json, to_dataframe

client = AvitoClient()
items = list(client.search("PlayStation 5", limit=30, enrich_details=True))

# 1. Styled Excel spreadsheet with auto-width columns
to_excel(items, "ps5_listings.xlsx")

# 2. JSON Lines for data pipelines and ML
to_json(items, "ps5_listings.json")

# 3. Pandas DataFrame
df = to_dataframe(items)
print(df[["id", "title", "price", "seller_name"]].head())
```

---

### 6. 🌐 Mobile Proxies & Multithreading (Mandatory for High-Speed Scraping)

> [!IMPORTANT]
> **Using a Mobile Proxy (`proxy` + `proxy_change_url`) is mandatory when running multithreaded (`max_workers > 1`), high-concurrency async, or deep card scraping (`enrich_details=True`)!**  
> Avito's anti-fraud firewall aggressively rate-limits (`429`) and bans (`403`) standard server/datacenter IP addresses under parallel load. With a mobile proxy and IP rotation URL configured, `avito-sdk` automatically rotates the operator IP whenever a block is detected and continues scraping seamlessly without data loss.

```python
from avito_sdk import AvitoClient

# Initialize client with Mobile Proxy and automatic IP rotation URL
client = AvitoClient(
    proxy="http://username:password@proxy.example.com:8000",
    proxy_change_url="https://changeip.mobileproxy.space/?proxy_key=YOUR_KEY",
)

# Run multithreaded card enrichment (8 parallel threads) safely via mobile proxy
items = list(
    client.search(
        query="коммерческая недвижимость",
        region="moskva",
        enrich_details=True,  # Fetches full params («О помещении»), views & description
        max_workers=8,        # Parallel threads (requires mobile proxy!)
        limit=100,
    )
)
```

---

## 🖥️ Command-Line Interface (CLI)

The package provides `avito-sdk` and `avito-parser` executable scripts:

```bash
# Search and save directly to Excel:
avito-sdk search "MacBook M2" --region moskva --max-price 90000 --output macbooks.xlsx

# High-speed multithreaded search with Mobile Proxy and deep parameter extraction:
avito-sdk search "помещение" --region moskva --enrich --workers 5 \
  --proxy "http://user:pass@ip:port" \
  --proxy-change-url "https://changeip.mobileproxy.space/?proxy_key=..." \
  --output premises.xlsx

# Inspect single item card:
avito-sdk item 3854129841

# View all recorded price drops:
avito-sdk drops --db prices.db
```

---

## 🛠️ Comparison: `parser_avito` (GUI) vs `avito-sdk` (Library)

| Feature | Duff89/parser_avito | **avito-sdk** |
| :--- | :---: | :---: |
| Target Audience | End-users wanting a desktop GUI app | Developers, bots, ML pipelines & servers |
| Graphical Interface | ✅ CustomTkinter / Tkinter GUI | ❌ None (100% Headless) |
| Server / Docker / VPS | Requires virtual display (Xvfb) | ✅ Native headless out of the box |
| Async API (`asyncio`) | ❌ No | ✅ `AsyncAvitoClient` |
| Telegram Bots (Aiogram) | Difficult | ✅ `pip install avito-sdk` |
| Price Tracking (PR #334) | ✅ Supported | ✅ Built-in `PriceTracker` engine |
| Parameters Parsing (PR #337) | ✅ Supported | ✅ Beduin & Mobile API parser |
| Python 3.8 – 3.16+ | 3.11 – 3.13 | ✅ 3.8 – 3.16, Free-Threaded No-GIL, PyPy |

---

## 📄 License

Distributed under the **MIT** License.  
Author: **eminsk** ([M_N_N@tut.by](mailto:M_N_N@tut.by))
