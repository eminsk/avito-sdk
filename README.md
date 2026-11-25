<p align="center">
  <img src="assets/logo.png" width="140" alt="Avito SDK Pro Logo">
</p>
<h1 align="center">Avito SDK Pro</h1>
<p align="center">
  <b>High-performance Python SDK & Modern Desktop GUI for Avito scraping, real-time monitoring, and price sniping.</b>
</p>

<p align="center">
  <b>🇬🇧 English</b> •
  <a href="https://github.com/eminsk/avito-sdk/blob/main/README_RU.md">🇷🇺 Документация на русском</a>
</p>

[![Release Version](https://img.shields.io/badge/release-v0.4.5-0969da.svg?style=flat&logo=github)](https://github.com/eminsk/avito-sdk/releases/tag/v0.4.5)
[![Glama MCP Server](https://glama.ai/mcp/servers/eminsk/avito-sdk/badges/score.svg)](https://glama.ai/mcp/servers/eminsk/avito-sdk)
[![Free 3h Proxy Trial](https://img.shields.io/badge/Mobile_Proxy-Free_3h_Trial_(No_VPN)-00C853?style=flat&logo=cloudflare&logoColor=white)](https://mobileproxy.rent/user.html?free&p=279117)
[![PyPI Version](https://img.shields.io/pypi/v/avito-sdk.svg?style=flat&logo=pypi&color=blue)](https://pypi.org/project/avito-sdk/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/avito-sdk.svg?style=flat&logo=pypi)](https://pypi.org/project/avito-sdk/)
[![Python Versions](https://img.shields.io/badge/python-3.8_--_3.16+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://pypi.org/project/avito-sdk/)
[![Free-Threaded No-GIL](https://img.shields.io/badge/No--GIL-3.13t%20--%203.16t-brightgreen?style=flat)](https://peps.python.org/pep-0703/)
[![PyPy](https://img.shields.io/badge/PyPy-3.8_--_3.12-yellow.svg?style=flat&logo=pypy)](https://pypy.org/)
[![Pure Native HTTP](https://img.shields.io/badge/Browser-Zero--Browser_%7C_Pure_Native_HTTP-informational?style=flat)](https://github.com/eminsk/avito-sdk)
[![Tests](https://img.shields.io/badge/tests-84%20passed-2ea44f.svg?style=flat&logo=pytest&logoColor=white)](https://github.com/eminsk/avito-sdk)
[![Desktop GUI](https://img.shields.io/badge/Desktop_GUI-CustomTkinter-blueviolet.svg?style=flat)](https://github.com/eminsk/avito-sdk#desktop-gui)
[![Telegram Channel](https://img.shields.io/badge/Telegram_Channel-@avito__sdk__pro-26A5E4?style=flat&logo=telegram&logoColor=white)](https://t.me/avito_sdk_pro)
[![Telegram Bot](https://img.shields.io/badge/Telegram_Bot-@eminsk__avito__bot-2CA5E0?style=flat&logo=telegram&logoColor=white)](https://t.me/eminsk_avito_bot)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat)](https://opensource.org/licenses/MIT)

> **High-performance Avito scraping and data extraction SDK for Python.**  
> Production-grade, autonomous Avito scraping and data extraction engine for Python.

> ### 🤝 Community, Issues & Support
> - 🌐 **Getting 429 / 403 without a proxy?** Claim a [3-Hour Free Mobile Proxy Trial](https://mobileproxy.rent/user.html?free&p=279117) ([MobileProxy Portal](https://mobileproxy.rent/?p=279117) — works in Russia without VPN).
> - 📢 **Releases, proxy setups & community chat:** Join our [Telegram Channel (@avito_sdk_pro)](https://t.me/avito_sdk_pro).
> - 🐛 **Found a bug or parser issue?** Please [Open an Issue](https://github.com/eminsk/avito-sdk/issues) — parser layout fixes and bug reports are prioritized!
> - 💬 **Questions, proxy setups, or feature ideas?** Join our [GitHub Discussions](https://github.com/eminsk/avito-sdk/discussions).
> - ⭐ **Find this SDK useful?** Give it a star on GitHub — it helps more developers discover the library!
> - ☕ **Support development (USDT TRC-20):** `TDVbEdnpgNgoAhNcn1EwXxWHiR3RKLit5P` ([Verify on TronScan](https://tronscan.org/#/address/TDVbEdnpgNgoAhNcn1EwXxWHiR3RKLit5P))

<p align="center">
  <img src="docs/images/gui_monitor.png" alt="Avito SDK Pro Desktop GUI — Monitoring & Filters" width="820">
</p>

---

## 🚀 Key Features

- 🖥️ **Modern Desktop GUI (Avito SDK Pro)**: Dark-themed `CustomTkinter` desktop app with live listing cards, instant deal sniper buttons, 1-click proxy verification, and Excel export.
- 📦 **Standalone Windows Executable (`.exe`)**: 1-click launch on Windows 10/11 without needing Python, virtual environments, or terminal commands.
- 🌐 **Flexible Proxy Architecture**: Supports cheap static Datacenter proxies, Pay-As-You-Go mobile proxies (AstroProxy, Asocks), and dedicated mobile 4G modems with API rotation (MobileProxy.space).
- ⚡ **Dual Sync & Async API**: `AsyncAvitoClient` for high-throughput asyncio backends (Aiogram 3, FastAPI, aiohttp) and `AvitoClient` for scripts and automation.
- 📉 **Real-time Price Tracking**: Built-in `PriceTracker` engine with SQLite persistence, historical logs, and automatic price drop calculation (`item.price_drop`).
- 👤 **Seller Details & Store Slugs**: Extracts verified seller name (`seller_name`) and seller profile/brand ID (`seller_id`).
- 📋 **Deep Parameters & Specs Parsing**: Extracts full item characteristics («О помещении», floor, area, auto specs, electronics) from Beduin mobile scenarios and Mobile API.
- 📝 **Full Multiline Descriptions**: Extracts complete uncut descriptions from JSON scenarios and Schema.org microdata.
- 🛡️ **Anti-Bot TLS Fingerprinting**: Browser impersonation (Chrome/Safari TLS fingerprints) via `curl_cffi` with transparent fallback to standard HTTP transport.
- 📊 **Multi-Format Exporters**: Direct export to styled Excel (`.xlsx` with automatic column sizing via openpyxl), CSV, JSON, JSONL, and Pandas/Polars `DataFrame`.
- 💻 **Command-Line Interface (CLI)**: Built-in CLI commands `avito-sdk` and `avito-parser` for instant terminal searches and exports.
- 🌐 **Universal Python Support**: Full compatibility with Python 3.8 – 3.16+, Free-Threaded No-GIL (PEP 703: Python 3.13t – 3.16t), and PyPy (PyPy 3.8 – 3.12).

---

## 🖥️ Desktop GUI (Avito SDK Pro)

For users who want instant real-time monitoring and sniping without writing code:

### 1. Download Standalone Windows App (No Python Required):
1. Download **[AvitoSDK_Pro_Windows_x64.zip](https://github.com/eminsk/avito-sdk/releases/latest)** from [Releases](https://github.com/eminsk/avito-sdk/releases).
2. Unpack and launch `AvitoSDK_Pro.exe`.
3. Pre-configured search links and price limits are loaded automatically out of the box!

### 2. Launch via Python / PyPI:
```bash
pip install "avito-sdk[gui]"
avito-gui
```
Or from source:
```bash
python run_gui.py
# or double-click run_gui.bat
```

### Desktop App Features:
- 🔍 **Monitoring Tab**: Monitor multiple Avito catalog URLs concurrently with price range and keyword filtering.
- ⚡ **Live Feed Tab**: Real-time listing stream with clickable *"Open on Avito ↗"* buttons for immediate purchase.
- 📊 **Excel Export**: Export the live feed into beautifully formatted `.xlsx` spreadsheets with active hyperlinks.
- 🌐 **Proxy Tab**: 1-click proxy connectivity test with ping latency measurement in milliseconds.
- ✈️ **Telegram Tab**: Instant deal notification dispatch with support for dedicated Telegram proxies to bypass regional ISP throttling.
- 🐛 **Bug Tracker Integration**: Instant 1-click access to the [GitHub Issue Tracker](https://github.com/eminsk/avito-sdk/issues).

<p align="center">
  <img src="docs/images/gui_feed.png" alt="Avito SDK Pro Desktop GUI — Live Feed & Price-Drop Tracking" width="820">
</p>

---

## 📦 Developer Installation

```bash
# Core package
pip install avito-sdk

# With Desktop GUI
pip install "avito-sdk[gui]"

# Full installation (GUI, Excel, TLS, Async, DataFrames)
pip install "avito-sdk[all]"
```

---

## 🌟 What's New in Version 0.4.4

- 🛡️ **Bundled Native Chrome TLS (`curl_cffi 0.16.3`) in Windows `.exe`**: Standalone GUI builds now run on Python 3.12 with built-in Chrome TLS fingerprinting and a live header status badge.
- 🔑 **`spfa.pro` Cookie Auto-Refresh & Phone API**: Updated `ParsePhone` to `https://spfa.pro/api/phone/` and added an optional `spfa_api_key` field in the Proxy tab for automated cookie recovery on static server proxies.
- 🎨 **Cleaner Desktop UI & Price-Drop Alerts**: Added explicit labels for all filter controls, fixed Telegram notification toggles, enabled SQLite-backed `seen_prices` price-drop notifications, and aligned MobileProxy links to the VPN-free `mobileproxy.rent` mirror (`/?p=279117` & 3h free trial).
- 💎 **Dynamic Versioning & Packaging Parity**: Synchronized dynamic version reporting across the GUI, MCP server, Debian package, Conda recipe, and PyPI README.

---

## 🌐 Choosing & Configuring Proxies

Avito SDK Pro adapts to your budget and monitoring workload:

### 1. Datacenter / Server Static Proxies (IPv4 / SOCKS5 — ~$0.50/mo)
* **Best for:** Low-frequency sniping of 1–3 search links with intervals of 25–45 seconds.
* **Providers:** Proxy-Seller, SpaceProxy, PX6, etc.
* **Connection string:** `http://user:pass@host:port` or `socks5://user:pass@host:port`.
* **Tip:** Keep `max_workers=1` and interval at 30 seconds.

### 2. Pay-As-You-Go Mobile Proxies (~$2–$3 per 1 GB)
* **Best for:** Cost-effective private monitoring **without paying $25–$30/mo for a dedicated modem**.
* **Providers:** [AstroProxy](https://astroproxy.com) or [Asocks](https://asocks.com).
* **Cost efficiency:** 1 GB costs ~$2.50. Because Avito SDK only requests lightweight HTML/JSON without downloading images (~10–15 KB per request), **1 GB provides over 70,000 queries** — enough for a full month of continuous monitoring every 30 seconds!
* **Rotation:** IP rotates seamlessly on the provider side.

### 3. Dedicated 4G/LTE Mobile Modems with API Rotation
* **Best for:** High-volume commercial scraping of hundreds of pages and thousands of listings in 4–16 parallel workers.
* **Recommended provider:** [MobileProxy.space / mobileproxy.rent](https://mobileproxy.rent/?p=279117) ([Free 3-Hour Trial](https://mobileproxy.rent/user.html?free&p=279117)).
* **Connection:**
  ```python
  client = AvitoClient(
      proxy="http://login:password@proxy-domain.space:port",
      proxy_change_url="https://changeip.mobileproxy.space/?proxy_key=YOUR_KEY",
  )
  ```

---

## ⚡ Quickstart (Minimal 3-line code without boilerplate)

### 1. Installation:
```bash
uv add avito-sdk
# or: pip install avito-sdk
```

### 2. Scraping without `main()` functions:
```python
from avito_sdk import AvitoClient

# Initialize client with your mobile proxy
client = AvitoClient(
    proxy="http://user:password@host:port",
    proxy_change_url="https://changeip.mobileproxy.space/?proxy_key=...",
    modems_count=1,
)

# 1. Search by query or direct Avito URL
for item in client.search("RTX 4090", limit=10, show_progress=True):
    print(f"{item.title} | {item.price:,} ₽ | {item.url}")
    print(f"  Seller: {item.seller_name} | Views: {item.total_views}")

# 2. Or scrape catalog link directly into styled Excel (.xlsx) report
client.scrape_url(
    url="https://www.avito.ru/moskva/noutbuki?cd=1",
    limit=30,
    enrich_details=True,
    excel_path="noutbuki.xlsx",
)
```

---

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

### 6. 🌐 Mobile Proxies & Multithreading: MobileProxy.space Integration

> [!IMPORTANT]
> **Using a Mobile Proxy (`proxy` + `proxy_change_url` / `mobileproxy_key`) is mandatory when running multithreaded (`max_workers > 1`), high-concurrency async, or deep card scraping (`enrich_details=True`)!**  
> Avito's anti-fraud firewall aggressively rate-limits (`429`) and bans (`403`) standard server/datacenter IP addresses under parallel load. Real 4G/LTE SIM cards share IP pools with millions of cellular subscribers, making them immune to subnet-level bans.

> 📱 **Recommended Provider**: [MobileProxy.space / mobileproxy.rent](https://mobileproxy.rent/?p=279117) *(Get a [Free 3-Hour Trial](https://mobileproxy.rent/user.html?free&p=279117))*  
> Dedicated 4G/LTE mobile proxies across real SIM carriers (MTS, Megafon, Beeline, Tele2) with instant URL/API IP rotation.

#### Option A: One-line setup via `mobileproxy_key`
```python
from avito_sdk import AvitoClient

# Pass your proxy address and rotation key from the MobileProxy.space dashboard
client = AvitoClient(
    proxy="http://username:password@proxy-domain.space:8000",
    mobileproxy_key="YOUR_ROTATION_KEY",  # avito-sdk builds changeip.mobileproxy.space automatically
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

#### Option B: Standalone IP rotation via `MobileProxySpace`
```python
from avito_sdk import MobileProxySpace

mps = MobileProxySpace.from_key("YOUR_ROTATION_KEY")
res = mps.rotate_ip(wait_reconnect=True)
print("New public IP:", res.get("new_ip"))
```

#### Option C: From Terminal CLI
```bash
avito-sdk search "ноутбук" --proxy "http://user:pass@host:port" --mobileproxy-key "YOUR_KEY" --enrich --workers 4
```

---

### 7. 🌐 Mobile Proxy Auto-Rotation + Telegram Progress Bar + Excel Upload

Pure native HTTP scraping with automatic cellular IP rotation:

```python
from avito_sdk import AvitoClient

client = AvitoClient(
    proxy="http://user:pass@ip:port",
    proxy_change_url="https://changeip.mobileproxy.space/?proxy_key=YOUR_KEY",
    tg_token="123456:ABC-DEF_BOT_TOKEN",
    tg_chat_id="-1001234567890",  # Telegram channel or chat ID
)

# Scrapes with mobile proxy, updates a live progress bar in Telegram,
# sends formatted cards (📉 Old ➔ New price), saves styled .xlsx, and uploads the .xlsx to Telegram!
items = list(
    client.search(
        query="аренда склада",
        region="moskva",
        enrich_details=True,
        max_workers=4,
        limit=50,
        notify_telegram=True,
        telegram_progress=True,
        show_progress=True,
        excel_path="warehouses.xlsx",
    )
)
```

Live status message displayed in Telegram during scraping:
```text
⏳ Парсинг Авито: аренда склада
🟩🟩🟩🟩🟩⬜⬜⬜⬜⬜ 50% (25/50)
🌐 Мобильный прокси: Активен (ротаций IP: 2)
🧵 Потоков: 4  |  📉 Снижений цен: 3
```

---

### 8. 🤖 Interactive Telegram Bot Controller (`AvitoTelegramBot`)

Control parsing directly from Telegram (`/search`, `/proxy`, `/workers`), watch a live updating progress bar (`🟩🟩🟩🟩🟩⬜⬜⬜⬜⬜ 50%`), and receive the `.xlsx` report right in the chat:

```python
from avito_sdk import AvitoTelegramBot

bot = AvitoTelegramBot(
    bot_token="123456:ABC-DEF_BOT_TOKEN",
    proxy="http://user:pass@ip:port",
    proxy_change_url="https://changeip.mobileproxy.space/?proxy_key=YOUR_KEY",
    workers=4,
)
bot.run_polling()
```

---

## 🖥️ Command-Line Interface (CLI)

The package provides `avito-sdk` and `avito-parser` executable scripts:

```bash
# Search and save directly to Excel:
avito-sdk search "MacBook M2" --region moskva --max-price 90000 --output macbooks.xlsx

# High-speed multithreaded search with Mobile Proxy, Telegram progress & Excel upload:
avito-sdk search "помещение" --region moskva --enrich --workers 5 \
  --proxy "http://user:pass@ip:port" \
  --proxy-change-url "https://changeip.mobileproxy.space/?proxy_key=..." \
  --tg-token "123456:ABC..." --tg-chat-id "-1001234567890" \
  --output premises.xlsx

# Launch interactive Telegram Bot Controller (manage proxy, workers & receive .xlsx in Telegram):
avito-sdk bot --tg-token "123456:ABC..." \
  --proxy "http://user:pass@ip:port" \
  --proxy-change-url "https://changeip.mobileproxy.space/?proxy_key=..." \
  --workers 4

# Run directly from a parser_avito config.toml file:
avito-sdk config config.toml

# Inspect single item card:
avito-sdk item 3854129841

# View all recorded price drops:
avito-sdk drops --db prices.db

# Start Model Context Protocol (MCP) Server over stdio:
avito-mcp --proxy "http://user:pass@ip:port" --proxy-change-url "https://..."
```

---

## 🤖 Native MCP (Model Context Protocol) Server

[![eminsk/avito-sdk MCP server](https://glama.ai/mcp/servers/eminsk/avito-sdk/badges/score.svg)](https://glama.ai/mcp/servers/eminsk/avito-sdk)

**avito-sdk** includes a native, high-performance [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server (`avito-mcp` or `avito-sdk mcp`) communicating over JSON-RPC 2.0 `stdio` (listed on [Glama MCP](https://glama.ai/mcp/servers/eminsk/avito-sdk)).

It enables frontier AI assistants and agentic IDEs — **Google Antigravity**, **Anthropic Claude Code & Claude Desktop**, **Cursor IDE**, **OpenAI Codex**, and **Windsurf** — to autonomously search Avito, inspect item parameters («О помещении», авто, etc.), and monitor price drops.

### 🛠️ Exposed MCP Tools

| Tool | Description | Key Parameters |
| :--- | :--- | :--- |
| `avito_search` | Search Avito with deep filtering, price ranges, keywords & Excel/Telegram export | `query`, `region`, `min_price`, `max_price`, `limit`, `enrich_details`, `excel_path` |
| `avito_get_item` | Deep inspect a single item card (characteristics, full description, seller, views) | `item_id` |
| `avito_price_drops` | Query tracked listings with price drops or full price history for an item | `item_id` (optional) |

---

### 🚀 Integration Guides for AI IDEs & Agents

#### 1. 🪐 Google Antigravity (IDE & CLI)

**Via Antigravity CLI:**
```bash
agy mcp add avito -- avito-mcp --workers 2
```

**Or add to global `~/.gemini/config/mcp_config.json`:**
```json
{
  "mcpServers": {
    "avito": {
      "command": "avito-mcp",
      "args": ["--db", "avito_prices.db", "--workers", "2"],
      "env": {
        "AVITO_PROXY": "http://user:pass@ip:port",
        "AVITO_PROXY_CHANGE_URL": "https://changeip.mobileproxy.space/?proxy_key=YOUR_KEY"
      }
    }
  }
}
```

---

#### 2. ⚡ Anthropic Claude Code & Claude Desktop

**Claude Code CLI:**
```bash
claude mcp add avito avito-mcp -- --workers 2
```

**Claude Desktop (`claude_desktop_config.json`):**
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "avito": {
      "command": "avito-mcp",
      "args": ["--workers", "2"],
      "env": {
        "AVITO_PROXY": "http://user:pass@ip:port",
        "AVITO_PROXY_CHANGE_URL": "https://changeip.mobileproxy.space/?proxy_key=YOUR_KEY"
      }
    }
  }
}
```

---

#### 3. 🖱️ Cursor IDE

Create `.cursor/mcp.json` in your workspace root (or navigate to **Cursor Settings > Features > MCP > Add New MCP Server**):

```json
{
  "mcpServers": {
    "avito": {
      "command": "avito-mcp",
      "args": ["--workers", "2"],
      "env": {
        "AVITO_PROXY": "http://user:pass@ip:port",
        "AVITO_PROXY_CHANGE_URL": "https://changeip.mobileproxy.space/?proxy_key=YOUR_KEY"
      }
    }
  }
}
```

---

#### 4. 🧠 OpenAI Codex / ChatGPT / Windsurf / Roo Code

For **Windsurf** (`~/.codeium/windsurf/mcp_config.json`) or **VS Code Roo Code / Continue.dev**:

```json
{
  "mcpServers": {
    "avito": {
      "command": "avito-mcp",
      "args": ["--workers", "2"],
      "env": {
        "AVITO_PROXY": "http://user:pass@ip:port",
        "AVITO_PROXY_CHANGE_URL": "https://changeip.mobileproxy.space/?proxy_key=YOUR_KEY"
      }
    }
  }
}
```

---

### 💬 Example Prompts for AI Agents

Once connected, simply prompt your agent in natural language:
- *"Find 5 commercial real estate listings in Moscow under 500,000 RUB and export them to `real_estate.xlsx`."*
- *"Fetch full card details and characteristics for Avito item 4176185210 and summarize the seller's terms."*
- *"Check the local database for tracked price drops on graphics cards and report the top deals."*

---

## 🛠️ Comparison: Desktop GUI Parsers vs `avito-sdk` (Library)

| Feature | Desktop GUI Parsers | **avito-sdk** |
| :--- | :---: | :---: |
| Target Audience | End-users wanting a desktop GUI app | Developers, bots, ML pipelines & servers |
| Graphical Interface | ⚠️ Legacy Tkinter / Flet (Heavy, Freezes) | ✅ Modern Dark Desktop GUI (`avito-gui`, CustomTkinter) |
| Server / Docker / VPS | Requires virtual display (Xvfb) | ✅ Native headless out of the box |
| Async API (`asyncio`) | ❌ No | ✅ `AsyncAvitoClient` |
| Telegram Bots (Aiogram) | Difficult | ✅ `pip install avito-sdk` |
| Price History Tracking | ⚠️ Limited / External | ✅ Built-in `PriceTracker` engine |
| Extended Item Parameters | ⚠️ Limited / External | ✅ Beduin & Mobile API parser |
| Python 3.8 – 3.16+ | 3.11 – 3.13 | ✅ 3.8 – 3.16, Free-Threaded No-GIL (3.13t–3.16t), PyPy |

---

## 🌐 High-Performance Systems Ecosystem

`avito-sdk` is developed by [**@eminsk**](https://github.com/eminsk) as part of an open-source AI & systems engineering ecosystem:

* ⚡ [**NanoVector**](https://github.com/eminsk/nanovector) — Bare-metal C99/AVX2 vector search & episodic memory engine (~120KB) with Native MCP Server (`pip install nanovector`).
* 🧠 [**AgentJIT**](https://github.com/eminsk/agentjit) — Just-In-Time Compiler for AI Agent Trajectories with speculative de-optimization guards (`pip install agentjit`).
* ⚡ [**NanoGEMM**](https://github.com/eminsk/nanogemm) — Bare-metal AVX2+FMA SIMD matrix multiplication engine in ~100KB for sub-microsecond CPU inference (`pip install nanogemm`).
* 🖥️ [**NanoRecall**](https://github.com/eminsk/nanorecall) — 100% Private, offline desktop memory & semantic screen search engine powered by NanoVector (`pip install nanorecall`).
* 📈 [**yfinance-ta-patterns**](https://github.com/eminsk/yfinance-ta-patterns) — Candlestick & chart pattern scanner with AI Confluence Scoring, Backtesting, and Native MCP Server (`pip install yfinance-ta-patterns`).
* 📊 [**xlsx_vievers**](https://github.com/eminsk/xlsx_vievers) — Headless Excel formula engine (129+ functions), desktop spreadsheet viewer, SIMD SSE2 math, and Native MCP Server (`pip install xlsx-viewer-pro`).

---

## ☕ Support, Community & Donations

If you find this project valuable, encounter issues, or want to support ongoing development:

* ⭐ **Star the Repository**: If avito-sdk powers your scraping or bots, give us a star on GitHub — it helps more developers discover the SDK!
* 🐛 **Report Issues & Bugs**: Found a bug or did Avito update their layout? Please [open an Issue](https://github.com/eminsk/avito-sdk/issues) with reproduction details!
* 💬 **Join Discussions**: Have feature ideas, architecture questions, or general feedback? Start or join a thread in [GitHub Discussions](https://github.com/eminsk/avito-sdk/discussions)!
* 📢 **Telegram Channel & Chat**: Subscribe to [@avito_sdk_pro](https://t.me/avito_sdk_pro) for new `.exe` releases, proxy guides, and help in comments.
* ☕ **Donate (USDT TRC-20)**:  
  `TDVbEdnpgNgoAhNcn1EwXxWHiR3RKLit5P`  
  *(Network: TRON / TRC-20 | [Verify on TronScan](https://tronscan.org/#/address/TDVbEdnpgNgoAhNcn1EwXxWHiR3RKLit5P))*

[![GitHub Repo stars](https://img.shields.io/github/stars/eminsk/avito-sdk?style=social)](https://github.com/eminsk/avito-sdk)
[![Telegram Channel](https://img.shields.io/badge/Telegram-@avito__sdk__pro-26A5E4?logo=telegram&style=flat-square)](https://t.me/avito_sdk_pro)
[![GitHub Issues](https://img.shields.io/github/issues/eminsk/avito-sdk?color=red&style=flat-square)](https://github.com/eminsk/avito-sdk/issues)
[![GitHub Discussions](https://img.shields.io/badge/Discussions-Join_Community-blue?logo=github&style=flat-square)](https://github.com/eminsk/avito-sdk/discussions)
[![Donate USDT](https://img.shields.io/badge/Donate-USDT_(TRC20)-26A17B?style=flat-square&logo=tether&logoColor=white)](https://tronscan.org/#/address/TDVbEdnpgNgoAhNcn1EwXxWHiR3RKLit5P)

---

## 📄 License

Distributed under the **MIT** License.  
Author: **eminsk** ([M_N_Nik@yahoo.com](mailto:M_N_Nik@yahoo.com))
