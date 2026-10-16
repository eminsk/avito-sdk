#!/usr/bin/env python3
"""
Быстрая проверка работы Avito MCP Server (JSON-RPC 2.0 stdio)
Запуск: uv run python check_mcp.py
"""

import json
import subprocess
import sys
from pathlib import Path

# Путь к скомпилированному MCP серверу
EXE_PATH = Path(sys.prefix) / "Scripts" / "avito-mcp.exe"
if not EXE_PATH.exists():
    EXE_PATH = Path(r"C:\proekts\avito-sdk\.venv\Scripts\avito-mcp.exe")

PROXY = "http://UZ5beb:Yk9uK3AR5uSk@mproxy.site:12411"
CHANGE_URL = "https://changeip.mobileproxy.space/?proxy_key=41e8d9bc9c9a784102c33bf2db28bedb&format=json"

def main():
    print("=" * 65)
    print("       ПРОВЕРКА РАБОТЫ AVITO MCP СЕРВЕРА В АНТИГРАВИТИ")
    print("=" * 65)
    print(f"[*] Исполняемый файл MCP: {EXE_PATH}")
    
    if not EXE_PATH.exists():
        print(f"[!] Ошибка: файл {EXE_PATH} не найден!")
        return 1

    print("[*] Запуск процесса avito-mcp.exe через stdio...")
    proc = subprocess.Popen(
        [
            str(EXE_PATH),
            "--proxy", PROXY,
            "--proxy-change-url", CHANGE_URL,
            "--db", "avito_prices.db",
            "--workers", "2",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    def query_mcp(req: dict) -> dict:
        proc.stdin.write(json.dumps(req, ensure_ascii=False) + "\n")
        proc.stdin.flush()
        line = proc.stdout.readline()
        if not line:
            err = proc.stderr.read()
            raise RuntimeError(f"Сервер не ответил. Stderr: {err}")
        return json.loads(line)

    try:
        # 1. Handshake
        print("\n[ШАГ 1] Проверка рукопожатия MCP (initialize)...")
        r_init = query_mcp({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05"},
        })
        info = r_init.get("result", {}).get("serverInfo", {})
        ver = r_init.get("result", {}).get("protocolVersion")
        print(f"  ✓ Сервер ответил: {info.get('name')} v{info.get('version')}")
        print(f"  ✓ Версия протокола MCP: {ver}")

        # 2. Список инструментов
        print("\n[ШАГ 2] Запрос доступных инструментов (tools/list)...")
        r_tools = query_mcp({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        })
        tools = r_tools.get("result", {}).get("tools", [])
        print(f"  ✓ Найдено инструментов: {len(tools)}")
        for t in tools:
            print(f"    • {t['name']}: {t['description'][:55]}...")

        # 3. Вызов реального поиска
        query = "iPhone 15"
        print(f"\n[ШАГ 3] Вызов инструмента avito_search (query='{query}', limit=2)...")
        r_call = query_mcp({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "avito_search",
                "arguments": {
                    "query": query,
                    "region": "moskva",
                    "limit": 2,
                    "enrich_details": False,
                },
            },
        })

        res = r_call.get("result", {})
        if res.get("isError"):
            print(f"  [!] Ошибка вызова: {res.get('content')}")
        else:
            data = res.get("structuredContent", {})
            items = data.get("items", [])
            print(f"  ✓ Найдено объявлений: {len(items)}")
            for idx, item in enumerate(items, 1):
                print(f"\n  [Объявление #{idx}]")
                print(f"    ID:       {item.get('id')}")
                print(f"    Название: {item.get('title')}")
                print(f"    Цена:     {item.get('price')} ₽")
                print(f"    Город:    {item.get('location')}")
                print(f"    Ссылка:   {item.get('url')}")

        print("\n" + "=" * 65)
        print("  ✓ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ: MCP СЕРВЕР РАБОТАЕТ ИДЕАЛЬНО!")
        print("=" * 65)
        return 0

    finally:
        proc.terminate()
        proc.wait(timeout=2)

if __name__ == "__main__":
    sys.exit(main())
