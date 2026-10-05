"""
04_export_excel_and_json.py - Extract full parameters (PR #337) and export to styled Excel.
"""

from avito_sdk import AvitoClient, to_excel, to_jsonl


def main():
    client = AvitoClient()

    print("[*] Fetching listings with deep parameter extraction (PR #337)...")
    items = list(
        client.search(
            query="снять 1-комнатную квартиру",
            region="Москва",
            limit=15,
            enrich_details=True,
        )
    )

    # 1. Export to Excel with auto column width and styled header
    excel_file = "apartments_moscow.xlsx"
    to_excel(items, excel_file)
    print(f"[✓] Successfully exported {len(items)} items to {excel_file}")

    # 2. Export to JSON Lines
    jsonl_file = "apartments_moscow.jsonl"
    to_jsonl(items, jsonl_file)
    print(f"[✓] Successfully exported {len(items)} items to {jsonl_file}")


if __name__ == "__main__":
    main()
