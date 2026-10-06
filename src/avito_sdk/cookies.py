"""
Playwright-based cookie harvesting and anti-bot bypass for Avito (PlaywrightCookieProvider).
Ported and modernized from Duff89/parser_avito (get_cookies.py & playwright_setup.py):
- Automatic Chromium installation check
- Built-in stealth JS injection + optional playwright-stealth integration
- Flexible mobile proxy parsing (user:pass@ip:port, ip:port@user:pass, ip:port:user:pass)
- Automatic IP block detection ("проблема с ip") with mobile proxy IP rotation
- Extracts 'ft' session cookies and matching User-Agent for SyncHttpTransport / AsyncHttpTransport
"""

from __future__ import annotations

import asyncio
import logging
import os
import random
import subprocess
import sys
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
import urllib.request

logger = logging.getLogger("avito_sdk")

BAD_IP_TITLE = "проблема с ip"
DEFAULT_PLAYWRIGHT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/140.0.0.0 Safari/537.36"
)


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


def ensure_playwright_chromium() -> None:
    """Ensure Playwright Chromium browser binary is installed."""
    if not os.environ.get("PLAYWRIGHT_BROWSERS_PATH"):
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "0"
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            exec_path = p.chromium.executable_path
            if exec_path and os.path.exists(exec_path):
                return
    except Exception:
        pass

    logger.info("Installing Playwright Chromium browser...")
    subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        check=False,
    )


class PlaywrightCookieProvider:
    """
    Headless Chromium cookie harvester using Playwright + Mobile Proxy.
    Obtains valid Avito session cookies ('ft', etc.) and rotates mobile IP if blocked.
    """

    def __init__(
        self,
        proxy: Optional[str] = None,
        proxy_change_url: Optional[str] = None,
        headless: bool = True,
        user_agent: Optional[str] = None,
        max_retries: int = 3,
    ):
        self.parsed_proxy = parse_proxy_config(proxy, proxy_change_url)
        self.headless = headless
        self.user_agent = user_agent or DEFAULT_PLAYWRIGHT_UA
        self.max_retries = max_retries
        self.ip_rotations = 0

    @staticmethod
    def parse_cookie_string(cookie_str: str) -> Dict[str, str]:
        return dict(pair.split("=", 1) for pair in cookie_str.split("; ") if "=" in pair)

    async def rotate_ip(self) -> bool:
        """Rotate mobile proxy IP via change_ip_url."""
        if not self.parsed_proxy or not self.parsed_proxy.change_ip_url:
            logger.warning("IP blocked, but no proxy_change_url provided. Waiting 30s...")
            await asyncio.sleep(30)
            return False

        url = self.parsed_proxy.change_ip_url
        for attempt in range(1, self.max_retries + 1):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
                await asyncio.to_thread(urllib.request.urlopen, req, timeout=20)
                self.ip_rotations += 1
                logger.info(f"Mobile proxy IP rotated via PlaywrightCookieProvider (#{self.ip_rotations})")
                await asyncio.sleep(3.0)
                return True
            except Exception as err:
                logger.warning(f"[{attempt}/{self.max_retries}] Mobile proxy IP rotation error: {err}")
                await asyncio.sleep(5.0)
        return False

    @staticmethod
    async def _apply_stealth(page) -> None:
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
            Object.defineProperty(navigator, 'vendor', { get: () => 'Google Inc.' });
            window.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
            Object.defineProperty(navigator, 'languages', { get: () => ['ru-RU', 'ru', 'en-US', 'en'] });
        """)

    async def fetch_cookies_async(self, target_url: Optional[str] = None) -> Tuple[Dict[str, str], str]:
        """Launch Playwright Chromium, bypass anti-bot challenge, and return (cookies, user_agent)."""
        try:
            from playwright.async_api import async_playwright
        except ImportError as exc:
            raise ImportError(
                "Playwright is required for browser cookie harvesting. "
                "Install it with: pip install 'avito-sdk[browser]' && playwright install chromium"
            ) from exc

        ensure_playwright_chromium()
        url = target_url or f"https://www.avito.ru/{random.randint(1111111111, 9999999999)}"

        stealth_cm = None
        try:
            from playwright_stealth import Stealth
            stealth_cm = Stealth().use_async(async_playwright())
            pw = await stealth_cm.__aenter__()
        except ImportError:
            stealth_cm = async_playwright()
            pw = await stealth_cm.__aenter__()

        browser = None
        try:
            launch_args = {
                "headless": self.headless,
                "chromium_sandbox": False,
                "args": [
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--start-maximized",
                    "--window-size=1920,1080",
                ],
            }
            browser = await pw.chromium.launch(**launch_args)

            context_args = {
                "user_agent": self.user_agent,
                "viewport": {"width": 1920, "height": 1080},
                "screen": {"width": 1920, "height": 1080},
                "device_scale_factor": 1,
                "is_mobile": False,
                "has_touch": False,
            }
            if self.parsed_proxy:
                proxy_cfg = {"server": self.parsed_proxy.server}
                if self.parsed_proxy.username:
                    proxy_cfg["username"] = self.parsed_proxy.username
                if self.parsed_proxy.password:
                    proxy_cfg["password"] = self.parsed_proxy.password
                context_args["proxy"] = proxy_cfg

            context = await browser.new_context(**context_args)
            page = await context.new_page()
            await self._apply_stealth(page)

            await page.goto(url, timeout=60_000, wait_until="domcontentloaded")

            for _ in range(10):
                title = (await page.title() or "").lower()
                if BAD_IP_TITLE in title:
                    logger.info("Avito IP block detected in Playwright; rotating mobile proxy IP...")
                    await context.clear_cookies()
                    await self.rotate_ip()
                    await page.reload(timeout=60_000)

                raw_cookie = await page.evaluate("() => document.cookie")
                cookie_dict = self.parse_cookie_string(raw_cookie)
                if cookie_dict.get("ft"):
                    logger.info("Avito session cookies ('ft') successfully obtained via Playwright!")
                    return cookie_dict, self.user_agent
                await asyncio.sleep(4.0)

            # Fallback to context cookies if document.cookie didn't expose 'ft'
            ctx_cookies = await context.cookies()
            fallback_dict = {c["name"]: c["value"] for c in ctx_cookies if "name" in c and "value" in c}
            return fallback_dict, self.user_agent
        finally:
            if browser:
                await browser.close()
            if stealth_cm:
                await stealth_cm.__aexit__(None, None, None)

    def fetch_cookies(
        self,
        target_url: Optional[str] = None,
        storage_path: Optional[str] = None,
        force_refresh: bool = False,
    ) -> Tuple[Dict[str, str], str]:
        """Synchronous wrapper for fetch_cookies_async with optional disk caching (OwnCookiesProvider style)."""
        if storage_path and not force_refresh:
            from pathlib import Path
            import json
            p = Path(storage_path)
            if p.exists():
                try:
                    data = json.loads(p.read_text(encoding="utf-8"))
                    cached = data.get("cookies")
                    ua = data.get("user_agent") or self.user_agent
                    if isinstance(cached, dict) and cached:
                        return cached, ua
                except Exception:
                    pass

        cookies, ua = asyncio.run(self.fetch_cookies_async(target_url=target_url))
        if storage_path and cookies:
            from pathlib import Path
            import json
            import time
            p = Path(storage_path)
            try:
                p.parent.mkdir(parents=True, exist_ok=True)
                tmp = p.with_suffix(".tmp")
                tmp.write_text(
                    json.dumps(
                        {"cookies": cookies, "user_agent": ua, "saved_at": time.time()},
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )
                tmp.replace(p)
            except Exception:
                pass
        return cookies, ua


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

