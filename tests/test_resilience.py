"""Suite C — Unitarias de la capa de resiliencia (Slice 3-B: reintento + backoff).

Mockea http_client y asyncio.sleep para no hacer llamadas reales ni esperar.
"""

import asyncio
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.core import resilience


def _resp(status):
    return httpx.Response(status_code=status, request=httpx.Request("GET", "http://x"))


class TestResiliencia:
    def test_exito_al_primer_intento(self):
        mock = AsyncMock(return_value=_resp(200))
        with patch.object(resilience.http_client, "request", new=mock):
            r = asyncio.run(resilience.resilient_get("http://x"))
        assert r.status_code == 200
        assert mock.call_count == 1

    def test_reintenta_ante_503_y_luego_exito(self):
        mock = AsyncMock(side_effect=[_resp(503), _resp(200)])
        with (
            patch.object(resilience.http_client, "request", new=mock),
            patch("app.core.resilience.asyncio.sleep", new=AsyncMock()),
        ):
            r = asyncio.run(resilience.resilient_get("http://x"))
        assert r.status_code == 200
        assert mock.call_count == 2  # un reintento

    def test_agota_reintentos_ante_503_persistente(self):
        mock = AsyncMock(side_effect=[_resp(503), _resp(503), _resp(503)])
        with (
            patch.object(resilience.http_client, "request", new=mock),
            patch("app.core.resilience.asyncio.sleep", new=AsyncMock()),
        ):
            r = asyncio.run(resilience.resilient_get("http://x"))
        assert r.status_code == 503
        assert mock.call_count == resilience._MAX_ATTEMPTS  # 3 intentos

    def test_reintenta_ante_connect_error_y_propaga(self):
        mock = AsyncMock(side_effect=httpx.ConnectError("down"))
        with (
            patch.object(resilience.http_client, "request", new=mock),
            patch("app.core.resilience.asyncio.sleep", new=AsyncMock()),
        ):
            with pytest.raises(httpx.ConnectError):
                asyncio.run(resilience.resilient_post("http://x", json={}))
        assert mock.call_count == resilience._MAX_ATTEMPTS
