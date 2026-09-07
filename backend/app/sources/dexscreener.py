"""
Adaptador de DexScreener.

Verificado en vivo (ver docs/data-sources.md): responde hoy sin API key.
Límites aproximados y NO garantizados por contrato: ~300 req/min en
endpoints de pares. Sin histórico OHLCV. Sus términos de servicio prohíben
construir un producto que compita directamente con DexScreener: este
adaptador es para research interno, no para redistribuir su dato como
si fuera un DexScreener alternativo.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.aggregation.schemas import MarketSnapshot
from app.sources.base import MarketDataSource
from app.utils.http import http_client, cache

BASE_URL = "https://api.dexscreener.com/latest/dex"
CACHE_TTL_SECONDS = 20  # los precios de memecoins se mueven rápido; no cachear mucho


class DexScreenerSource(MarketDataSource):
    name = "dexscreener"

    async def get_market_snapshot(self, mint: str) -> MarketSnapshot:
        cache_key = f"dexscreener:token:{mint}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        data = await http_client.get_json(
            self.name,
            f"{BASE_URL}/tokens/{mint}",
        )
        pairs = data.get("pairs") or []
        if not pairs:
            raise ValueError(f"DexScreener no tiene pares para el mint {mint}")

        # Nos quedamos con el par de mayor liquidez (suele ser el más representativo).
        best = max(pairs, key=lambda p: (p.get("liquidity") or {}).get("usd") or 0)

        snapshot = MarketSnapshot(
            mint=mint,
            symbol=(best.get("baseToken") or {}).get("symbol"),
            price_usd=_to_float(best.get("priceUsd")),
            liquidity_usd=(best.get("liquidity") or {}).get("usd"),
            fdv_usd=best.get("fdv"),
            market_cap_usd=best.get("marketCap"),
            volume_24h_usd=(best.get("volume") or {}).get("h24"),
            price_change_24h_pct=(best.get("priceChange") or {}).get("h24"),
            pair_created_at=_ms_to_datetime(best.get("pairCreatedAt")),
            dex=best.get("dexId"),
            pair_address=best.get("pairAddress"),
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


def _ms_to_datetime(ms) -> datetime | None:
    if not ms:
        return None
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
