"""Capa de resiliencia del bridge a v1 (Slice 3-B).

Razon de existir del intermediario (ACL): aislar al frontend de la inestabilidad
del backend legacy. Estas envolturas reintentan las llamadas a v1 ante fallos
transitorios (conexion, timeout, 502/503/504) con backoff acotado antes de
propagar el error. Es una capacidad que ni v1 ni el frontend proveen hoy.
"""

import asyncio
import logging

import httpx

from app.core.http_client import http_client

logger = logging.getLogger(__name__)

_TRANSIENT_STATUS = {502, 503, 504}
_MAX_ATTEMPTS = 3
_BASE_BACKOFF = 0.25  # segundos; backoff lineal: 0.25, 0.50, ...


async def resilient_get(url, **kwargs):
    return await _request("GET", url, **kwargs)


async def resilient_post(url, **kwargs):
    return await _request("POST", url, **kwargs)


async def _request(method, url, **kwargs):
    last_exc = None
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            response = await http_client.request(method, url, **kwargs)
            # Reintenta ante 5xx transitorios del bridge (p.ej. cold-start de v1).
            if response.status_code in _TRANSIENT_STATUS and attempt < _MAX_ATTEMPTS:
                logger.warning(
                    f"[resilience] {method} {url} -> {response.status_code}; "
                    f"reintento {attempt}/{_MAX_ATTEMPTS - 1}"
                )
                await asyncio.sleep(_BASE_BACKOFF * attempt)
                continue
            return response
        except httpx.TransportError as exc:
            # Errores de transporte (conexion/timeout/lectura) suelen ser transitorios.
            last_exc = exc
            if attempt < _MAX_ATTEMPTS:
                logger.warning(
                    f"[resilience] {method} {url} fallo transitorio "
                    f"({type(exc).__name__}); reintento {attempt}/{_MAX_ATTEMPTS - 1}"
                )
                await asyncio.sleep(_BASE_BACKOFF * attempt)
                continue
            raise
    if last_exc:
        raise last_exc
