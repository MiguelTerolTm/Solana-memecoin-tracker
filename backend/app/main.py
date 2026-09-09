from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_tokens import router as tokens_router
from app.config import settings
from app.db.session import init_db
from app.onchain.pumpfun_listener import PumpFunLogListener
from app.workers.launch_ingestor import handle_pumpfun_log

logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()

    listener_task: asyncio.Task | None = None
    if settings.solana_ws_url:
        listener = PumpFunLogListener(handle_pumpfun_log)
        listener_task = asyncio.create_task(listener.run())
        logger.info("Listener de pump.fun arrancado en segundo plano (SOLANA_WS_URL configurado)")
    else:
        logger.info(
            "SOLANA_WS_URL no configurado: no se detectan lanzamientos nuevos en tiempo real. "
            "El resto del sistema funciona igual por polling."
        )

    yield

    if listener_task:
        listener_task.cancel()


app = FastAPI(
    title="Solana Memecoin Intelligence Tracker",
    description=(
        "Herramienta de inteligencia y análisis de solo lectura para memecoins de Solana. "
        "No ejecuta trading, no gestiona wallets, no requiere claves privadas ni seed phrases."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tokens_router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}
