"""
Orquestador de fallback.

Por cada "necesidad de dato" (precio/liquidez, riesgo...) hay una cadena de
fuentes ordenada por prioridad. Se intenta la primera; si falla (excepción
de app.utils.http o ValueError de "no tengo datos para este mint"), se
prueba la siguiente. Solo si TODAS fallan se propaga el error hacia arriba.

Esto es exactamente el requisito de diseño: "usar múltiples fuentes y
hacer fallback cuando una fuente falle" (punto 8 del encargo original).
"""
from __future__ import annotations

import logging

from app.aggregation.schemas import MarketSnapshot, RiskReport, OnchainTokenFacts
from app.onchain.spl_token import get_onchain_token_facts
from app.sources.dexscreener import DexScreenerSource
from app.sources.geckoterminal import GeckoTerminalSource
from app.sources.jupiter import JupiterSource
from app.sources.rugcheck import RugCheckSource

logger = logging.getLogger("orchestrator")

# Orden de prioridad explícito y fácil de reordenar/ampliar.
_MARKET_SOURCES = [DexScreenerSource(), GeckoTerminalSource(), JupiterSource()]
_RISK_SOURCES = [RugCheckSource()]


async def get_market_snapshot(mint: str) -> MarketSnapshot | None:
    errors: list[str] = []
    for source in _MARKET_SOURCES:
        try:
            return await source.get_market_snapshot(mint)
        except Exception as exc:  # noqa: BLE001 - queremos capturar cualquier fallo de fuente
            errors.append(f"{source.name}: {exc}")
            logger.warning("Fuente de mercado '%s' falló para %s: %s", source.name, mint, exc)
    logger.error("Todas las fuentes de mercado fallaron para %s: %s", mint, errors)
    return None


async def get_risk_report(mint: str) -> RiskReport | None:
    errors: list[str] = []
    for source in _RISK_SOURCES:
        try:
            return await source.get_risk_report(mint)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{source.name}: {exc}")
            logger.warning("Fuente de riesgo '%s' falló para %s: %s", source.name, mint, exc)
    logger.error("Todas las fuentes de riesgo fallaron para %s: %s", mint, errors)
    return None


async def get_onchain_facts(mint: str) -> OnchainTokenFacts | None:
    """
    Última línea de defensa: si RugCheck también falla, al menos podemos
    calcular mint/freeze authority y holders directamente del RPC.
    """
    try:
        return await get_onchain_token_facts(mint)
    except Exception as exc:  # noqa: BLE001
        logger.error("Lectura on-chain falló para %s: %s", mint, exc)
        return None
