# avito-sdk

[ 🇬🇧 English ] | [ 🇷🇺 Документация на русском ](https://github.com/eminsk/avito-sdk/blob/main/README_RU.md)


[![Release Version](https://img.shields.io/badge/release-v0.3.4-0969da.svg?style=flat&logo=github)](https://github.com/eminsk/avito-sdk/releases/tag/v0.3.4)
[![PyPI Version](https://img.shields.io/pypi/v/avito-sdk.svg?style=flat&logo=pypi&color=blue)](https://pypi.org/project/avito-sdk/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/avito-sdk.svg?style=flat&logo=pypi)](https://pypi.org/project/avito-sdk/)
[![Python Versions](https://img.shields.io/badge/python-3.8_--_3.16+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://pypi.org/project/avito-sdk/)
[![Free-Threaded No-GIL](https://img.shields.io/badge/No--GIL-3.13t%20--%203.16t-brightgreen?style=flat)](https://peps.python.org/pep-0703/)
[![PyPy](https://img.shields.io/badge/PyPy-3.11_%7C_3.12-yellow.svg?style=flat&logo=pypy)](https://pypy.org/)
[![Tests](https://img.shields.io/badge/tests-78%20passed-2ea44f.svg?style=flat&logo=pytest&logoColor=white)](https://github.com/eminsk/avito-sdk)
[![Telegram Bot](https://img.shields.io/badge/Telegram_Bot-@eminsk__avito__bot-2CA5E0?style=flat&logo=telegram&logoColor=white)](https://t.me/eminsk_avito_bot)
[![Mobile Proxy](https://img.shields.io/badge/Mobile_Proxy-Integrated_Auto--Failover-ff6b6b.svg?style=flat)](https://mobileproxy.space/)
[![MCP Server](https://img.shields.io/badge/MCP-Native_Stdio_Server-00a67e.svg?style=flat)](#native-mcp-model-context-protocol-server)
[![Excel Export](https://img.shields.io/badge/Export-.xlsx_Hyperlinks-217346?style=flat&logo=microsoftexcel&logoColor=white)](https://github.com/eminsk/avito-sdk)
[![CI](https://github.com/eminsk/avito-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/eminsk/avito-sdk/actions)
[![Conda-Forge](https://img.shields.io/conda/vn/conda-forge/avito-sdk.svg?style=flat&logo=condaforge)](https://anaconda.org/conda-forge/avito-sdk)
[![eminsk PPA](https://img.shields.io/badge/APT%20PPA-python3--avito--sdk-blueviolet.svg?style=flat)](https://eminsk.github.io/ppa/)
[![GitHub Stars](https://img.shields.io/github/stars/eminsk/avito-sdk?style=flat&logo=github)](https://github.com/eminsk/avito-sdk/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat)](https://opensource.org/licenses/MIT)
[![Donate USDT](https://img.shields.io/badge/Donate-USDT_(TRC20)-26A17B?style=flat&logo=tether&logoColor=white)](https://tronscan.org/#/address/TDVbEdnpgNgoAhNcn1EwXxWHiR3RKLit5P)

> **High-performance headless Avito scraping and data extraction SDK for Python.**  
> Developed by core contributor to [`Duff89/parser_avito`](https://github.com/Duff89/parser_avito).

> ### 🤝 Community, Issues & Support
> - 🐛 **Found a bug or parser issue?** Please [Open an Issue](https://github.com/eminsk/avito-sdk/issues) — parser layout fixes and bug reports are prioritized!
> - 💬 **Questions, proxy setups, or feature ideas?** Join our [GitHub Discussions](https://github.com/eminsk/avito-sdk/discussions).
> - ⭐ **Find this SDK useful?** Give it a star on GitHub — it helps more developers discover the library!
> - ☕ **Support development (USDT TRC-20):** `TDVbEdnpgNgoAhNcn1EwXxWHiR3RKLit5P` ([Verify on TronScan](https://tronscan.org/#/address/TDVbEdnpgNgoAhNcn1EwXxWHiR3RKLit5P))

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
# or with pixi
pixi add avito-sdk
```

---

## 🌟 What's New in Version 0.2.2

- 🔗 **Multi-Link Batch Scraping:** Send 2, 3, 4, or more Avito URLs in a single Telegram message to `@eminsk_avito_bot`. The bot sequentially scrapes each URL (up to 1,000+ items per link) and delivers individual Excel spreadsheets.
- 🚀 **Fast and Turbo Modes (up to 8–16 workers):** Accelerated concurrent scraping with adaptive micro-jitter to prevent WAF burst blocks.
- 🌐 **Strict Mobile Proxy Audit (`[ProxyAudit]`):** Automatic verification of purchased 4G/LTE mobile proxies with IP rotation at startup and in logs.
- 📝 **Persistent Rotating File Logging (`storage/logs/avito_bot.log`):** Automatic log rotation (10 MB × 5 archives), strictly excluded from Git (`.gitignore`).
- 🔒 **On-the-Fly Credential Masking (`PrivacyFilter`):** Sensitive proxy passwords and Telegram bot tokens are dynamically redacted from logs.
- 🧹 **Guaranteed Resource Cleanup (Zero Socket Leaks):** All HTTP sessions, sockets, and transport connections are always closed cleanly.

---

## 🌐 Mobile Proxy Requirements & Support Policy

> [!IMPORTANT]
> **Mandatory requirement for stable scraping & official support policy:**
> 1. Scraping Avito (especially for 100 to 1,000+ items, deep specs enrichment, and parallel workers) **strictly requires a purchased 4G/LTE mobile proxy with automatic IP rotation** (e.g. via [MobileProxy.space](https://mobileproxy.space/?p=32111)).
> 2. **Proxy Audit in Logs:** The SDK automatically audits proxy status at startup and logs an explicit `[ProxyAudit]` badge.
> 3. ⛔ **Support Policy:** **If scraping is run without a paid 4G mobile proxy with IP rotation (via direct home/datacenter IPs or non-rotating proxies), any issues regarding Avito WAF challenges, SmartCaptcha, HTTP 429 Too Many Requests, or 439 blocks ARE NOT CONSIDERED AND WILL NOT BE SUPPORTED.**
> 4. **Persistent Logging & Privacy:** Logs are automatically saved to `storage/logs/avito_bot.log` with file rotation (10 MB × 5 backups) and are strictly excluded from Git (`.gitignore`). Credentials and bot tokens are masked in real time via `PrivacyFilter`.
> 5. **Resource Cleanup:** All HTTP client sessions, sockets, and connections are always closed cleanly with zero leaks.

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

> 📱 **Recommended Provider**: [MobileProxy.space](https://mobileproxy.space/?p=279117) *(Get a [Free 3-Hour Trial](https://mobileproxy.space/user.html?free&p=279117))*  
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

### 7. 🎭 Playwright Cookie Harvesting + Telegram Progress Bar + Excel Upload

Install with Playwright browser support (`pip install "avito-sdk[all]"`):

```python
from avito_sdk import AvitoClient

client = AvitoClient(
    proxy="http://user:pass@ip:port",
    proxy_change_url="https://changeip.mobileproxy.space/?proxy_key=YOUR_KEY",
    use_playwright_cookies=True,  # Automatically harvests 'ft' cookie via headless Chromium + stealth JS
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

Control parsing directly from Telegram (`/search`, `/proxy`, `/workers`, `/playwright`), watch a live updating progress bar (`🟩🟩🟩🟩🟩⬜⬜⬜⬜⬜ 50%`), and receive the `.xlsx` report right in the chat:

```python
from avito_sdk import AvitoTelegramBot

bot = AvitoTelegramBot(
    bot_token="123456:ABC-DEF_BOT_TOKEN",
    proxy="http://user:pass@ip:port",
    proxy_change_url="https://changeip.mobileproxy.space/?proxy_key=YOUR_KEY",
    workers=4,
    use_playwright_cookies=True,
)
bot.run_polling()
```

---

## 🖥️ Command-Line Interface (CLI)

The package provides `avito-sdk` and `avito-parser` executable scripts:

```bash
# Search and save directly to Excel:
avito-sdk search "MacBook M2" --region moskva --max-price 90000 --output macbooks.xlsx

# High-speed multithreaded search with Mobile Proxy, Playwright cookies, Telegram progress & Excel upload:
avito-sdk search "помещение" --region moskva --enrich --workers 5 \
  --proxy "http://user:pass@ip:port" \
  --proxy-change-url "https://changeip.mobileproxy.space/?proxy_key=..." \
  --playwright \
  --tg-token "123456:ABC..." --tg-chat-id "-1001234567890" \
  --output premises.xlsx

# Launch interactive Telegram Bot Controller (manage proxy, workers & receive .xlsx in Telegram):
avito-sdk bot --tg-token "123456:ABC..." \
  --proxy "http://user:pass@ip:port" \
  --proxy-change-url "https://changeip.mobileproxy.space/?proxy_key=..." \
  --playwright --workers 4

# Run directly from a parser_avito config.toml file:
avito-sdk config config.toml

# Inspect single item card:
avito-sdk item 3854129841

# View all recorded price drops:
avito-sdk drops --db prices.db

# Start Model Context Protocol (MCP) Server over stdio:
avito-mcp --proxy "http://user:pass@ip:port" --proxy-change-url "https://..." --playwright
```

---

## 🤖 Native MCP (Model Context Protocol) Server

**avito-sdk** includes a native, high-performance [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server (`avito-mcp` or `avito-sdk mcp`) communicating over JSON-RPC 2.0 `stdio`.

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
* ☕ **Donate (USDT TRC-20)**:  
  `TDVbEdnpgNgoAhNcn1EwXxWHiR3RKLit5P`  
  *(Network: TRON / TRC-20 | [Verify on TronScan](https://tronscan.org/#/address/TDVbEdnpgNgoAhNcn1EwXxWHiR3RKLit5P))*

[![GitHub Repo stars](https://img.shields.io/github/stars/eminsk/avito-sdk?style=social)](https://github.com/eminsk/avito-sdk)
[![GitHub Issues](https://img.shields.io/github/issues/eminsk/avito-sdk?color=red&style=flat-square)](https://github.com/eminsk/avito-sdk/issues)
[![GitHub Discussions](https://img.shields.io/badge/Discussions-Join_Community-blue?logo=github&style=flat-square)](https://github.com/eminsk/avito-sdk/discussions)
[![Donate USDT](https://img.shields.io/badge/Donate-USDT_(TRC20)-26A17B?style=flat-square&logo=tether&logoColor=white)](https://tronscan.org/#/address/TDVbEdnpgNgoAhNcn1EwXxWHiR3RKLit5P)

---

## 📄 License

Distributed under the **MIT** License.  
Author: **eminsk** ([M_N_Nik@yahoo.com](mailto:M_N_Nik@yahoo.com))
