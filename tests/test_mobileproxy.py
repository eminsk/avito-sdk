import io
import json
from unittest.mock import MagicMock, patch

import pytest

from avito_sdk.config import AvitoConfig, load_avito_config
from avito_sdk.http import SyncHttpTransport
from avito_sdk.mobileproxy import (
    DEFAULT_CHANGEIP_BASE,
    DEFAULT_REFERRAL_URL,
    MobileProxySpace,
)
from avito_sdk.client import AvitoClient


def test_mobileproxy_key_extraction():
    # 1. Full URL with params
    url = "https://changeip.mobileproxy.space/?proxy_key=secret_key_123&format=json"
    assert MobileProxySpace.extract_proxy_key(url) == "secret_key_123"

    # 2. Bare key string
    bare = "abc_key_456"
    assert MobileProxySpace.extract_proxy_key(bare) == "abc_key_456"

    # 3. None or empty
    assert MobileProxySpace.extract_proxy_key(None) is None
    assert MobileProxySpace.extract_proxy_key("") is None


def test_mobileproxy_build_change_url():
    url = MobileProxySpace.build_change_url("my_test_key", fmt="json")
    assert url == f"{DEFAULT_CHANGEIP_BASE}?proxy_key=my_test_key&format=json"


def test_mobileproxy_rotate_ip_mock():
    mps = MobileProxySpace(proxy_key="test_key_xyz", reconnect_delay=0.0)
    fake_response = io.BytesIO(
        json.dumps({
            "status": "SUCCESS",
            "new_ip": "178.62.204.10",
            "message": "IP changed successfully",
        }).encode("utf-8")
    )

    with patch("urllib.request.urlopen", return_value=fake_response):
        result = mps.rotate_ip(wait_reconnect=False)

    assert result["success"] is True
    assert result["status"] == "SUCCESS"
    assert result["new_ip"] == "178.62.204.10"
    assert mps.rotations_count == 1
    assert mps.last_ip == "178.62.204.10"


def test_sync_http_transport_mobileproxy_key():
    transport = SyncHttpTransport(
        mobileproxy_key="carrier_key_999",
        proxy="http://user:pass@1.2.3.4:8000",
    )
    assert transport.proxy_change_url == "https://changeip.mobileproxy.space/?proxy_key=carrier_key_999&format=json"
    assert transport.mobileproxy_key == "carrier_key_999"

    fake_response = io.BytesIO(b'{"status": "SUCCESS", "new_ip": "95.24.11.22"}')
    with patch("urllib.request.urlopen", return_value=fake_response):
        rotated = transport.rotate_proxy_ip()
    assert rotated is True
    assert transport.ip_rotations == 1


def test_avito_config_mobileproxy_key(tmp_path):
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        """
[avito]
urls = ["https://www.avito.ru/moskva/noutbuki"]
mobileproxy_key = "tok_mobile_444"
proxy_string = "http://login:pwd@proxy.net:9000"
count = 2
        """,
        encoding="utf-8",
    )

    cfg = load_avito_config(config_file)
    assert cfg.mobileproxy_key == "tok_mobile_444"
    assert cfg.proxy_change_url == "https://changeip.mobileproxy.space/?proxy_key=tok_mobile_444&format=json"
    assert cfg.proxy_string == "http://login:pwd@proxy.net:9000"


def test_avito_client_with_mobileproxy_key():
    client = AvitoClient(
        mobileproxy_key="auto_key_777",
        tracker_db=None,
        enable_tracking=False,
    )
    assert client.transport.proxy_change_url == "https://changeip.mobileproxy.space/?proxy_key=auto_key_777&format=json"
    assert client.transport.mobileproxy_key == "auto_key_777"
