"""
Mobile proxy configuration parsing, external cookie providers, and phone extraction utilities.
Ported and modernized from Duff89/parser_avito:
- Flexible mobile proxy parsing (user:pass@ip:port, ip:port@user:pass, ip:port:user:pass)
- External API cookie providers (SPFA)
- URL conversion to mobile API
- Phone number extraction
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

logger = logging.getLogger("avito_sdk")


@dataclass
class ParsedProxy:
    server: str
    username: Optional[str] = None
    password: Optional[str] = None
    change_ip_url: Optional[str] = None

    def __getitem__(self, key: str):
        return getattr(self, key)


def parse_proxy_config(proxy_str: Optional[str], change_ip_url: Optional[str] = None) -> Optional[ParsedProxy]:
    """
    Parse flexible proxy formats supported by parser_avito:
    - http://user:pass@ip:port
    - user:pass@ip:port
    - ip:port@user:pass
    - ip:port:user:pass
    - user:pass:ip:port
    - ip:port
    """
    if not proxy_str:
        return None
    raw = proxy_str.strip()
    if "//" in raw:
        raw = raw.split("//", 1)[1]

    if "@" in raw:
        left, right = raw.split("@", 1)
        if "." in right and ":" in right:
            ip_port, user_pass = right, left
        else:
            ip_port, user_pass = left, right
        if ":" in user_pass:
            login, password = user_pass.split(":", 1)
        else:
            login, password = user_pass, ""
    else:
        parts = raw.split(":")
        if len(parts) == 4:
            if "." in parts[0]:
                ip, port, login, password = parts
            else:
                login, password, ip, port = parts
            ip_port = f"{ip}:{port}"
        elif len(parts) == 2:
            ip_port = raw
            login, password = None, None
        else:
            raise ValueError(
                f"Unsupported proxy format: '{proxy_str}'. "
                "Use http://user:pass@ip:port, ip:port@user:pass, or ip:port:user:pass"
            )

    if not ip_port.startswith("http://") and not ip_port.startswith("https://"):
        ip_port = f"http://{ip_port}"

    return ParsedProxy(
        server=ip_port,
        username=login,
        password=password,
        change_ip_url=change_ip_url,
    )


class ExternalApiCookiesProvider:
    """
    SPFA External API cookie provider (ported from parser_avito/parser/cookies/external_api.py).
    Purchases and unblocks mobile session cookies & TLS fingerprints via https://spfa.pro/api.
    """

    API_URL = "https://spfa.pro/api"

    def __init__(
        self,
        api_key: str,
        proxy: Optional[str] = None,
        purchase_cooldown: int = 600,
        storage_path: str = "storage/cookies_external.json",
    ):
        from pathlib import Path
        self.api_key = api_key
        self.proxy = proxy
        self.purchase_cooldown = purchase_cooldown
        self.storage_path = Path(storage_path)
        self.last_id: Optional[str] = None
        self.last_cookies: Optional[Dict[str, str]] = None
        self.user_agent: Optional[str] = None
        self.fingerprint: Optional[dict] = None
        self._load_from_disk()

    def get_cookies(self) -> Tuple[Dict[str, str], Optional[str]]:
        if self.last_cookies:
            return self.last_cookies, self.user_agent
        return self.purchase_new_cookies()

    def purchase_new_cookies(self) -> Tuple[Dict[str, str], Optional[str]]:
        import json
        import time
        import requests

        resp = requests.post(
            f"{self.API_URL}/cookies/mobile/",
            json={"api_key": self.api_key, "mobile": True, "proxy": self.proxy},
            timeout=120,
        )
        resp.raise_for_status()
        payload = resp.json()
        if not payload.get("success"):
            raise RuntimeError("SPFA cookies service returned success=false")
        data = payload.get("results", {})
        self.last_id = data.get("id")
        self.last_cookies = data.get("cookies") or {}
        self.fingerprint = data.get("fingerprint") or {}
        fp_headers = self.fingerprint.get("headers", {}) if isinstance(self.fingerprint, dict) else {}
        self.user_agent = data.get("user_agent") or fp_headers.get("user-agent")
        self._save_to_disk(time.time())
        return self.last_cookies, self.user_agent

    def unblock_or_refresh(self) -> Tuple[Dict[str, str], Optional[str]]:
        import requests
        if not self.last_id:
            return self.purchase_new_cookies()
        try:
            res = requests.post(
                f"{self.API_URL}/unblock/",
                json={"id": self.last_id, "api_key": self.api_key, "proxy": self.proxy},
                timeout=120,
            )
            if res.status_code in (200, 202, 409):
                return self.last_cookies or {}, self.user_agent
        except Exception:
            pass
        return self.purchase_new_cookies()

    def _save_to_disk(self, saved_at: float) -> None:
        import json
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            self.storage_path.write_text(
                json.dumps(
                    {
                        "id": self.last_id,
                        "cookies": self.last_cookies,
                        "user_agent": self.user_agent,
                        "fingerprint": self.fingerprint,
                        "saved_at": saved_at,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
        except Exception:
            pass

    def _load_from_disk(self) -> None:
        import json
        if not self.storage_path.exists():
            return
        try:
            data = json.loads(self.storage_path.read_text(encoding="utf-8"))
            self.last_id = data.get("id")
            self.last_cookies = data.get("cookies")
            self.user_agent = data.get("user_agent")
            self.fingerprint = data.get("fingerprint")
        except Exception:
            pass


class AvitoUrlConverter:
    """
    Converts public Avito web URLs into mobile API URLs via https://spfa.pro/api/avito-url/
    with local JSON caching (ported from parser_avito/parser/url_converter.py).
    """

    ENDPOINT = "https://spfa.pro/api/avito-url/"

    def __init__(self, cache_path: str = "storage/avito_api_urls.json", timeout: int = 20):
        from pathlib import Path
        import json
        self.cache_path = Path(cache_path)
        self.timeout = timeout
        self._cache: Dict[str, str] = {}
        if self.cache_path.exists():
            try:
                data = json.loads(self.cache_path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    self._cache = {str(k): str(v) for k, v in data.items() if k and v}
            except Exception:
                pass

    def convert(self, url: str) -> str:
        import json
        import requests
        if url in self._cache:
            return self._cache[url]
        resp = requests.post(self.ENDPOINT, json={"url": url}, timeout=self.timeout)
        resp.raise_for_status()
        payload = resp.json()
        api_url = payload.get("api_url")
        if not payload.get("success") or not api_url:
            raise RuntimeError(f"SPFA did not return api_url for {url}")
        self._cache[url] = api_url
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            self.cache_path.write_text(json.dumps(self._cache, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass
        return api_url


class ParsePhone:
    """
    Batch phone number extractor via https://spfa.ru/api/phone/
    (ported from parser_avito/utils/parse_phone.py).
    """

    API_URL = "https://spfa.ru/api/phone/"
    BATCH_SIZE = 10

    def __init__(self, api_key: str, timeout: int = 30):
        self.api_key = api_key
        self.timeout = timeout

    @staticmethod
    def clean_phone(phone: Optional[str]) -> Optional[str]:
        import re
        if not phone or not isinstance(phone, str):
            return phone
        cleaned = re.sub(r"\D", "", phone)
        return cleaned if cleaned else phone

    def enrich_phones(self, items: list) -> list:
        import requests
        if not self.api_key or not items:
            return items
        phone_map: Dict[str, str] = {}
        for i in range(0, len(items), self.BATCH_SIZE):
            batch = items[i : i + self.BATCH_SIZE]
            ad_ids = [str(it.id) for it in batch if getattr(it, "has_phone", True)]
            if not ad_ids:
                continue
            try:
                resp = requests.post(
                    self.API_URL,
                    json={"api_key": self.api_key, "ads": ad_ids},
                    timeout=self.timeout,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("success") and isinstance(data.get("results"), list):
                        for entry in data["results"]:
                            if entry.get("ad_id") is not None and entry.get("phone"):
                                phone_map[str(entry["ad_id"])] = self.clean_phone(entry["phone"]) or ""
            except Exception as err:
                logger.warning(f"Phone batch extraction error: {err}")

        for it in items:
            if str(it.id) in phone_map:
                it.phone = phone_map[str(it.id)]
        return items

