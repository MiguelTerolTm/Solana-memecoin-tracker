"""
Rutas de la API.

Todo es de SOLO LECTURA e informativo. No hay ningún endpoint que firme,
envíe o ejecute una transacción — este servicio no sabe hablar con
wallets, deliberadamente (ver encargo original, puntos 9 y 10).
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.aggregation.orchestrator import get_market_snapshot, get_risk_report, get_onchain_facts
from app.aggregation.schemas import AggregatedToken
from app.db.models import TokenSnapshot, WatchlistEntry, TokenLaunch
from app.db.session import get_session
from app.scoring.rules import score_token

router = APIRouter()


@router.get("/tokens/{mint}", response_model=AggregatedToken)
async def get_token(mint: str, session: AsyncSession = Depends(get_session)) -> AggregatedToken:
    """
    Punto de entrada principal: agrega mercado + riesgo + on-chain con
    fallback automático en cada capa, calcula el score, y guarda un
    snapshot para tener histórico propio.
    """
    market = await get_market_snapshot(mint)
    risk = await get_risk_report(mint)
    onchain = await get_onchain_facts(mint)

    if market is None and risk is None and onchain is None:
        raise HTTPException(
            status_code=502,
            detail="Todas las fuentes de datos fallaron para este mint. Puede que el mint no exista, "
            "o que todas las fuentes configuradas estén caídas o rate-limited en este momento.",
        )

    score = score_token(market, risk, onchain)

    snapshot = TokenSnapshot(
        mint=mint,
        fetched_at=datetime.now(timezone.utc),
        price_usd=market.price_usd if market else None,
        liquidity_usd=market.liquidity_usd if market else None,
        volume_24h_usd=market.volume_24h_usd if market else None,
        market_source=market.source if market else None,
        risk_score=risk.risk_score if risk else None,
        top10_holder_pct=risk.top10_holder_pct if risk else None,
        lp_locked_pct=risk.lp_locked_pct if risk else None,
        tracker_score=score.value,
        tracker_score_label=score.label,
        raw={
            "market": market.model_dump(mode="json") if market else None,
            "risk": risk.model_dump(mode="json") if risk else None,
            "onchain": onchain.model_dump(mode="json") if onchain else None,
        },
    )
    session.add(snapshot)
    await session.commit()

    return AggregatedToken(mint=mint, market=market, risk=risk, onchain=onchain, score=score)


@router.get("/tokens/{mint}/history")
async def get_token_history(mint: str, session: AsyncSession = Depends(get_session)):
    """Histórico propio (nuestra única fuente de continuidad temporal, ver docs/data-sources.md)."""
    result = await session.execute(
        select(TokenSnapshot).where(TokenSnapshot.mint == mint).order_by(TokenSnapshot.fetched_at)
    )
    rows = result.scalars().all()
    return [
        {
            "fetched_at": r.fetched_at,
            "price_usd": r.price_usd,
            "liquidity_usd": r.liquidity_usd,
            "tracker_score": r.tracker_score,
        }
        for r in rows
    ]


@router.post("/watchlist/{mint}")
async def add_to_watchlist(mint: str, note: str | None = None, session: AsyncSession = Depends(get_session)):
    existing = await session.get(WatchlistEntry, mint)
    if existing:
        return {"status": "ya estaba en watchlist"}
    entry = WatchlistEntry(mint=mint, added_at=datetime.now(timezone.utc), note=note)
    session.add(entry)
    await session.commit()
    return {"status": "añadido"}


@router.get("/watchlist")
async def list_watchlist(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(WatchlistEntry))
    return [
        {"mint": e.mint, "symbol": e.symbol, "added_at": e.added_at, "note": e.note}
        for e in result.scalars().all()
    ]


@router.get("/launches")
async def list_recent_launches(limit: int = 50, session: AsyncSession = Depends(get_session)):
    """
    Lanzamientos nuevos de pump.fun detectados por el listener de websocket
    (ver app/workers/launch_ingestor.py). Vacío si SOLANA_WS_URL no está
    configurado, o si todavía no ha pasado ningún lanzamiento nuevo desde
    que arrancó el servidor.
    """
    result = await session.execute(
        select(TokenLaunch).order_by(TokenLaunch.detected_at.desc()).limit(limit)
    )
    return [
        {"mint": r.mint, "creator": r.creator, "detected_at": r.detected_at, "signature": r.signature}
        for r in result.scalars().all()
    ]
