"""
HTTP engine supporting both sync and async requests with TLS fingerprint impersonation.
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


class SyncHttpTransport:
    """Synchronous HTTP transport."""

    def __init__(
        self,
        proxy: Optional[str] = None,
        timeout: int = 25,
        max_retries: int = 3,
        impersonate: str = "chrome",
    ):
        self.proxy = proxy
        self.timeout = timeout
        self.max_retries = max_retries
        self.impersonate = impersonate
        self._session = self._create_session()

    def _create_session(self):
        try:
            from curl_cffi import requests as cffi_requests
            session = cffi_requests.Session(impersonate=self.impersonate)
            if self.proxy:
                session.proxies = {"http": self.proxy, "https": self.proxy}
            return session
        except ImportError:
            import requests
            session = requests.Session()
            if self.proxy:
                session.proxies = {"http": self.proxy, "https": self.proxy}
            return session

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
                    delay = 1.5 * attempt + random.uniform(0.5, 1.5)
                    logger.warning(
                        f"Rate limited ({resp.status_code}) on {url}. Retrying in {delay:.1f}s"
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
    """Asynchronous HTTP transport."""

    def __init__(
        self,
        proxy: Optional[str] = None,
        timeout: int = 25,
        max_retries: int = 3,
        impersonate: str = "chrome",
    ):
        self.proxy = proxy
        self.timeout = timeout
        self.max_retries = max_retries
        self.impersonate = impersonate
        self._session = None

    async def _get_session(self):
        if self._session is None:
            try:
                from curl_cffi.requests import AsyncSession
                self._session = AsyncSession(impersonate=self.impersonate)
                if self.proxy:
                    self._session.proxies = {"http": self.proxy, "https": self.proxy}
            except ImportError:
                import httpx
                self._session = httpx.AsyncClient(proxy=self.proxy, timeout=self.timeout)
        return self._session

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
