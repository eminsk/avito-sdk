import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from avito_sdk.http import SyncHttpTransport, AsyncHttpTransport, get_ca_bundle, _normalize_ca_path


def test_get_ca_bundle_env(monkeypatch):
    with tempfile.NamedTemporaryFile(suffix=".pem", delete=False) as f:
        fake_cert = f.name
    try:
        monkeypatch.setenv("CURL_CA_BUNDLE", fake_cert)
        assert get_ca_bundle() == fake_cert
    finally:
        if os.path.exists(fake_cert):
            os.remove(fake_cert)


def test_get_ca_bundle_meipass(monkeypatch):
    monkeypatch.delenv("CURL_CA_BUNDLE", raising=False)
    monkeypatch.delenv("REQUESTS_CA_BUNDLE", raising=False)
    monkeypatch.delenv("SSL_CERT_FILE", raising=False)

    with tempfile.TemporaryDirectory() as tmp_dir:
        cert_dir = Path(tmp_dir) / "certifi"
        cert_dir.mkdir(parents=True, exist_ok=True)
        cert_file = cert_dir / "cacert.pem"
        cert_file.write_text("dummy", encoding="utf-8")

        monkeypatch.setattr(sys, "_MEIPASS", tmp_dir, raising=False)
        with patch("certifi.where", return_value=r"C:\nonexistent\cacert.pem"):
            bundle = get_ca_bundle()
            assert bundle == str(cert_file)


def test_get_ca_bundle_missing_returns_false(monkeypatch):
    monkeypatch.delenv("CURL_CA_BUNDLE", raising=False)
    monkeypatch.delenv("REQUESTS_CA_BUNDLE", raising=False)
    monkeypatch.delenv("SSL_CERT_FILE", raising=False)
    if hasattr(sys, "_MEIPASS"):
        monkeypatch.delattr(sys, "_MEIPASS", raising=False)

    with patch("certifi.where", return_value=r"C:\nonexistent\cacert.pem"):
        bundle = get_ca_bundle()
        assert bundle is False


def test_sync_transport_recovers_from_curl_77():
    transport = SyncHttpTransport(verify=r"C:\fake\broken\cacert.pem")
    assert transport.verify == r"C:\fake\broken\cacert.pem"

    fake_resp = MagicMock()
    fake_resp.status_code = 200
    fake_resp.raise_for_status = MagicMock()
    fake_resp.text = "ok"

    calls = 0

    mock_sess = MagicMock()

    def mock_request(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise Exception("curl: (77) error setting certificate verify locations")
        return fake_resp

    mock_sess.request = mock_request
    mock_sess.close = MagicMock()

    with patch.object(transport, "_create_session", return_value=mock_sess):
        transport._session = mock_sess
        transport._thread_local.session = mock_sess
        resp = transport.request("GET", "https://m.avito.ru/api/1/card/items/123", allow_rotation=False)
        assert resp == fake_resp
        assert transport.verify is False
        assert calls == 2


def test_async_transport_recovers_from_curl_77():
    import asyncio

    async def _run():
        transport = AsyncHttpTransport(verify=r"C:\fake\broken\cacert.pem")
        assert transport.verify == r"C:\fake\broken\cacert.pem"

        fake_resp = MagicMock()
        fake_resp.status_code = 200
        fake_resp.raise_for_status = MagicMock()
        fake_resp.text = "ok"

        calls = 0

        mock_sess = MagicMock()

        async def mock_request(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise Exception("curl: (77) error setting certificate verify locations")
            return fake_resp

        mock_sess.request = mock_request
        mock_sess.close = MagicMock()

        with patch.object(transport, "_get_session", return_value=mock_sess):
            resp = await transport.request("GET", "https://m.avito.ru/api/1/card/items/123")
            assert resp == fake_resp
            assert transport.verify is False
            assert calls == 2

    asyncio.run(_run())
