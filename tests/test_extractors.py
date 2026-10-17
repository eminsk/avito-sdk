"""Tests for extractors covering PR #334 (seller, price) and PR #337 (params) and PR #329 (description)."""

from avito_sdk.extractors import (
    extract_catalog_items,
    extract_description,
    extract_params,
    extract_seller_id,
    extract_seller_name,
    extract_views,
    parse_raw_item,
)


# === Tests for PR #337: Parameters & Characteristics ===

def test_extract_params_beduin_scenario():
    """Verify extraction of parameters from Beduin scenario widgets (PR #337)."""
    payload = {
        "success": {
            "view": {
                "scenario": {
                    "beduin": {
                        "main": {
                            "params": {
                                "realtyParams": {
                                    "items": [
                                        {"title": "Общая площадь", "description": "45.5 м²"},
                                        {"name": "Этаж", "value": "4 из 10"},
                                    ]
                                },
                                "buildingParams": {
                                    "items": [
                                        {"label": "Тип дома", "text": "Монолитный"},
                                    ]
                                },
                            }
                        }
                    }
                }
            }
        }
    }
    params = extract_params(payload)
    assert params["Общая площадь"] == "45.5 м²"
    assert params["Этаж"] == "4 из 10"
    assert params["Тип дома"] == "Монолитный"


def test_extract_params_mobile_api():
    """Verify extraction of parameters from mobile API payload (PR #337)."""
    payload = {
        "success": {
            "mobile": {
                "params": [
                    {"title": "Состояние", "description": "Новое"},
                    {"title": "Бренд", "description": "Apple"},
                ]
            }
        }
    }
    params = extract_params(payload)
    assert params["Состояние"] == "Новое"
    assert params["Бренд"] == "Apple"


def test_extract_params_empty():
    assert extract_params(None) == {}
    assert extract_params({}) == {}
    assert extract_params({"success": {}}) == {}


# === Tests for PR #334: Seller Name & Seller ID ===

def test_extract_seller_name_from_payload():
    """Extract seller name from mobile API payload."""
    payload = {
        "success": {
            "mobile": {
                "seller": {
                    "name": "Алексей Смирнов"
                }
            }
        }
    }
    assert extract_seller_name(payload) == "Алексей Смирнов"


def test_extract_seller_name_from_html():
    """Extract seller name from HTML markers (Issue #333)."""
    html = '''
    <div class="seller-block">
        <span data-marker="seller-info/name">Магазин Электроники</span>
    </div>
    '''
    assert extract_seller_name({}, html_text=html) == "Магазин Электроники"


def test_extract_seller_id():
    """Extract seller slug from userLogo link."""
    payload = {
        "userLogo": {
            "link": "/brands/re-store"
        }
    }
    assert extract_seller_id(payload) == "re-store"

    payload_user = {
        "userLogo": {
            "link": "/user/abcdef1234567890/profile"
        }
    }
    assert extract_seller_id(payload_user) == "abcdef1234567890"


# === Tests for Issue #305: Full Description ===

def test_extract_description_from_mobile_payload():
    payload = {
        "success": {
            "mobile": {
                "description": "Полный текст описания объявления.\nВ идеальном состоянии."
            }
        }
    }
    desc = extract_description(payload)
    assert desc == "Полный текст описания объявления.\nВ идеальном состоянии."


def test_extract_description_from_segments():
    payload = {
        "success": {
            "view": {
                "scenario": {
                    "beduin": {
                        "main": {
                            "params": {
                                "description": {
                                    "segments": [
                                        {"text": "Часть 1. "},
                                        {"text": "Часть 2."},
                                    ]
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    assert extract_description(payload) == "Часть 1. Часть 2."


def test_extract_description_from_html():
    html = '<div data-marker="item-description/text">Продам отличный велосипед</div>'
    assert extract_description({}, html_text=html) == "Продам отличный велосипед"


# === Tests for Views ===

def test_extract_views():
    payload = {
        "success": {
            "mobile": {
                "stats": {
                    "views": {
                        "total": 350,
                        "today": 12,
                    }
                }
            }
        }
    }
    total, today = extract_views(payload)
    assert total == 350
    assert today == 12


# === Tests for Catalog Extraction ===

def test_extract_catalog_items():
    catalog_json = {
        "result": {
            "items": [
                {
                    "id": 111222,
                    "title": "Игровой ПК RTX 4080",
                    "priceDetailed": {"value": 150000, "string": "150 000 ₽"},
                    "urlPath": "/moskva/tovary/pk_111222",
                    "sellerName": "ComputerShop",
                    "userLogo": {"link": "/brands/computershop"},
                },
                {
                    "id": 333444,
                    "title": "Монитор 4K 144Hz",
                    "price": 40000,
                },
            ]
        }
    }

    items = extract_catalog_items(catalog_json)
    assert len(items) == 2
    assert items[0].id == 111222
    assert items[0].price == 150000
    assert items[0].seller_name == "ComputerShop"
    assert items[0].seller_id == "computershop"
    assert items[1].id == 333444
    assert items[1].price == 40000


def test_safe_int_unicode_superscripts():
    """Verify that unicode superscripts like ² and ³ do not break integer parsing."""
    from avito_sdk.extractors import safe_int

    assert safe_int("2466²") == 2466
    assert safe_int("2 466 ₽ за м²") == 2466
    assert safe_int("150 000 ₽ / м³") == 150000
    assert safe_int("¹²³⁴⁵⁶⁷⁸⁹") == 0  # no standard ASCII 0-9 digits
    assert safe_int(None) == 0
    assert safe_int(False) == 0
    assert safe_int(999) == 999


def test_commercial_realty_price_parsing():
    """Verify that commercial real estate price strings with м² are parsed cleanly."""
    raw_item = {
        "id": "3854129841",
        "title": "Склад 500 м²",
        "priceDetailed": {"value": "2466²", "string": "2 466 ₽ за м²"},
        "urlPath": "/moskva/kommercheskaya_nedvizhimost/sklad_3854129841",
    }
    item = parse_raw_item(raw_item)
    assert item is not None
    assert item.id == 3854129841
    assert item.price == 2466


def test_extract_embedded_state_skips_non_catalog_scripts():
    """Verify that extract_embedded_state skips header/subdomain scripts and finds catalog items in __initialData__."""
    from bs4 import BeautifulSoup
    from avito_sdk.extractors import extract_embedded_state, extract_catalog_items

    html = """
    <html>
      <head>
        <script type="mime/invalid" data-mfe-state="true">
          {"subdomain": {"routeBasePath": "", "subdomainSlug": ""}, "geo": {"id": 123}}
        </script>
        <script>
          window.__initialData__ = "{\\"search\\":{\\"allItems\\":{\\"777\\":{\\"type\\":\\"item\\",\\"value\\":{\\"id\\":777,\\"title\\":\\"Ноутбук ThinkPad\\",\\"priceDetailed\\":{\\"value\\":55000}}}}}}";
        </script>
      </head>
      <body></body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    state = extract_embedded_state(soup)
    assert state is not None
    items = extract_catalog_items(state)
    assert len(items) == 1
    assert items[0].id == 777
    assert items[0].title.startswith("Ноутбук ThinkPad")
    assert items[0].price == 55000


def test_extract_all_embedded_states_multiple_candidates():
    """Verify that multiple MFE and __initialData__ scripts are all extracted and scored properly."""
    from bs4 import BeautifulSoup
    from avito_sdk.extractors import extract_all_embedded_states, extract_embedded_state, extract_catalog_items

    html = """
    <html>
      <head>
        <script type="mime/invalid" data-mfe-state="true">
          {"result": {"userInfo": {"id": 12345, "name": "User"}}}
        </script>
        <script>
          window.__initialData__ = "{\\"search\\":{\\"catalog\\":{\\"items\\":[{\\"id\\":888,\\"title\\":\\"iPhone 15\\",\\"priceDetailed\\":{\\"value\\":75000}}]}}}";
        </script>
      </head>
      <body></body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    all_states = extract_all_embedded_states(soup)
    assert len(all_states) == 2

    # extract_embedded_state must prioritize the one with catalog items over userInfo
    best_state = extract_embedded_state(soup)
    assert best_state is not None
    items = extract_catalog_items(best_state)
    assert len(items) == 1
    assert items[0].id == 888
    assert items[0].price == 75000


