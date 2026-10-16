"""
HTTP engine supporting both sync and async requests with TLS fingerprint impersonation
and automatic Mobile Proxy IP rotation (proxy_change_url).
Prefers curl_cffi when available; falls back cleanly to httpx/requests.
"""

from __future__ import annotations

import logging
import random
import threading
import time
from typing import Any, Dict, Optional

logger = logging.getLogger("avito_sdk")

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

# Realistic modern Android profiles for seamless rotation without TLS fingerprint mismatch
MOBILE_PROFILES = [
    ("Android 14; Pixel 8", "131.0.6778.200", "131"),
    ("Android 14; Pixel 8 Pro", "131.0.6778.200", "131"),
    ("Android 14; SM-S918B", "131.0.6778.260", "131"),  # Samsung Galaxy S23 Ultra
    ("Android 14; SM-S928B", "131.0.6778.260", "131"),  # Samsung Galaxy S24 Ultra
    ("Android 13; 2210132G", "131.0.6778.135", "131"),  # Xiaomi 13
    ("Android 14; 23127PN0CG", "131.0.6778.200", "131"),  # Xiaomi 14
    ("Android 14; CPH2551", "131.0.6778.200", "131"),   # OnePlus Open
]


def get_random_mobile_headers(accept_html: bool = False) -> Dict[str, str]:
    """
    Generate realistic mobile headers with synchronized Android User-Agent and Client Hints.
    Strictly aligns with curl_cffi Chrome 131 TLS fingerprint to prevent Avito WAF blocks.
    """
    device, chrome_ver, major = random.choice(MOBILE_PROFILES)
    ua = (
        f"Mozilla/5.0 (Linux; {device}) "
        f"AppleWebKit/537.36 (KHTML, like Gecko) "
        f"Chrome/{chrome_ver} Mobile Safari/537.36"
    )
    accept = (
        "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        if accept_html
        else "application/json, text/plain, */*"
    )
    return {
        "accept": accept,
        "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "referer": "https://m.avito.ru/",
        "sec-ch-ua": f'"Chromium";v="{major}", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": '"Android"',
        "user-agent": ua,
    }


CARD_API_HEADERS = get_random_mobile_headers(accept_html=False)
MOBILE_SEARCH_HEADERS = get_random_mobile_headers(accept_html=True)

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
        mobileproxy_key: Optional[str] = None,
        cookies: Optional[Dict[str, str]] = None,
        use_playwright_cookies: bool = False,
        timeout: int = 25,
        max_retries: int = 3,
        impersonate: str = "chrome",
    ):
        self.proxy = normalize_proxy(proxy)
        if mobileproxy_key and not proxy_change_url:
            from avito_sdk.mobileproxy import MobileProxySpace
            self.proxy_change_url = MobileProxySpace.build_change_url(mobileproxy_key)
        else:
            self.proxy_change_url = proxy_change_url
        self.mobileproxy_key = mobileproxy_key
        self.cookies: Dict[str, str] = dict(cookies) if cookies else {}
        self.use_playwright_cookies = use_playwright_cookies
        if use_playwright_cookies and not self.cookies:
            from pathlib import Path
            import json
            cache_p = Path("storage/own_cookies.json")
            if cache_p.exists():
                try:
                    cdata = json.loads(cache_p.read_text(encoding="utf-8"))
                    if isinstance(cdata.get("cookies"), dict):
                        self.cookies.update(cdata["cookies"])
                except Exception:
                    pass
        self.timeout = timeout
        self.max_retries = max(max_retries, 5) if self.proxy_change_url else max_retries
        self.impersonate = impersonate
        self.ip_rotations = 0
        self._rotation_lock = threading.Lock()
        self._last_rotation_ts = 0.0
        self._session_generation = 0
        self._pacing_delay = 0.35 if self.proxy else 0.0
        self._thread_local = threading.local()
        self._session = self._create_session()

    def _get_thread_session(self):
        gen = getattr(self._thread_local, "generation", -1)
        sess = getattr(self._thread_local, "session", None)
        if sess is None or gen != self._session_generation:
            if sess is not None and hasattr(sess, "close"):
                try:
                    sess.close()
                except Exception:
                    pass
            sess = self._create_session()
            self._thread_local.session = sess
            self._thread_local.generation = self._session_generation
        return sess

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

    def refresh_cookies(
        self,
        target_url: Optional[str] = None,
        storage_path: Optional[str] = "storage/own_cookies.json",
        force_refresh: bool = False,
    ) -> Dict[str, str]:
        """Obtain fresh Avito cookies via Playwright + Mobile Proxy (with optional disk cache)."""
        from avito_sdk.cookies import PlaywrightCookieProvider
        with self._rotation_lock:
            provider = PlaywrightCookieProvider(
                proxy=self.proxy,
                proxy_change_url=self.proxy_change_url,
                headless=True,
            )
            new_cookies, _ = provider.fetch_cookies(
                target_url=target_url,
                storage_path=storage_path,
                force_refresh=force_refresh,
            )
            self.ip_rotations += provider.ip_rotations
            if new_cookies:
                self.cookies.update(new_cookies)
                if hasattr(self._session, "cookies"):
                    self._session.cookies.update(new_cookies)
                sess = getattr(self._thread_local, "session", None)
                if sess is not None and hasattr(sess, "cookies"):
                    sess.cookies.update(new_cookies)
            return self.cookies

    def rotate_proxy_ip(self) -> bool:
        """Trigger mobile proxy IP change via proxy_change_url (thread-safe for 3.15t/3.16t No-GIL)."""
        if not self.proxy_change_url:
            return False
        with self._rotation_lock:
            now = time.monotonic()
            if self._last_rotation_ts > 0 and (now - self._last_rotation_ts) < 4.0:
                return True

            rotated = False
            if "mobileproxy.space" in self.proxy_change_url:
                try:
                    from avito_sdk.mobileproxy import MobileProxySpace
                    mps = MobileProxySpace(change_url=self.proxy_change_url, reconnect_delay=3.5)
                    res = mps.rotate_ip(wait_reconnect=True)
                    if res.get("success"):
                        self.ip_rotations += 1
                        self._last_rotation_ts = time.monotonic()
                        rotated = True
                except Exception as err:
                    logger.warning(f"[MobileProxy.space] IP rotation failed: {err}")
                    return False
            else:
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
                    self._last_rotation_ts = time.monotonic()
                    time.sleep(3.5)
                    rotated = True
                except Exception as err:
                    logger.warning(f"Failed to rotate mobile proxy IP: {err}")
                    return False

            if rotated:
                # Advance session generation so ALL threads discard stale sockets and connect fresh
                self._session_generation += 1
                if hasattr(self._session, "close"):
                    try:
                        self._session.close()
                    except Exception:
                        pass
                self._session = self._create_session()
                sess = getattr(self._thread_local, "session", None)
                if sess and hasattr(sess, "close"):
                    try:
                        sess.close()
                    except Exception:
                        pass
                self._thread_local.session = None
                return True
            return False

    def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        allow_rotation: bool = True,
        **kwargs,
    ) -> Any:
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            session = self._get_thread_session()
            if self.cookies and hasattr(session, "cookies"):
                session.cookies.update(self.cookies)
            try:
                resp = session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    timeout=self.timeout,
                    **kwargs,
                )
                is_waf_challenge = resp.status_code in (429, 439) or (
                    resp.status_code == 200
                    and any(kw in resp.text.lower() for kw in ("проблема с ip", "доступ ограничен", "проверка безопасности"))
                ) or (
                    resp.status_code == 403
                    and any(kw in resp.text.lower() for kw in ("доступ ограничен", "проверка безопасности", "smartcaptcha"))
                )
                if is_waf_challenge:
                    logger.warning(f"Avito security challenge/block detected (status {resp.status_code}) on {url}")
                    if self.proxy_change_url and allow_rotation:
                        self.rotate_proxy_ip()
                        logger.info(
                            f"[ProxyAudit] 🔄 Ротация IP купленного мобильного прокси выполнена (причина: WAF {resp.status_code}). "
                            f"Всего ротаций в сессии: {self.ip_rotations}."
                        )
                        time.sleep(3.5)
                    elif not allow_rotation:
                        return resp
                    if self.use_playwright_cookies:
                        try:
                            self.refresh_cookies(target_url=url, force_refresh=True)
                        except Exception as pw_err:
                            logger.warning(f"Playwright cookie refresh failed: {pw_err}")
                    elif not self.proxy_change_url:
                        from avito_sdk.mobileproxy import DEFAULT_FREE_TRIAL_URL
                        delay = 1.5 * attempt + random.uniform(0.5, 1.5)
                        logger.warning(
                            f"[ProxyAudit] ⛔ Блокировка Avito WAF ({resp.status_code}) на {url}. "
                            f"ВНИМАНИЕ: Запрос выполнен БЕЗ купленного мобильного 4G-прокси с ротацией IP! "
                            f"Согласно регламенту, проблемы с блокировками без купленного мобильного прокси НЕ РАССМАТРИВАЮТСЯ. "
                            f"Для стабильной работы подключите MobileProxy.space (триал: {DEFAULT_FREE_TRIAL_URL})."
                        )
                        time.sleep(delay)
                    continue
                elif resp.status_code == 403:
                    if not allow_rotation:
                        return resp
                    # Transient 403 rate burst: pause briefly and retry without rotating mobile proxy
                    delay = 0.8 + random.uniform(0.2, 0.5)
                    time.sleep(delay)
                    continue

                if resp.status_code == 404:
                    return resp
                resp.raise_for_status()
                return resp
            except Exception as e:
                last_error = e
                # Clean up broken session so next attempt opens a brand new socket
                sess = getattr(self._thread_local, "session", None)
                if sess and hasattr(sess, "close"):
                    try:
                        sess.close()
                    except Exception:
                        pass
                self._thread_local.session = None

                if attempt >= 2 and self.proxy_change_url and allow_rotation:
                    logger.info(f"Connection issue on attempt {attempt} ({e}). Rotating mobile proxy IP...")
                    self.rotate_proxy_ip()

                delay = 1.0 * attempt + random.uniform(0.2, 0.8)
                time.sleep(delay)

        raise RuntimeError(f"HTTP request failed after {self.max_retries} attempts: {url}") from last_error

    def fetch_item_card(self, item_id: int) -> dict:
        """Fetch mobile JSON card for an item without causing unnecessary IP rotations."""
        if getattr(self, "_pacing_delay", 0) > 0:
            time.sleep(random.uniform(0.15, self._pacing_delay))
        url = f"https://m.avito.ru/api/1/card/items/{item_id}"
        headers = get_random_mobile_headers(accept_html=False)
        try:
            resp = self.request("GET", url, headers=headers, allow_rotation=False)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, dict):
                    return data
        except Exception as e:
            logger.debug(f"Card {item_id} fetch failed ({e}), skipping enrichment.")
        return {}

    def fetch_html(self, url: str, allow_rotation: bool = True) -> str:
        """Fetch raw HTML for an Avito page with automatic mobile routing and sort cleaning."""
        target_url = url
        headers = WEB_HEADERS.copy()
        if "avito.ru" in url:
            if "m.avito.ru" not in url:
                target_url = url.replace("https://www.avito.ru", "https://m.avito.ru").replace("http://www.avito.ru", "https://m.avito.ru")
                if "https://avito.ru" in target_url:
                    target_url = target_url.replace("https://avito.ru", "https://m.avito.ru")
                elif "http://avito.ru" in target_url:
                    target_url = target_url.replace("http://avito.ru", "https://m.avito.ru")
            # Convert desktop delivery param cd=1 -> mobile d=1
            import re
            target_url = re.sub(r'([?&])cd=1(?=&|$)', r'\1d=1', target_url)
            # Strip bot-flagging sort params (&s=104 and &s=101) which trigger 429 WAF blocks on mobile
            target_url = re.sub(r'[?&]s=(101|104)(?=&|$)', '', target_url)
            if "?" not in target_url and "&" in target_url:
                target_url = target_url.replace("&", "?", 1)
            headers = get_random_mobile_headers(accept_html=True)
        resp = self.request("GET", target_url, headers=headers, allow_rotation=allow_rotation)
        return resp.text

    def close(self) -> None:
        """Close main HTTP session and any active thread-local sessions to prevent dangling sockets."""
        if hasattr(self._session, "close"):
            try:
                self._session.close()
            except Exception:
                pass
        sess = getattr(self._thread_local, "session", None)
        if sess and hasattr(sess, "close"):
            try:
                sess.close()
            except Exception:
                pass
        self._thread_local.session = None


class AsyncHttpTransport:
    """Asynchronous HTTP transport with mobile proxy rotation support."""

    def __init__(
        self,
        proxy: Optional[str] = None,
        proxy_change_url: Optional[str] = None,
        mobileproxy_key: Optional[str] = None,
        cookies: Optional[Dict[str, str]] = None,
        use_playwright_cookies: bool = False,
        timeout: int = 25,
        max_retries: int = 3,
        impersonate: str = "chrome",
    ):
        self.proxy = normalize_proxy(proxy)
        if mobileproxy_key and not proxy_change_url:
            from avito_sdk.mobileproxy import MobileProxySpace
            self.proxy_change_url = MobileProxySpace.build_change_url(mobileproxy_key)
        else:
            self.proxy_change_url = proxy_change_url
        self.mobileproxy_key = mobileproxy_key
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
        if "mobileproxy.space" in self.proxy_change_url:
            try:
                from avito_sdk.mobileproxy import MobileProxySpace
                mps = MobileProxySpace(change_url=self.proxy_change_url, reconnect_delay=3.5)
                res = await asyncio.to_thread(mps.rotate_ip, True)
                if res.get("success"):
                    self.ip_rotations += 1
                    if self._session and hasattr(self._session, "close"):
                        try:
                            await self._session.close()
                        except Exception:
                            pass
                    self._session = None
                    return True
            except Exception as err:
                logger.warning(f"[MobileProxy.space] Async IP rotation failed: {err}")
                return False

        try:
            import urllib.request
            logger.info("Rotating mobile proxy IP via proxy_change_url...")
            req = urllib.request.Request(
                self.proxy_change_url,
                headers={"User-Agent": DEFAULT_USER_AGENT},
            )
            await asyncio.to_thread(urllib.request.urlopen, req, timeout=15)
            self.ip_rotations += 1
            await asyncio.sleep(3.5)
            if self._session and hasattr(self._session, "close"):
                try:
                    await self._session.close()
                except Exception:
                    pass
            self._session = None
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
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            session = await self._get_session()
            if self.cookies and hasattr(session, "cookies"):
                session.cookies.update(self.cookies)
            try:
                resp = await session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    timeout=self.timeout,
                    **kwargs,
                )
                is_blocked = resp.status_code in (403, 429, 439) or (
                    resp.status_code == 200
                    and any(kw in resp.text.lower() for kw in ("проблема с ip", "доступ ограничен", "проверка безопасности"))
                )
                if is_blocked:
                    logger.warning(f"Async Avito security challenge/block detected (status {resp.status_code}) on {url}")
                    if self.proxy_change_url:
                        await self.rotate_proxy_ip()
                        await asyncio.sleep(3.5)
                    if self.use_playwright_cookies:
                        try:
                            await self.refresh_cookies(target_url=url)
                        except Exception as pw_err:
                            logger.warning(f"Playwright async cookie refresh failed: {pw_err}")
                    elif not self.proxy_change_url:
                        from avito_sdk.mobileproxy import DEFAULT_FREE_TRIAL_URL
                        delay = 1.5 * attempt + random.uniform(0.5, 1.5)
                        logger.warning(
                            f"Async request rate limited ({resp.status_code}) on {url}. "
                            f"Tip: Use real 4G/LTE mobile proxies from MobileProxy.space (Free 3h trial: {DEFAULT_FREE_TRIAL_URL}) "
                            f"to avoid IP bans. Retrying in {delay:.1f}s"
                        )
                        await asyncio.sleep(delay)
                    continue

                resp.raise_for_status()
                return resp
            except Exception as e:
                last_error = e
                if self._session and hasattr(self._session, "close"):
                    try:
                        await self._session.close()
                    except Exception:
                        pass
                self._session = None
                if attempt >= 2 and self.proxy_change_url:
                    logger.info(f"Async connection issue on attempt {attempt} ({e}). Rotating mobile proxy IP...")
                    await self.rotate_proxy_ip()
                await asyncio.sleep(1.0 * attempt + random.uniform(0.2, 0.8))

        raise RuntimeError(f"Async HTTP request failed after {self.max_retries} attempts: {url}") from last_error

    async def fetch_item_card(self, item_id: int) -> dict:
        url = f"https://m.avito.ru/api/1/card/items/{item_id}"
        headers = get_random_mobile_headers(accept_html=False)
        resp = await self.request("GET", url, headers=headers)
        data = resp.json()
        if isinstance(data, dict):
            return data
        return {}

    async def fetch_html(self, url: str) -> str:
        """Fetch raw HTML for an Avito page with automatic mobile routing and sort cleaning."""
        target_url = url
        headers = WEB_HEADERS.copy()
        if "avito.ru" in url:
            if "m.avito.ru" not in url:
                target_url = url.replace("https://www.avito.ru", "https://m.avito.ru").replace("http://www.avito.ru", "https://m.avito.ru")
                if "https://avito.ru" in target_url:
                    target_url = target_url.replace("https://avito.ru", "https://m.avito.ru")
                elif "http://avito.ru" in target_url:
                    target_url = target_url.replace("http://avito.ru", "https://m.avito.ru")
            import re
            target_url = re.sub(r'([?&])cd=1(?=&|$)', r'\1d=1', target_url)
            target_url = re.sub(r'[?&]s=(101|104)(?=&|$)', '', target_url)
            if "?" not in target_url and "&" in target_url:
                target_url = target_url.replace("&", "?", 1)
            headers = get_random_mobile_headers(accept_html=True)
        resp = await self.request("GET", target_url, headers=headers)
        return resp.text

    async def close(self) -> None:
        if self._session and hasattr(self._session, "close"):
            res = self._session.close()
            import inspect
            if inspect.isawaitable(res):
                await res
