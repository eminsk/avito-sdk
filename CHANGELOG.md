# Changelog

All notable changes to `avito-sdk` will be documented in this file.

## [0.4.5] - 2026-11-25

### Added & Fixed
- **Item.location & Feed Cards Stability**: Added `@property def location` fallback (`location_name` or `address`) on `Item` model, resolving runtime `AttributeError` when displaying live listings in GUI cards.
- **Price Drop Badge in Live Feed**: Highlighted listing discounts with `(📉 -...)` directly on feed cards.
- **Official Community & Support Links**: Added direct `✈️ Telegram` link buttons in GUI header & Telegram tab to official channel `@avito_sdk_pro` and documentation links in GUI and CLI epilog.
- **Native MCP Ecosystem & Catalogs**: Integrated `smithery.yaml` and `Dockerfile` for automated container indexing on Glama, Smithery, PulseMCP, and Awesome MCP Servers.
- **High-DPI Showcase Media**: Embedded real GUI screenshots (`gui_monitor.png`, `gui_feed.png`) into README documentation.

## [0.4.4] - 2026-11-25

### Added & Fixed
- **Bundled Native Chrome TLS in Standalone Windows `.exe`**: Switched PyInstaller builds (`AvitoSDK_Pro.spec`, `build_exe.bat`, `run_gui.bat`) to Python 3.12 with `curl_cffi` bundled natively and added a header TLS badge in the GUI.
- **`spfa.pro` API Key & Phone Endpoint**: Updated `ParsePhone.API_URL` from deprecated `spfa.ru` to `https://spfa.pro/api/phone/` and added optional `spfa_api_key` cookie auto-refresh in the Proxy tab.
- **GUI & Alerts Polish**: Added clear labels above filter controls, fixed Telegram toggle persistence and `seen_prices` price-drop notifications, attached SDK log queue streaming, and wired dynamic `__version__` across GUI & launcher.
- **Unified Partner & Packaging Parity**: Synchronized all MobileProxy links to the VPN-free `mobileproxy.rent/?p=279117` mirror and 3-hour free trial, and aligned versions across PyPI, Conda recipe, and Debian packaging.

## [0.4.3] - 2026-11-24

### Added
- **Avito SDK Pro Desktop GUI & Standalone Binary**: Dark CustomTkinter desktop UI (`AvitoSDK_Pro.exe`) with 3D icon, Windows Taskbar `AppUserModelID` integration, live sniping feed, 1-click proxy latency test, Telegram proxy decoupling, Excel export, and pre-configured climate presets.

## [0.4.2] - 2026-11-16

### Added & Enhanced
- **Mobile Proxy Auto-Rotation & Multi-Threaded Scraping**:
  - First-class support for mobile proxy rotation (`MobileProxyRotator` and MobileProxy.space integration) for high-concurrency scraping without anti-bot bans or 429 rate limits.
  - Seamless support for external IP-change rotation URLs (`change_ip_url`) with configurable cooldowns and automatic retry mechanisms.
- **PyInstaller & Bundled Environment Compatibility**:
  - Added robust `get_ca_bundle()` resolution supporting `sys._MEIPASS` when compiled into standalone `.exe` binaries with PyInstaller.
  - Automatic Windows 8.3 short-path conversion (`GetShortPathNameW`) to eliminate issues with Cyrillic or special characters in user profile directory paths.
- **Resilient SSL Fallback (`curl: (77)`)**:
  - Graceful auto-recovery in both `SyncHttpTransport` and `AsyncHttpTransport` when SSL CA certificates cannot be loaded: transparently retries with `verify=False` to prevent parser downtime.

### Fixed
- **Typing Imports**: Resolved missing `Any`, `Tuple`, and `AvitoConfig` type hints across exporters, parameters, and models.
- **ProcessGuard**: Harmonized cross-platform process collision messages and regex patterns across Windows, Linux, and macOS (`flock`).

## [0.4.1] - 2026-10-17

### Added
- **Pure Native HTTP Transport**:
  - Zero Playwright dependency by default for ultra-lightweight execution.
  - Built-in Mobile Proxy Auto-Rotation integration.
  - Full compatibility with PyPy 3.8–3.12 and Python 3.13 free-threaded (no-GIL) builds.

## [0.1.0] - 2026-10-05

### Added
- **Core SDK & Clients**:
  - `AvitoClient`: intuitive synchronous client for search, enrichment, and export.
  - `AsyncAvitoClient`: native asyncio streaming client for bot and web frameworks (Aiogram 3, FastAPI, aiohttp).
  - Headless execution with zero desktop GUI dependencies.
- **Price Tracking Engine (PR #334 / Issue #214)**:
  - `PriceTracker` backed by SQLite and in-memory engine.
  - Automatic detection of price changes, drops (`price_drop`), and full price history log.
- **Seller Information Extraction (PR #334 / Issue #333)**:
  - Extraction of seller display name (`seller_name`) from API payloads and HTML markers.
  - Extraction of seller profile/brand slug (`seller_id`).
- **Item Parameters & Characteristics (PR #337 / Issue #335)**:
  - Deep parser for Beduin scenario widget structures and Mobile API properties.
  - Full support for real estate («О помещении», этаж, площадь), auto specs, electronics, and goods.
- **Full Description Extraction (PR #329 / Issue #305)**:
  - Support for multi-line description parsing from JSON scenarios and Schema.org microdata.
- **Exporters**:
  - Styled Excel (`.xlsx`) export via openpyxl with auto-sized columns.
  - JSON and JSON Lines (`.jsonl`) streaming export.
  - CSV export with utf-8-sig encoding.
  - Pandas / Polars DataFrame conversion.
- **CLI Tool**:
  - Built-in `avito-sdk` and `avito-parser` command-line interfaces.
- **Anti-Bot & Transport**:
  - TLS browser impersonation via `curl_cffi` with graceful fallback to `httpx` and `requests`.
  - Automatic retry logic on 429/403 with exponential backoff and jitter.
