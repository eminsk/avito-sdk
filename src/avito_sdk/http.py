"""
HTTP engine supporting both sync and async requests with TLS fingerprint impersonation
and automatic Mobile Proxy IP rotation (proxy_change_url).
Prefers curl_cffi when available; falls back cleanly to httpx/requests.
"""

from __future__ import annotations

import logging
import random
import time
from typing import Any, Dict, Optional

logger = logging.getLogger("avito_sdk")

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

MOBILE_USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Mobile Safari/537.36"
)

CARD_API_HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "referer": "https://m.avito.ru/",
    "sec-ch-ua": '"Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-mobile": "?1",
    "sec-ch-ua-platform": '"Android"',
    "user-agent": MOBILE_USER_AGENT,
}

WEB_HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "referer": "https://www.avito.ru/",
    "user-agent": DEFAULT_USER_AGENT,
}


def normalize_proxy(proxy: Optional[str]) -> Optional[str]:
    """Normalize proxy string to full URL scheme if omitted (e.g. user:pass@ip:port)."""
    if not proxy:
        return None
    proxy = proxy.strip()
    if "://" not in proxy:
        return f"http://{proxy}"
    return proxy


class SyncHttpTransport:
    """Synchronous HTTP transport with mobile proxy rotation support."""

    def __init__(
        self,
        proxy: Optional[str] = None,
        proxy_change_url: Optional[str] = None,
        cookies: Optional[Dict[str, str]] = None,
        use_playwright_cookies: bool = False,
        timeout: int = 25,
        max_retries: int = 3,
        impersonate: str = "chrome",
    ):
        self.proxy = normalize_proxy(proxy)
        self.proxy_change_url = proxy_change_url
        self.cookies: Dict[str, str] = dict(cookies) if cookies else {}
        self.use_playwright_cookies = use_playwright_cookies
        self.timeout = timeout
        self.max_retries = max_retries
        self.impersonate = impersonate
        self.ip_rotations = 0
        self._session = self._create_session()
        if self.use_playwright_cookies and not self.cookies:
            self.refresh_cookies()

    def _create_session(self):
        try:
            from curl_cffi import requests as cffi_requests
            session = cffi_requests.Session(impersonate=self.impersonate)
            if self.proxy:
                session.proxies = {"http": self.proxy, "https": self.proxy}
            if self.cookies:
                session.cookies.update(self.cookies)
            return session
        except ImportError:
            import requests
            session = requests.Session()
            if self.proxy:
                session.proxies = {"http": self.proxy, "https": self.proxy}
            if self.cookies:
                session.cookies.update(self.cookies)
            return session

    def refresh_cookies(self, target_url: Optional[str] = None) -> Dict[str, str]:
        """Obtain fresh Avito cookies via Playwright + Mobile Proxy."""
        from avito_sdk.cookies import PlaywrightCookieProvider
        provider = PlaywrightCookieProvider(
            proxy=self.proxy,
            proxy_change_url=self.proxy_change_url,
            headless=True,
        )
        new_cookies, _ = provider.fetch_cookies(target_url=target_url)
        self.ip_rotations += provider.ip_rotations
        if new_cookies:
            self.cookies.update(new_cookies)
            if hasattr(self._session, "cookies"):
                self._session.cookies.update(new_cookies)
        return self.cookies

    def rotate_proxy_ip(self) -> bool:
        """Trigger mobile proxy IP change via proxy_change_url."""
        if not self.proxy_change_url:
            return False
        try:
            import urllib.request
            logger.info("Rotating mobile proxy IP via proxy_change_url...")
            req = urllib.request.Request(
                self.proxy_change_url,
                headers={"User-Agent": DEFAULT_USER_AGENT},
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                logger.debug(f"Mobile proxy rotation status: {resp.status}")
            self.ip_rotations += 1
            time.sleep(2.5)
            return True
        except Exception as err:
            logger.warning(f"Failed to rotate mobile proxy IP: {err}")
            return False

    def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Any:
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self._session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    timeout=self.timeout,
                    **kwargs,
                )
                if resp.status_code in (403, 429):
                    if self.proxy_change_url:
                        self.rotate_proxy_ip()
                    if self.use_playwright_cookies:
                        try:
                            self.refresh_cookies(target_url=url)
                        except Exception as pw_err:
                            logger.warning(f"Playwright cookie refresh failed: {pw_err}")
                    elif not self.proxy_change_url:
                        delay = 1.5 * attempt + random.uniform(0.5, 1.5)
                        logger.warning(
                            f"Rate limited ({resp.status_code}) on {url}. "
                            f"Tip: Configure a Mobile Proxy (proxy + proxy_change_url) to avoid IP bans. "
                            f"Retrying in {delay:.1f}s"
                        )
                        time.sleep(delay)
                    continue

                resp.raise_for_status()
                return resp
            except Exception as e:
                last_error = e
                delay = 1.0 * attempt + random.uniform(0.2, 0.8)
                time.sleep(delay)

        raise RuntimeError(f"HTTP request failed after {self.max_retries} attempts: {url}") from last_error

    def fetch_item_card(self, item_id: int) -> dict:
        """Fetch mobile JSON card for an item."""
        url = f"https://m.avito.ru/api/1/card/items/{item_id}"
        resp = self.request("GET", url, headers=CARD_API_HEADERS.copy())
        data = resp.json()
        if isinstance(data, dict):
            return data
        return {}

    def fetch_html(self, url: str) -> str:
        """Fetch raw HTML for an Avito page."""
        resp = self.request("GET", url, headers=WEB_HEADERS.copy())
        return resp.text

    def close(self) -> None:
        if hasattr(self._session, "close"):
            self._session.close()


class AsyncHttpTransport:
    """Asynchronous HTTP transport with mobile proxy rotation support."""

    def __init__(
        self,
        proxy: Optional[str] = None,
        proxy_change_url: Optional[str] = None,
        cookies: Optional[Dict[str, str]] = None,
        use_playwright_cookies: bool = False,
        timeout: int = 25,
        max_retries: int = 3,
        impersonate: str = "chrome",
    ):
        self.proxy = normalize_proxy(proxy)
        self.proxy_change_url = proxy_change_url
        self.cookies: Dict[str, str] = dict(cookies) if cookies else {}
        self.use_playwright_cookies = use_playwright_cookies
        self.timeout = timeout
        self.max_retries = max_retries
        self.impersonate = impersonate
        self.ip_rotations = 0
        self._session = None

    async def _get_session(self):
        if self._session is None:
            if self.use_playwright_cookies and not self.cookies:
                await self.refresh_cookies()
            try:
                from curl_cffi.requests import AsyncSession
                self._session = AsyncSession(impersonate=self.impersonate)
                if self.proxy:
                    self._session.proxies = {"http": self.proxy, "https": self.proxy}
                if self.cookies:
                    self._session.cookies.update(self.cookies)
            except ImportError:
                import httpx
                self._session = httpx.AsyncClient(
                    proxy=self.proxy,
                    cookies=self.cookies,
                    timeout=self.timeout,
                )
        return self._session

    async def refresh_cookies(self, target_url: Optional[str] = None) -> Dict[str, str]:
        """Obtain fresh Avito cookies asynchronously via Playwright + Mobile Proxy."""
        from avito_sdk.cookies import PlaywrightCookieProvider
        provider = PlaywrightCookieProvider(
            proxy=self.proxy,
            proxy_change_url=self.proxy_change_url,
            headless=True,
        )
        new_cookies, _ = await provider.fetch_cookies_async(target_url=target_url)
        self.ip_rotations += provider.ip_rotations
        if new_cookies:
            self.cookies.update(new_cookies)
            if self._session and hasattr(self._session, "cookies"):
                self._session.cookies.update(new_cookies)
        return self.cookies

    async def rotate_proxy_ip(self) -> bool:
        """Trigger mobile proxy IP change asynchronously."""
        if not self.proxy_change_url:
            return False
        import asyncio
        try:
            import urllib.request
            logger.info("Rotating mobile proxy IP via proxy_change_url...")
            req = urllib.request.Request(
                self.proxy_change_url,
                headers={"User-Agent": DEFAULT_USER_AGENT},
            )
            await asyncio.to_thread(urllib.request.urlopen, req, timeout=15)
            self.ip_rotations += 1
            await asyncio.sleep(2.5)
            return True
        except Exception as err:
            logger.warning(f"Failed to rotate mobile proxy IP: {err}")
            return False

    async def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Any:
        import asyncio
        session = await self._get_session()
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                resp = await session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    timeout=self.timeout,
                    **kwargs,
                )
                if resp.status_code in (403, 429):
                    if self.proxy_change_url:
                        await self.rotate_proxy_ip()
                    if self.use_playwright_cookies:
                        try:
                            await self.refresh_cookies(target_url=url)
                        except Exception as pw_err:
                            logger.warning(f"Playwright async cookie refresh failed: {pw_err}")
                    elif not self.proxy_change_url:
                        delay = 1.5 * attempt + random.uniform(0.5, 1.5)
                        await asyncio.sleep(delay)
                    continue

                resp.raise_for_status()
                return resp
            except Exception as e:
                last_error = e
                await asyncio.sleep(1.0 * attempt + random.uniform(0.2, 0.8))

        raise RuntimeError(f"Async HTTP request failed after {self.max_retries} attempts: {url}") from last_error

    async def fetch_item_card(self, item_id: int) -> dict:
        url = f"https://m.avito.ru/api/1/card/items/{item_id}"
        resp = await self.request("GET", url, headers=CARD_API_HEADERS.copy())
        data = resp.json()
        if isinstance(data, dict):
            return data
        return {}

    async def fetch_html(self, url: str) -> str:
        resp = await self.request("GET", url, headers=WEB_HEADERS.copy())
        return resp.text

    async def close(self) -> None:
        if self._session and hasattr(self._session, "close"):
            res = self._session.close()
            import inspect
            if inspect.isawaitable(res):
                await res
