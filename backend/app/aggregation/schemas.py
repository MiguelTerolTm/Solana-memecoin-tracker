"""
Esquemas normalizados.

Cada fuente externa devuelve JSON con forma distinta (DexScreener no es
GeckoTerminal, ni es RugCheck). Para poder hacer fallback entre fuentes sin
que el resto del sistema tenga que saber de quién vino el dato, TODOS los
adaptadores traducen su respuesta cruda a estos modelos antes de
devolverla al orquestador.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MarketSnapshot(BaseModel):
    """Precio/liquidez/volumen de un token en un momento dado."""

    mint: str
    symbol: Optional[str] = None
    price_usd: Optional[float] = None
    liquidity_usd: Optional[float] = None
    fdv_usd: Optional[float] = None
    market_cap_usd: Optional[float] = None
    volume_24h_usd: Optional[float] = None
    price_change_24h_pct: Optional[float] = None
    pair_created_at: Optional[datetime] = None
    dex: Optional[str] = None
    pair_address: Optional[str] = None

    # Trazabilidad: de qué fuente vino este snapshot concreto.
    source: str = Field(description="Nombre del adaptador que produjo este dato")
    fetched_at: datetime


class RiskReport(BaseModel):
    """Señales de riesgo de un token (mint/freeze authority, holders, LP...)."""

    mint: str
    risk_score: Optional[float] = Field(
        default=None, description="0-10 según convención de RugCheck; ver docs/risk-methodology.md"
    )
    is_rugged: Optional[bool] = None
    mint_authority_active: Optional[bool] = None
    freeze_authority_active: Optional[bool] = None
    top_holder_pct: Optional[float] = None
    top10_holder_pct: Optional[float] = None
    holder_count: Optional[int] = None
    lp_locked_pct: Optional[float] = None
    flags: list[str] = Field(default_factory=list)

    source: str
    fetched_at: datetime


class OnchainTokenFacts(BaseModel):
    """
    Hechos calculados directamente desde el RPC de Solana, sin ninguna API
    de terceros de por medio. Es la fuente más lenta pero la más fiable
    porque no depende de que un proveedor externo mantenga su servicio.
    """

    mint: str
    decimals: Optional[int] = None
    supply: Optional[int] = None
    mint_authority: Optional[str] = None
    freeze_authority: Optional[str] = None
    top_holders: list[dict] = Field(default_factory=list)  # [{address, amount, pct}]
    fetched_at: datetime


class AggregatedToken(BaseModel):
    """Vista combinada que expone la API: lo mejor que se pudo reunir de todas las fuentes."""

    mint: str
    market: Optional[MarketSnapshot] = None
    risk: Optional[RiskReport] = None
    onchain: Optional[OnchainTokenFacts] = None
    score: Optional["TokenScore"] = None


class TokenScore(BaseModel):
    """Salida del motor de scoring: nunca una recomendación de compra."""

    value: float = Field(description="0-100, mayor = más señales positivas para investigar")
    label: str = Field(description="ej. 'requiere más investigación', 'señales mixtas'...")
    reasons: list[str] = Field(default_factory=list, description="Explicación legible de cada factor")
    missing_data: list[str] = Field(
        default_factory=list, description="Qué no se pudo verificar (transparencia sobre huecos)"
    )


AggregatedToken.model_rebuild()
