"""
Unit Tests for avito-sdk Native MCP Server (JSON-RPC 2.0 stdio)
"""

import json
import pytest

from avito_sdk import __version__
from avito_sdk.mcp_server import (
    AvitoMCPServer,
    LATEST_PROTOCOL_VERSION,
    SUPPORTED_PROTOCOL_VERSIONS,
)


def test_mcp_initialize_negotiation():
    server = AvitoMCPServer()

    # 1. Request latest supported version
    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {"protocolVersion": "2025-11-25"},
    }
    resp = server.handle_request(req)
    assert resp["id"] == 1
    assert resp["result"]["protocolVersion"] == "2025-11-25"
    assert resp["result"]["serverInfo"]["name"] == "avito-sdk-mcp"
    assert resp["result"]["serverInfo"]["version"] == __version__
    assert "tools" in resp["result"]["capabilities"]

    # 2. Request older supported version
    req_old = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "initialize",
        "params": {"protocolVersion": "2024-11-05"},
    }
    resp_old = server.handle_request(req_old)
    assert resp_old["result"]["protocolVersion"] == "2024-11-05"

    # 3. Request unknown version -> fallback to latest supported
    req_unknown = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "initialize",
        "params": {"protocolVersion": "9999-99-99"},
    }
    resp_unknown = server.handle_request(req_unknown)
    assert resp_unknown["result"]["protocolVersion"] == LATEST_PROTOCOL_VERSION


def test_mcp_ping():
    server = AvitoMCPServer()
    resp = server.handle_request({"jsonrpc": "2.0", "id": 5, "method": "ping"})
    assert resp["id"] == 5
    assert resp["result"] == {}


def test_mcp_notifications_ignored():
    server = AvitoMCPServer()
    resp = server.handle_request({
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {},
    })
    assert resp is None


def test_mcp_method_not_found():
    server = AvitoMCPServer()
    resp = server.handle_request({"jsonrpc": "2.0", "id": 99, "method": "unknown_action"})
    assert resp["id"] == 99
    assert "error" in resp
    assert resp["error"]["code"] == -32601


def test_mcp_tools_list_schema():
    server = AvitoMCPServer()
    resp = server.handle_request({"jsonrpc": "2.0", "id": 10, "method": "tools/list"})
    assert resp["id"] == 10
    tools = resp["result"]["tools"]
    tool_names = [t["name"] for t in tools]
    assert "avito_search" in tool_names
    assert "avito_get_item" in tool_names
    assert "avito_price_drops" in tool_names

    for tool in tools:
        assert "name" in tool
        assert "description" in tool
        assert "inputSchema" in tool
        assert "type" in tool["inputSchema"]
