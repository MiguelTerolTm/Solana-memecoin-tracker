"""
Interfaz común de un adaptador de fuente de datos.

Cada adaptador (dexscreener.py, geckoterminal.py, jupiter.py, rugcheck.py...)
implementa un subconjunto de estos métodos según lo que esa fuente ofrezca.
El orquestador (aggregation/orchestrator.py) los prueba en orden de
prioridad y solo necesita saber que todos hablan el mismo idioma de salida
(los modelos en aggregation/schemas.py).

Si una fuente no soporta una capacidad, simplemente no implementa ese
método (o lanza NotImplementedError) y el orquestador pasa a la siguiente.
"""
from __future__ import annotations

from abc import ABC

from app.aggregation.schemas import MarketSnapshot, RiskReport


class MarketDataSource(ABC):
    name: str

    async def get_market_snapshot(self, mint: str) -> MarketSnapshot:
        raise NotImplementedError


class RiskDataSource(ABC):
    name: str

    async def get_risk_report(self, mint: str) -> RiskReport:
        raise NotImplementedError
