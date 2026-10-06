"""
Configuration loader and writer for avito-sdk, 100% compatible with Duff89/parser_avito's config.toml.
Supports Python 3.11+ built-in tomllib as well as fallback TOML parsing for Python 3.8-3.10.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


@dataclass
class AvitoConfig:
    """Full configuration model compatible with parser_avito's config.toml."""

    urls: List[str] = field(default_factory=list)
    proxy_string: Optional[str] = None
    proxy_change_url: Optional[str] = None
    keys_word_white_list: List[str] = field(default_factory=list)
    keys_word_black_list: List[str] = field(default_factory=list)
    seller_black_list: List[str] = field(default_factory=list)
    count: int = 1
    tg_token: Optional[str] = None
    tg_chat_id: List[str] = field(default_factory=list)
    vk_token: Optional[str] = None
    vk_user_id: List[str] = field(default_factory=list)
    max_price: int = 999_999_999
    min_price: int = 0
    geo: Optional[str] = None
    max_age: int = 0
    debug_mode: int = 0
    pause_general: int = 60
    pause_between_links: int = 5
    max_count_of_retry: int = 5
    ignore_reserv: bool = True
    ignore_promotion: bool = False
    one_time_start: bool = False
    one_file_for_link: bool = False
    parse_views: bool = False
    parse_description: bool = False
    parse_params: bool = False
    save_xlsx: bool = True
    use_webdriver: bool = True
    use_bypass_api: bool = False
    cookies_api_key: Optional[str] = None
    purchase_cooldown: int = 600
    output_dir: Path = Path("result")
    use_own_cookies: bool = False
    parse_phone: bool = False
    proxy_notifier: Optional[str] = None
    tg_only_text: bool = False
    retry_delay: int = 5
    timeout: int = 20
    block_threshold: int = 3
    max_workers: int = 1


def _parse_toml_bytes(raw_bytes: bytes) -> Dict[str, Any]:
    try:
        import tomllib
        return tomllib.loads(raw_bytes.decode("utf-8"))
    except ImportError:
        try:
            import tomli
            return tomli.loads(raw_bytes.decode("utf-8"))
        except ImportError:
            import toml
            return toml.loads(raw_bytes.decode("utf-8"))


def load_avito_config(path: Union[str, Path] = "config.toml") -> AvitoConfig:
    """Load an AvitoConfig from a parser_avito-compatible config.toml file."""
    cfg_path = Path(path)
    if not cfg_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {cfg_path}")

    data = _parse_toml_bytes(cfg_path.read_bytes())
    avito_sec = data.get("avito", data) if isinstance(data, dict) else {}

    out_dir = avito_sec.get("output_dir", "result")
    tg_chat = avito_sec.get("tg_chat_id") or []
    if isinstance(tg_chat, (str, int)):
        tg_chat = [str(tg_chat)] if str(tg_chat).strip() else []

    vk_users = avito_sec.get("vk_user_id") or []
    if isinstance(vk_users, (str, int)):
        vk_users = [str(vk_users)] if str(vk_users).strip() else []

    return AvitoConfig(
        urls=list(avito_sec.get("urls") or []),
        proxy_string=avito_sec.get("proxy_string") or None,
        proxy_change_url=avito_sec.get("proxy_change_url") or None,
        keys_word_white_list=list(avito_sec.get("keys_word_white_list") or []),
        keys_word_black_list=list(avito_sec.get("keys_word_black_list") or []),
        seller_black_list=list(avito_sec.get("seller_black_list") or []),
        count=int(avito_sec.get("count", 1)),
        tg_token=avito_sec.get("tg_token") or None,
        tg_chat_id=[str(x) for x in tg_chat],
        vk_token=avito_sec.get("vk_token") or None,
        vk_user_id=[str(x) for x in vk_users],
        max_price=int(avito_sec.get("max_price", 999_999_999)),
        min_price=int(avito_sec.get("min_price", 0)),
        geo=avito_sec.get("geo") or None,
        max_age=int(avito_sec.get("max_age", 0)),
        debug_mode=int(avito_sec.get("debug_mode", 0)),
        pause_general=int(avito_sec.get("pause_general", 60)),
        pause_between_links=int(avito_sec.get("pause_between_links", 5)),
        max_count_of_retry=int(avito_sec.get("max_count_of_retry", 5)),
        ignore_reserv=bool(avito_sec.get("ignore_reserv", True)),
        ignore_promotion=bool(avito_sec.get("ignore_promotion", False)),
        one_time_start=bool(avito_sec.get("one_time_start", False)),
        one_file_for_link=bool(avito_sec.get("one_file_for_link", False)),
        parse_views=bool(avito_sec.get("parse_views", False)),
        parse_description=bool(avito_sec.get("parse_description", False)),
        parse_params=bool(avito_sec.get("parse_params", False)),
        save_xlsx=bool(avito_sec.get("save_xlsx", True)),
        use_webdriver=bool(avito_sec.get("use_webdriver", True)),
        use_bypass_api=bool(avito_sec.get("use_bypass_api", False)),
        cookies_api_key=avito_sec.get("cookies_api_key") or None,
        purchase_cooldown=int(avito_sec.get("purchase_cooldown", 600)),
        output_dir=Path(out_dir),
        use_own_cookies=bool(avito_sec.get("use_own_cookies", False)),
        parse_phone=bool(avito_sec.get("parse_phone", False)),
        proxy_notifier=avito_sec.get("proxy_notifier") or None,
        tg_only_text=bool(avito_sec.get("tg_only_text", False)),
        retry_delay=int(avito_sec.get("retry_delay", 5)),
        timeout=int(avito_sec.get("timeout", 20)),
        block_threshold=int(avito_sec.get("block_threshold", 3)),
        max_workers=int(avito_sec.get("max_workers", 1)),
    )
