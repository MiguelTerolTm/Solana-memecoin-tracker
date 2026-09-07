"""
Adaptador de GeckoTerminal (API pública "keyless" de CoinGecko).

Documentado como activo y gratis sin key. El límite exacto por minuto varía
según la fuente consultada (~10-30 req/min) — NO lo hardcodeamos como
verdad absoluta; confiamos en ResilientClient para reaccionar a un 429 real
en vez de asumir un número. Ventaja sobre DexScreener: expone velas OHLC,
útil para calcular tendencia de precio sin depender de nuestra propia
base de datos histórica desde el primer día.

Se usa como SEGUNDA fuente en la cadena de fallback de mercado.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.aggregation.schemas import MarketSnapshot
from app.sources.base import MarketDataSource
from app.utils.http import http_client, cache

BASE_URL = "https://api.geckoterminal.com/api/v2"
CACHE_TTL_SECONDS = 30


class GeckoTerminalSource(MarketDataSource):
    name = "geckoterminal"

    async def get_market_snapshot(self, mint: str) -> MarketSnapshot:
        cache_key = f"geckoterminal:token:{mint}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        data = await http_client.get_json(
            self.name,
            f"{BASE_URL}/networks/solana/tokens/{mint}",
            headers={"Accept": "application/json;version=20230302"},
        )
        attrs = ((data.get("data") or {}).get("attributes")) or {}
        if not attrs:
            raise ValueError(f"GeckoTerminal no tiene datos para el mint {mint}")

        snapshot = MarketSnapshot(
            mint=mint,
            symbol=attrs.get("symbol"),
            price_usd=_to_float(attrs.get("price_usd")),
            liquidity_usd=_to_float(attrs.get("total_reserve_in_usd")),
            fdv_usd=_to_float(attrs.get("fdv_usd")),
            market_cap_usd=_to_float(attrs.get("market_cap_usd")),
            volume_24h_usd=_to_float((attrs.get("volume_usd") or {}).get("h24")),
            price_change_24h_pct=None,  # GeckoTerminal lo da vía endpoint de pools, no de token
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
