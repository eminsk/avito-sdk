"""
Native Model Context Protocol (MCP) Server for avito-sdk.
Exposes Avito search, deep card inspection («О помещении» & characteristics),
price drop tracking, and Excel/Telegram reporting to Claude Desktop, Cursor,
Windsurf, Antigravity, and any MCP-compatible AI agent over JSON-RPC 2.0 stdio.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from avito_sdk.client import AvitoClient
from avito_sdk.tracker import PriceTracker

SUPPORTED_PROTOCOL_VERSIONS = (
    "2025-11-25",
    "2025-06-18",
    "2024-11-05",
)
LATEST_PROTOCOL_VERSION = SUPPORTED_PROTOCOL_VERSIONS[0]
MCP_PROTOCOL_VERSION = LATEST_PROTOCOL_VERSION

MCP_TOOLS_SCHEMA: List[Dict[str, Any]] = [
    {
        "name": "avito_search",
        "description": (
            "Search Avito listings with full filtering (price range, white/black keywords, "
            "seller blacklist, geo, ignore reserved/promotion), optional deep card enrichment "
            "(«О помещении», specs, seller name, views), price tracking, and Excel/Telegram export."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query (e.g. 'помещение свободного назначения', 'rtx 4090')"},
                "region": {"type": "string", "description": "Region slug (default: 'rossiya' or 'moskva')", "default": "rossiya"},
                "min_price": {"type": "integer", "description": "Minimum price in RUB"},
                "max_price": {"type": "integer", "description": "Maximum price in RUB"},
                "white_keywords": {"type": "array", "items": {"type": "string"}, "description": "Required keywords"},
                "black_keywords": {"type": "array", "items": {"type": "string"}, "description": "Excluded keywords"},
                "ignore_reserved": {"type": "boolean", "default": False, "description": "Skip reserved items"},
                "only_new_or_changed": {"type": "boolean", "default": False, "description": "Only return new or price-changed listings"},
                "enrich_details": {"type": "boolean", "default": False, "description": "Fetch full card parameters, seller name, and views"},
                "limit": {"type": "integer", "default": 10, "description": "Maximum number of items to return"},
                "max_pages": {"type": "integer", "default": 1, "description": "Maximum search pages to scan (default: 1)"},
                "excel_path": {"type": "string", "description": "Optional path to save results as .xlsx"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "avito_get_item",
        "description": (
            "Fetch complete details for a single Avito listing by numeric item_id, "
            "including full description, all parameters («О помещении», auto specs, etc.), "
            "seller name/ID, and view statistics (total and today)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "item_id": {"type": "integer", "description": "Avito numeric item ID"},
            },
            "required": ["item_id"],
        },
    },
    {
        "name": "avito_price_drops",
        "description": (
            "Retrieve all tracked Avito listings whose price has dropped compared to their "
            "initial recorded price in the local SQLite database, or get full price history for an item_id."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "item_id": {"type": "integer", "description": "Optional item ID to get full historical price records"},
            },
        },
    },
]


class AvitoMCPServer:
    """Zero-dependency Model Context Protocol (MCP) JSON-RPC 2.0 server for avito-sdk."""

    def __init__(
        self,
        proxy: Optional[str] = None,
        proxy_change_url: Optional[str] = None,
        use_playwright_cookies: bool = False,
        tracker_db: str = "avito_prices.db",
        tg_token: Optional[str] = None,
        tg_chat_id: Optional[str] = None,
        workers: int = 4,
        client: Optional[AvitoClient] = None,
    ):
        self.proxy = proxy or os.environ.get("AVITO_PROXY")
        self.proxy_change_url = proxy_change_url or os.environ.get("AVITO_PROXY_CHANGE_URL")
        self.use_playwright_cookies = use_playwright_cookies or (
            os.environ.get("AVITO_PLAYWRIGHT", "").lower() in ("1", "true", "yes")
        )
        self.tracker_db = tracker_db or os.environ.get("AVITO_TRACKER_DB", "avito_prices.db")
        self.tg_token = tg_token or os.environ.get("AVITO_TG_TOKEN")
        self.tg_chat_id = tg_chat_id or os.environ.get("AVITO_TG_CHAT_ID")
        self.workers = workers
        self._client = client

    @property
    def client(self) -> AvitoClient:
        if self._client is None:
            self._client = AvitoClient(
                proxy=self.proxy,
                proxy_change_url=self.proxy_change_url,
                use_playwright_cookies=self.use_playwright_cookies,
                tracker_db=self.tracker_db,
                tg_token=self.tg_token,
                tg_chat_id=self.tg_chat_id,
            )
        return self._client

    def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single JSON-RPC 2.0 message and return a response dict (or None for notifications)."""
        method = request.get("method", "")
        req_id = request.get("id")
        params = request.get("params") or {}

        # Notifications have no id and expect no response
        if req_id is None and method.startswith("notifications/"):
            return None

        try:
            if method == "initialize":
                from avito_sdk import __version__
                client_version = params.get("protocolVersion")
                negotiated_version = (
                    client_version
                    if client_version in SUPPORTED_PROTOCOL_VERSIONS
                    else LATEST_PROTOCOL_VERSION
                )
                result = {
                    "protocolVersion": negotiated_version,
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "avito-sdk-mcp",
                        "version": __version__,
                    },
                }
                return {"jsonrpc": "2.0", "id": req_id, "result": result}

            if method == "ping":
                return {"jsonrpc": "2.0", "id": req_id, "result": {}}

            if method == "tools/list":
                return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": MCP_TOOLS_SCHEMA}}

            if method == "tools/call":
                tool_name = params.get("name", "")
                args = params.get("arguments") or {}
                tool_output = self._call_tool(tool_name, args)
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(tool_output, ensure_ascii=False, indent=2),
                            }
                        ],
                        "isError": False,
                    },
                }

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }
        except Exception as exc:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": f"Error: {exc}"}],
                    "isError": True,
                },
            }

    def _call_tool(self, name: str, args: Dict[str, Any]) -> Any:
        if name == "avito_search":
            items = list(
                self.client.search(
                    query=str(args.get("query", "")),
                    region=str(args.get("region", "rossiya")),
                    min_price=args.get("min_price"),
                    max_price=args.get("max_price"),
                    white_keywords=args.get("white_keywords"),
                    black_keywords=args.get("black_keywords"),
                    ignore_reserved=bool(args.get("ignore_reserved", False)),
                    only_new_or_changed=bool(args.get("only_new_or_changed", False)),
                    enrich_details=bool(args.get("enrich_details", False)),
                    max_workers=self.workers,
                    limit=int(args.get("limit", 10)),
                    max_pages=int(args.get("max_pages", 1)),
                    excel_path=args.get("excel_path"),
                    notify_telegram=bool(self.client.notifier),
                )
            )
            return {
                "count": len(items),
                "items": [it.to_dict() for it in items],
            }

        if name == "avito_get_item":
            item_id = int(args["item_id"])
            item = self.client.get_item(item_id)
            return item.to_dict()

        if name == "avito_price_drops":
            tracker = self.client.tracker or PriceTracker(db_path=self.tracker_db)
            if "item_id" in args and args["item_id"] is not None:
                history = tracker.get_history(int(args["item_id"]))
                return {
                    "item_id": int(args["item_id"]),
                    "history": [
                        {
                            "price": rec.price,
                            "timestamp": rec.timestamp.isoformat(),
                            "title": rec.title,
                            "seller_name": rec.seller_name,
                        }
                        for rec in history
                    ],
                }
            drops = tracker.get_price_drops()
            return {"count": len(drops), "drops": drops}

        raise ValueError(f"Unknown MCP tool: {name}")

    def run_stdio(self) -> None:
        """Run the MCP JSON-RPC 2.0 server over standard input/output."""
        for raw_line in sys.stdin:
            line = raw_line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
            except json.JSONDecodeError:
                continue
            resp = self.handle_request(req)
            if resp is not None:
                sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
                sys.stdout.flush()


def main_mcp(argv=None) -> int:
    """CLI entry point for avito-mcp / avito-sdk mcp."""
    import argparse

    parser = argparse.ArgumentParser(description="Start Avito SDK Model Context Protocol (MCP) Server over stdio")
    parser.add_argument("--proxy", default=None, help="Mobile proxy URL")
    parser.add_argument("--proxy-change-url", default=None, help="Mobile proxy IP rotation URL")
    parser.add_argument("--playwright", action="store_true", help="Use Playwright Chromium for ft cookies")
    parser.add_argument("--db", default="avito_prices.db", help="Path to SQLite price tracker database")
    parser.add_argument("--tg-token", default=None, help="Telegram Bot Token")
    parser.add_argument("--tg-chat-id", default=None, help="Telegram Channel/Chat ID")
    parser.add_argument("--workers", type=int, default=4, help="Parallel worker threads")
    args = parser.parse_args(argv)

    server = AvitoMCPServer(
        proxy=args.proxy,
        proxy_change_url=args.proxy_change_url,
        use_playwright_cookies=args.playwright,
        tracker_db=args.db,
        tg_token=args.tg_token,
        tg_chat_id=args.tg_chat_id,
        workers=args.workers,
    )
    server.run_stdio()
    return 0


if __name__ == "__main__":
    sys.exit(main_mcp())
