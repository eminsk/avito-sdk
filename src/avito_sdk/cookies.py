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

    def fetch_cookies(self, target_url: Optional[str] = None) -> Tuple[Dict[str, str], str]:
        """Synchronous wrapper for fetch_cookies_async."""
        return asyncio.run(self.fetch_cookies_async(target_url=target_url))
