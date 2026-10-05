# Changelog

All notable changes to `avito-sdk` will be documented in this file.

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
