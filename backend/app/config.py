"""
Configuración de la aplicación.

Nota de seguridad importante: ninguna variable de este archivo debe ser
jamás una seed phrase, clave privada de wallet o credencial de custodia.
Todo lo que aquí se configura son claves de LECTURA de APIs públicas
(gratis, obtenidas con un simple registro por email) o URLs de RPC.
Este proyecto no firma transacciones ni gestiona fondos.
"""
from __future__ import annotations

import os


class Settings:
    # RPC de Solana. Por defecto, el público (NO apto para uso sostenido,
    # ver docs/data-sources.md). En producción, configurar aquí la URL de
    # un RPC dedicado gratuito (Helius, Alchemy, Syndica...) con su key
    # de lectura.
    solana_rpc_url: str = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")

    # Claves opcionales de fuentes que sí las requieren (todas de solo lectura).
    birdeye_api_key: str | None = os.getenv("BIRDEYE_API_KEY")

    # Ver docs/data-sources.md: el layout de la bonding curve de pump.fun
    # NO está verificado contra el programa en vivo. Se mantiene apagado
    # (False) hasta confirmarlo explícitamente.
    pumpfun_program_id_confirmed: bool = os.getenv("PUMPFUN_PROGRAM_ID_CONFIRMED", "false").lower() == "true"
    pumpfun_program_id: str | None = os.getenv("PUMPFUN_PROGRAM_ID")

    database_url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./tracker.db")

    cors_allow_origins: list[str] = os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:3000").split(",")


settings = Settings()
