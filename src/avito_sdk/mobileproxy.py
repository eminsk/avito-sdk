"""
MobileProxy.space integration for avito-sdk.
Provides programmatic IP rotation, modem re-connection handling,
and seamless proxy management using real 4G/LTE mobile carriers.
"""

from __future__ import annotations

import json
import logging
import time
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("avito_sdk")

DEFAULT_CHANGEIP_BASE = "https://changeip.mobileproxy.space/"
DEFAULT_REFERRAL_URL = "https://mobileproxy.space/?p=8052683359"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)


class MobileProxySpace:
    """Helper client for MobileProxy.space dynamic IP rotation and carrier management."""

    def __init__(
        self,
        proxy_key: Optional[str] = None,
        proxy_url: Optional[str] = None,
        change_url: Optional[str] = None,
        reconnect_delay: float = 4.0,
        api_token: Optional[str] = None,
    ):
        self.proxy_key = proxy_key or self.extract_proxy_key(change_url)
        self.proxy_url = proxy_url
        self.change_url = change_url or (self.build_change_url(self.proxy_key) if self.proxy_key else None)
        self.reconnect_delay = reconnect_delay
        self.api_token = api_token
        self.last_rotation_ts = 0.0
        self.last_ip: Optional[str] = None
        self.rotations_count = 0

    @staticmethod
    def extract_proxy_key(url_or_key: Optional[str]) -> Optional[str]:
        """Extract proxy_key from a full URL or return the raw key if already bare."""
        if not url_or_key:
            return None
        url_or_key = url_or_key.strip()
        if "://" in url_or_key or "proxy_key=" in url_or_key:
            parsed = urllib.parse.urlparse(url_or_key)
            query = urllib.parse.parse_qs(parsed.query)
            if "proxy_key" in query and query["proxy_key"]:
                return query["proxy_key"][0]
        # Otherwise assume it's directly the proxy_key string
        return url_or_key

    @staticmethod
    def build_change_url(proxy_key: str, fmt: str = "json") -> str:
        """Construct the standard MobileProxy.space rotation URL."""
        clean_key = proxy_key.strip()
        return f"{DEFAULT_CHANGEIP_BASE}?proxy_key={urllib.parse.quote(clean_key)}&format={fmt}"

    @classmethod
    def from_key(cls, proxy_key: str, proxy_url: Optional[str] = None) -> "MobileProxySpace":
        """Instantiate MobileProxySpace from a proxy key."""
        return cls(proxy_key=proxy_key, proxy_url=proxy_url)

    @classmethod
    def from_url(cls, change_url: str, proxy_url: Optional[str] = None) -> "MobileProxySpace":
        """Instantiate MobileProxySpace from a full change-IP URL."""
        return cls(change_url=change_url, proxy_url=proxy_url)

    def rotate_ip(self, wait_reconnect: bool = True, timeout: int = 15) -> Dict[str, Any]:
        """
        Trigger an instant IP rotation via MobileProxy.space modem reconnect.
        Waits for modem re-association with the mobile cell tower.
        """
        if not self.change_url:
            raise ValueError(
                "Cannot rotate IP: Neither proxy_key nor change_url is configured. "
                f"Get your proxy and rotation key at {DEFAULT_REFERRAL_URL}"
            )

        logger.info("[MobileProxy.space] Triggering modem reconnect & IP rotation...")
        req = urllib.request.Request(
            self.change_url,
            headers={"User-Agent": DEFAULT_USER_AGENT},
        )

        result: Dict[str, Any] = {"status": "UNKNOWN", "raw": ""}
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw_bytes = resp.read()
                raw_text = raw_bytes.decode("utf-8", errors="replace").strip()
                result["raw"] = raw_text

                # Try parsing JSON if requested format=json
                try:
                    data = json.loads(raw_text)
                    if isinstance(data, dict):
                        result.update(data)
                        if "new_ip" in data:
                            self.last_ip = data["new_ip"]
                except Exception:
                    result["message"] = raw_text

            self.rotations_count += 1
            self.last_rotation_ts = time.monotonic()

            if wait_reconnect and self.reconnect_delay > 0:
                logger.debug(
                    f"[MobileProxy.space] Waiting {self.reconnect_delay:.1f}s for mobile carrier reconnection..."
                )
                time.sleep(self.reconnect_delay)

            result["success"] = True
            logger.info(
                f"[MobileProxy.space] IP rotation successful (total: {self.rotations_count}). New IP: {self.last_ip or 'OK'}"
            )
            return result

        except Exception as err:
            logger.warning(f"[MobileProxy.space] Failed to rotate IP: {err}")
            result["success"] = False
            result["error"] = str(err)
            return result

    def get_current_ip(self, timeout: int = 10) -> Optional[str]:
        """Check the current public IP through the configured proxy."""
        check_urls = ["https://api.ipify.org?format=json", "https://ifconfig.me/ip"]
        opener = urllib.request.build_opener()
        if self.proxy_url:
            opener.add_handler(
                urllib.request.ProxyHandler({"http": self.proxy_url, "https": self.proxy_url})
            )
        for u in check_urls:
            try:
                req = urllib.request.Request(u, headers={"User-Agent": DEFAULT_USER_AGENT})
                with opener.open(req, timeout=timeout) as resp:
                    data = resp.read().decode("utf-8").strip()
                    if "{" in data:
                        parsed = json.loads(data)
                        return parsed.get("ip")
                    return data
            except Exception:
                continue
        return None
