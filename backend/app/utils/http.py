"""
Cliente HTTP compartido para todos los adaptadores de fuentes de datos.

Filosofía de diseño (ver docs/data-sources.md):
- Nunca asumimos un rate limit fijo: leemos las cabeceras 429 / Retry-After
  y hacemos backoff exponencial con jitter en vez de un número "quemado".
- Cada fuente externa puede fallar o cambiar sus límites sin aviso (ya nos
  pasó con Solscan y con pump.fun): un fallo aquí nunca debe tumbar el
  proceso, solo se propaga como excepción para que el orquestador de
  fallback (aggregation/orchestrator.py) pruebe la siguiente fuente.
"""
from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass
from typing import Any, Optional

import httpx


class SourceUnavailableError(Exception):
    """Se lanza cuando una fuente externa falla tras agotar los reintentos."""

    def __init__(self, source: str, detail: str):
        self.source = source
        self.detail = detail
        super().__init__(f"[{source}] no disponible: {detail}")


class RateLimitedError(SourceUnavailableError):
    """Caso específico de 429, útil para que el orquestador decida más rápido."""


@dataclass
class TTLCacheEntry:
    value: Any
    expires_at: float


class TTLCache:
    """
    Caché en memoria muy simple con expiración por clave.

    No es multi-proceso ni persistente a propósito: para el MVP local basta,
    y aísla la lógica de caché detrás de esta clase para poder sustituirla
    por Redis más adelante sin tocar los adaptadores.
    """

    def __init__(self) -> None:
        self._store: dict[str, TTLCacheEntry] = {}

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if entry is None:
            return None
        if entry.expires_at < time.monotonic():
            del self._store[key]
            return None
        return entry.value

    def set(self, key: str, value: Any, ttl_seconds: float) -> None:
        self._store[key] = TTLCacheEntry(value=value, expires_at=time.monotonic() + ttl_seconds)


class ResilientClient:
    """
    Envoltorio sobre httpx.AsyncClient con:
    - reintentos con backoff exponencial + jitter
    - respeto de Retry-After cuando el servidor lo manda
    - timeout explícito por request (nunca colgarse indefinidamente)

    IMPORTANTE: esto NO garantiza que una fuente "gratis" siga siendo gratis
    mañana. Solo hace que, cuando falle, falle de forma limpia y rápida
    para que el fallback entre en acción.
    """

    def __init__(self, timeout_seconds: float = 8.0, max_retries: int = 2):
        self._timeout = timeout_seconds
        self._max_retries = max_retries
        self._client = httpx.AsyncClient(timeout=timeout_seconds)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def get_json(
        self,
        source_name: str,
        url: str,
        *,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> Any:
        last_error: Optional[str] = None
        for attempt in range(self._max_retries + 1):
            try:
                resp = await self._client.get(url, params=params, headers=headers)
            except httpx.RequestError as exc:
                last_error = f"error de red: {exc}"
                await self._sleep_backoff(attempt)
                continue

            if resp.status_code == 429:
                retry_after = resp.headers.get("Retry-After")
                wait_s = float(retry_after) if retry_after else self._backoff_delay(attempt)
                if attempt == self._max_retries:
                    raise RateLimitedError(source_name, f"429 tras {attempt + 1} intentos")
                await asyncio.sleep(wait_s)
                continue

            if resp.status_code >= 500:
                last_error = f"HTTP {resp.status_code}"
                await self._sleep_backoff(attempt)
                continue

            if resp.status_code >= 400:
                # Error del cliente (404, 400...) no tiene sentido reintentarlo igual.
                raise SourceUnavailableError(source_name, f"HTTP {resp.status_code}: {resp.text[:200]}")

            try:
                return resp.json()
            except ValueError as exc:
                raise SourceUnavailableError(source_name, f"respuesta no-JSON: {exc}") from exc

        raise SourceUnavailableError(source_name, last_error or "fallo desconocido")

    def _backoff_delay(self, attempt: int) -> float:
        base = min(2 ** attempt, 8)
        return base + random.uniform(0, 0.5)

    async def _sleep_backoff(self, attempt: int) -> None:
        await asyncio.sleep(self._backoff_delay(attempt))


# Instancias compartidas a nivel de proceso (una sola conexión pool reutilizada).
http_client = ResilientClient()
cache = TTLCache()
