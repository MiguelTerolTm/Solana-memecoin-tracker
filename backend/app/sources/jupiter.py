"""
Adaptador de Jupiter Price API (lite-api.jup.ag).

TERCERA fuente en la cadena de fallback de mercado — Jupiter no da
liquidez ni volumen, solo precio, así que se usa como último recurso
cuando DexScreener y GeckoTerminal fallan, o como validación cruzada de
precio.

IMPORTANTE (ver docs/data-sources.md): Jupiter migró su plataforma de
desarrolladores en 2026; hay que reconfirmar el rate limit real de este
endpoint "lite" cuando se despliegue, puede haber cambiado.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.aggregation.schemas import MarketSnapshot
from app.sources.base import MarketDataSource
from app.utils.http import http_client, cache

BASE_URL = "https://lite-api.jup.ag/price/v2"
CACHE_TTL_SECONDS = 15


class JupiterSource(MarketDataSource):
    name = "jupiter"

    async def get_market_snapshot(self, mint: str) -> MarketSnapshot:
        cache_key = f"jupiter:price:{mint}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        data = await http_client.get_json(
            self.name,
            BASE_URL,
            params={"ids": mint},
        )
        entry = (data.get("data") or {}).get(mint)
        if not entry:
            raise ValueError(f"Jupiter no tiene precio para el mint {mint}")

        snapshot = MarketSnapshot(
            mint=mint,
            symbol=None,
            price_usd=_to_float(entry.get("price")),
            liquidity_usd=None,
            fdv_usd=None,
            market_cap_usd=None,
            volume_24h_usd=None,
            price_change_24h_pct=None,
            pair_created_at=None,
            dex=None,
            pair_address=None,
            source=self.name,
            fetched_at=datetime.now(timezone.utc),
        )
        cache.set(cache_key, snapshot, CACHE_TTL_SECONDS)
        return snapshot


def _to_float(value) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None
