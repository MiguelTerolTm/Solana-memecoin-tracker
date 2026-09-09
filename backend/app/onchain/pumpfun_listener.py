"""
Listener de websocket para pump.fun (casi tiempo real).

Usa `logsSubscribe`, un método ESTÁNDAR de Solana disponible en el plan
gratuito de cualquier proveedor de RPC compatible (Helius incluido — ver
docs/data-sources.md, verificado el 7/sep/2026: el free tier de Helius
da 5 conexiones websocket simultáneas con los métodos estándar). No usa
ningún método "mejorado" propio de Helius que requiera plan de pago.

Qué hace: se suscribe a los logs que mencionan el Program ID de pump.fun
y, por cada log nuevo, dispara un callback con la firma de la transacción.
Deliberadamente NO decodifica la transacción completa aquí dentro — eso
se delega al llamador (por ejemplo, un worker que llama a
`solana_rpc.get_account_info` sobre el mint concreto una vez sabe qué
buscar), para mantener este módulo simple y fácil de testear.

Uso típico:

    async def on_log(signature: str, logs: list[str]):
        print("Nueva actividad de pump.fun:", signature)

    listener = PumpFunLogListener(on_log)
    await listener.run()   # bucle infinito con reconexión automática
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Awaitable, Callable

import websockets
from websockets.exceptions import ConnectionClosed

from app.config import settings

logger = logging.getLogger("pumpfun_listener")

LogCallback = Callable[[str, list[str]], Awaitable[None]]

_MAX_BACKOFF_SECONDS = 30


class PumpFunLogListener:
    def __init__(self, on_log: LogCallback, ws_url: str | None = None):
        self._on_log = on_log
        self._ws_url = ws_url or settings.solana_ws_url
        self._program_id = settings.pumpfun_program_id or "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"

    async def run(self) -> None:
        """Bucle con reconexión automática y backoff exponencial ante cortes."""
        backoff = 1
        while True:
            try:
                await self._connect_and_listen()
                backoff = 1  # conexión terminó limpia, reset del backoff
            except (ConnectionClosed, OSError) as exc:
                logger.warning("Websocket de Solana cortado (%s). Reintentando en %ss...", exc, backoff)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, _MAX_BACKOFF_SECONDS)

    async def _connect_and_listen(self) -> None:
        if not self._ws_url:
            raise RuntimeError(
                "SOLANA_WS_URL no configurado en .env. Necesitas la URL websocket de tu "
                "proveedor de RPC (ej. wss://mainnet.helius-rpc.com/?api-key=TU_KEY)."
            )
        async with websockets.connect(self._ws_url, ping_interval=20, ping_timeout=20) as ws:
            subscribe_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "logsSubscribe",
                "params": [
                    {"mentions": [self._program_id]},
                    {"commitment": "confirmed"},
                ],
            }
            await ws.send(json.dumps(subscribe_request))
            ack = json.loads(await ws.recv())
            logger.info("Suscrito a logs de pump.fun, subscription id=%s", ack.get("result"))

            async for raw_message in ws:
                message = json.loads(raw_message)
                params = message.get("params")
                if not params:
                    continue  # puede ser la confirmación inicial de suscripción u otro mensaje de control
                result = params.get("result", {})
                value = result.get("value", {})
                signature = value.get("signature")
                logs = value.get("logs", [])
                if signature:
                    await self._on_log(signature, logs)
