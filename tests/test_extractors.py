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
