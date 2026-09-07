"""
Adaptador de RugCheck (api.rugcheck.xyz).

Fuente PRIMARIA de riesgo: es la mejor fuente gratuita y sin key para
autoridades de mint/freeze, concentración de holders y estado de LP.

PENDIENTE DE CONFIRMAR (ver docs/data-sources.md, sección "pendiente de
investigar"): el rate limit oficial documentado por RugCheck directamente,
no de terceros. Hasta confirmarlo, este adaptador trata cualquier 429
como señal para hacer fallback al lector on-chain (app/onchain), que
siempre puede calcular al menos las autoridades de mint/freeze aunque no
tenga el resto de heurísticas de RugCheck.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.aggregation.schemas import RiskReport
from app.sources.base import RiskDataSource
from app.utils.http import http_client, cache

BASE_URL = "https://api.rugcheck.xyz/v1"
CACHE_TTL_SECONDS = 300  # el riesgo estructural cambia lento; cache más larga que precio


class RugCheckSource(RiskDataSource):
    name = "rugcheck"

    async def get_risk_report(self, mint: str) -> RiskReport:
        cache_key = f"rugcheck:report:{mint}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        data = await http_client.get_json(
            self.name,
            f"{BASE_URL}/tokens/{mint}/report",
        )

        top_holders = data.get("topHolders") or []
        top1_pct = top_holders[0].get("pct") if top_holders else None
        top10_pct = sum(h.get("pct", 0) for h in top_holders[:10]) if top_holders else None

        markets = data.get("markets") or []
        lp_locked_pct = None
        if markets:
            lp_pcts = [m.get("lp", {}).get("lpLockedPct") for m in markets if m.get("lp")]
            lp_pcts = [p for p in lp_pcts if p is not None]
            if lp_pcts:
                lp_locked_pct = sum(lp_pcts) / len(lp_pcts)

        report = RiskReport(
            mint=mint,
            risk_score=data.get("score"),
            is_rugged=data.get("rugged"),
            mint_authority_active=bool(data.get("mintAuthority")),
            freeze_authority_active=bool(data.get("freezeAuthority")),
            top_holder_pct=top1_pct,
            top10_holder_pct=top10_pct,
            holder_count=data.get("totalHolders"),
            lp_locked_pct=lp_locked_pct,
            flags=[r.get("name") for r in (data.get("risks") or []) if r.get("name")],
            source=self.name,
            fetched_at=datetime.now(timezone.utc),
        )
        cache.set(cache_key, report, CACHE_TTL_SECONDS)
        return report
