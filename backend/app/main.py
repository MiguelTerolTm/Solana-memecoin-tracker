from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_tokens import router as tokens_router
from app.config import settings
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


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
