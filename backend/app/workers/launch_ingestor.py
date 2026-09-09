"""
Worker: listener de pump.fun → base de datos.

No nos fiamos del log en crudo para decidir "esto es un token nuevo" —
eso solo nos dice "algo pasó mencionando el programa de pump.fun" (podría
ser una compra, una venta, una migración...). Para confirmarlo de verdad:

1. Filtramos por logs que contengan "Instruction: Create" (el nombre de
   la instrucción Anchor de creación de token en pump.fun).
2. Pedimos la transacción completa (`getTransaction`) y miramos
   `meta.postTokenBalances`: un mint que aparece ahí pero no tenía saldo
   antes (`preTokenBalances`) es, con altísima probabilidad, un mint
   recién creado en esa misma transacción.
3. El creador se toma como el primer firmante de la transacción
   (`accountKeys[0]` cuando `signer: true`), que es como pump.fun
   estructura la instrucción de creación.

Si algo falla a mitad de camino (transacción no encontrada todavía por
el RPC, no se puede determinar el mint...), se descarta ese evento y se
sigue escuchando — no se detiene el worker por un evento suelto.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError

from app.db.models import TokenLaunch
from app.db.session import async_session_factory
from app.onchain.solana_client import solana_rpc

logger = logging.getLogger("launch_ingestor")

_CREATE_LOG_MARKER = "Instruction: Create"


async def handle_pumpfun_log(signature: str, logs: list[str]) -> None:
    if not any(_CREATE_LOG_MARKER in line for line in logs):
        return  # no es una creación de token, ignorar (compra/venta/otra instrucción)

    try:
        tx = await solana_rpc.get_transaction(signature)
    except Exception as exc:  # noqa: BLE001
        logger.warning("No se pudo obtener la transacción %s: %s", signature, exc)
        return

    if not tx:
        logger.info("Transacción %s todavía no disponible en el RPC, se ignora este evento", signature)
        return

    mint = _extract_new_mint(tx)
    if not mint:
        logger.info("No se pudo determinar el mint nuevo en la transacción %s", signature)
        return

    creator = _extract_creator(tx)

    async with async_session_factory() as session:
        launch = TokenLaunch(
            mint=mint,
            creator=creator,
            signature=signature,
            detected_at=datetime.now(timezone.utc),
        )
        session.add(launch)
        try:
            await session.commit()
            logger.info("Nuevo lanzamiento guardado: mint=%s creador=%s", mint, creator)
        except IntegrityError:
            # Ya lo teníamos guardado (mint es UNIQUE) — no es un error real, solo un duplicado.
            await session.rollback()


def _extract_new_mint(tx: dict) -> str | None:
    meta = tx.get("meta") or {}
    pre_balances = meta.get("preTokenBalances") or []
    post_balances = meta.get("postTokenBalances") or []

    pre_mints = {b.get("mint") for b in pre_balances}
    post_mints = {b.get("mint") for b in post_balances}

    new_mints = post_mints - pre_mints
    new_mints.discard(None)
    if not new_mints:
        return None
    # En la práctica una creación de pump.fun solo introduce un mint nuevo.
    return next(iter(new_mints))


def _extract_creator(tx: dict) -> str | None:
    try:
        account_keys = tx["transaction"]["message"]["accountKeys"]
    except (KeyError, TypeError):
        return None
    for entry in account_keys:
        if isinstance(entry, dict) and entry.get("signer"):
            return entry.get("pubkey")
    return None
