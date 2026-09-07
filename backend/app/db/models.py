"""
Modelos de base de datos.

Como casi ninguna fuente gratuita da histórico real (ver docs/data-sources.md),
esta base de datos ES la única forma de tener continuidad en el tiempo:
guardamos un snapshot cada vez que consultamos un token, y de ahí se puede
derivar momentum, "días desde el primer snapshot visto", etc.

Watchlist separada de snapshots para poder marcar qué tokens el usuario
quiere seguir sin mezclarlo con el histórico de datos.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, Float, Integer, DateTime, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TokenSnapshot(Base):
    __tablename__ = "token_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mint: Mapped[str] = mapped_column(String, index=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, index=True)

    price_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    liquidity_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume_24h_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    market_source: Mapped[str | None] = mapped_column(String, nullable=True)

    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    top10_holder_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    lp_locked_pct: Mapped[float | None] = mapped_column(Float, nullable=True)

    tracker_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    tracker_score_label: Mapped[str | None] = mapped_column(String, nullable=True)

    raw: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class WatchlistEntry(Base):
    __tablename__ = "watchlist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mint: Mapped[str] = mapped_column(String, unique=True, index=True)
    symbol: Mapped[str | None] = mapped_column(String, nullable=True)
    added_at: Mapped[datetime] = mapped_column(DateTime)
    note: Mapped[str | None] = mapped_column(String, nullable=True)
