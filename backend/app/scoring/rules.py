"""
Motor de scoring.

Objetivo explícito (ver encargo original, punto 11): ayudar a decidir si
un token MERECE SER INVESTIGADO más a fondo. Esto NO es una señal de
compra ni de trading automático, y así se etiqueta en el resultado.

Diseño deliberadamente simple y transparente: una suma de puntos con
razones legibles, no un modelo de ML de caja negra. Cada regla está
documentada en docs/risk-methodology.md para que el usuario pueda
auditar o ajustar los pesos.
"""
from __future__ import annotations

from app.aggregation.schemas import MarketSnapshot, RiskReport, OnchainTokenFacts, TokenScore

# Pesos ajustables — centralizados aquí para no esconder "números mágicos" en el código.
_WEIGHTS = {
    "liquidity_ok": 20,
    "mint_authority_revoked": 20,
    "freeze_authority_revoked": 15,
    "lp_locked": 20,
    "holder_concentration_ok": 15,
    "volume_present": 10,
}


def score_token(
    market: MarketSnapshot | None,
    risk: RiskReport | None,
    onchain: OnchainTokenFacts | None,
) -> TokenScore:
    points = 0.0
    max_points = 0.0
    reasons: list[str] = []
    missing: list[str] = []

    # --- Liquidez ---
    max_points += _WEIGHTS["liquidity_ok"]
    if market and market.liquidity_usd is not None:
        if market.liquidity_usd >= 10_000:
            points += _WEIGHTS["liquidity_ok"]
            reasons.append(f"Liquidez razonable (${market.liquidity_usd:,.0f})")
        else:
            reasons.append(f"Liquidez baja (${market.liquidity_usd:,.0f}) — riesgo de slippage alto")
    else:
        missing.append("liquidez")

    # --- Autoridad de mint (¿pueden crear más tokens de la nada?) ---
    max_points += _WEIGHTS["mint_authority_revoked"]
    mint_authority_active = _first_not_none(
        risk.mint_authority_active if risk else None,
        (onchain.mint_authority is not None) if onchain else None,
    )
    if mint_authority_active is not None:
        if not mint_authority_active:
            points += _WEIGHTS["mint_authority_revoked"]
            reasons.append("Mint authority revocada (no se puede emitir supply extra)")
        else:
            reasons.append("Mint authority ACTIVA — el creador podría emitir más tokens")
    else:
        missing.append("mint authority")

    # --- Autoridad de freeze (¿pueden congelar tu cuenta de tokens?) ---
    max_points += _WEIGHTS["freeze_authority_revoked"]
    freeze_authority_active = _first_not_none(
        risk.freeze_authority_active if risk else None,
        (onchain.freeze_authority is not None) if onchain else None,
    )
    if freeze_authority_active is not None:
        if not freeze_authority_active:
            points += _WEIGHTS["freeze_authority_revoked"]
            reasons.append("Freeze authority revocada")
        else:
            reasons.append("Freeze authority ACTIVA — el creador podría congelar transferencias")
    else:
        missing.append("freeze authority")

    # --- LP lock ---
    max_points += _WEIGHTS["lp_locked"]
    if risk and risk.lp_locked_pct is not None:
        if risk.lp_locked_pct >= 80:
            points += _WEIGHTS["lp_locked"]
            reasons.append(f"LP mayormente bloqueada ({risk.lp_locked_pct:.0f}%)")
        else:
            reasons.append(f"LP poco bloqueada ({risk.lp_locked_pct:.0f}%) — riesgo de retirada de liquidez")
    else:
        missing.append("estado de LP lock")

    # --- Concentración de holders ---
    max_points += _WEIGHTS["holder_concentration_ok"]
    top10 = risk.top10_holder_pct if risk else None
    if top10 is not None:
        if top10 <= 40:
            points += _WEIGHTS["holder_concentration_ok"]
            reasons.append(f"Top 10 holders concentran {top10:.0f}% (razonable)")
        else:
            reasons.append(f"Top 10 holders concentran {top10:.0f}% — alta concentración")
    else:
        missing.append("concentración de holders")

    # --- Volumen presente (¿hay algo de actividad real?) ---
    max_points += _WEIGHTS["volume_present"]
    if market and market.volume_24h_usd is not None:
        if market.volume_24h_usd > 1_000:
            points += _WEIGHTS["volume_present"]
            reasons.append(f"Volumen 24h presente (${market.volume_24h_usd:,.0f})")
        else:
            reasons.append("Volumen 24h muy bajo o inexistente")
    else:
        missing.append("volumen 24h")

    normalized = (points / max_points * 100) if max_points else 0.0

    if len(missing) >= 3:
        label = "datos insuficientes para evaluar"
    elif normalized >= 70:
        label = "señales mayormente positivas — aún así, investigar antes de cualquier decisión"
    elif normalized >= 40:
        label = "señales mixtas — requiere investigación adicional"
    else:
        label = "señales de alerta — alta cautela recomendada"

    return TokenScore(
        value=round(normalized, 1),
        label=label,
        reasons=reasons,
        missing_data=missing,
    )


def _first_not_none(*values):
    for v in values:
        if v is not None:
            return v
    return None
