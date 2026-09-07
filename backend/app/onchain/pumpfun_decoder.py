"""
Decoder de la cuenta "bonding curve" del programa de pump.fun.

⚠️ ESTADO: BORRADOR SIN VERIFICAR CONTRA EL PROGRAMA EN VIVO. ⚠️

Esto es intencional y está documentado en docs/data-sources.md como
pendiente de investigación antes de confiar en él en producción:

1. pump.fun NO tiene una API oficial. Su API "frontend" no oficial ya tuvo
   una caída de DNS en junio de 2026, así que apostamos por leer el
   programa on-chain directamente en vez de depender de esa API.
2. El layout de abajo es el que ha sido documentado públicamente y de
   forma consistente por múltiples proyectos open-source como la
   estructura de la cuenta "BondingCurve" (tras el discriminador Anchor
   de 8 bytes):

   Offset  Tamaño  Campo
   0       8       discriminador Anchor (hash del nombre de la cuenta)
   8       8       virtual_token_reserves (u64)
   16      8       virtual_sol_reserves (u64)
   24      8       real_token_reserves (u64)
   32      8       real_sol_reserves (u64)
   40      8       token_total_supply (u64)
   48      1       complete (bool)

   PERO pump.fun ha tenido varias migraciones/versiones de su curva
   (incluyendo una migración a AMM propio tras completar la curva), así
   que ESTE LAYOUT PUEDE ESTAR DESACTUALIZADO. Antes de usar esto para
   nada importante:
     a) obtener el Program ID actual verificado (no confiar en uno de
        memoria: buscarlo en la documentación/repositorio oficial vigente
        en el momento de implementar),
     b) leer una cuenta bonding curve conocida y comparar bytes/longitud
        real contra este layout,
     c) si pump.fun publica su IDL Anchor on-chain, preferir decodificarlo
        dinámicamente con esa IDL en vez de con offsets fijos a mano.

Este módulo lanza NotImplementedError hasta que el Program ID se
confirme explícitamente en config.py, para no dar falsa confianza con un
resultado silenciosamente incorrecto.
"""
from __future__ import annotations

import base64
from dataclasses import dataclass

from app.config import settings
from app.onchain.solana_client import solana_rpc

_EXPECTED_MIN_LEN = 49  # 8 (discriminador) + 5*8 + 1


@dataclass
class BondingCurveState:
    virtual_token_reserves: int
    virtual_sol_reserves: int
    real_token_reserves: int
    real_sol_reserves: int
    token_total_supply: int
    complete: bool

    @property
    def progress_pct(self) -> float | None:
        """Progreso aproximado de la curva hacia la migración a AMM (0-100)."""
        if not self.token_total_supply:
            return None
        sold = self.token_total_supply - self.real_token_reserves
        return max(0.0, min(100.0, sold / self.token_total_supply * 100))


def _decode_bonding_curve(raw_base64: str) -> BondingCurveState:
    raw = base64.b64decode(raw_base64)
    if len(raw) < _EXPECTED_MIN_LEN:
        raise ValueError(
            f"cuenta bonding curve de {len(raw)} bytes, se esperaban >= {_EXPECTED_MIN_LEN}. "
            "El layout documentado en este módulo probablemente cambió: NO uses este resultado "
            "sin antes revisar el Program ID / IDL actuales."
        )
    off = 8  # saltar discriminador Anchor
    virtual_token_reserves = int.from_bytes(raw[off : off + 8], "little")
    virtual_sol_reserves = int.from_bytes(raw[off + 8 : off + 16], "little")
    real_token_reserves = int.from_bytes(raw[off + 16 : off + 24], "little")
    real_sol_reserves = int.from_bytes(raw[off + 24 : off + 32], "little")
    token_total_supply = int.from_bytes(raw[off + 32 : off + 40], "little")
    complete = bool(raw[off + 40])

    return BondingCurveState(
        virtual_token_reserves=virtual_token_reserves,
        virtual_sol_reserves=virtual_sol_reserves,
        real_token_reserves=real_token_reserves,
        real_sol_reserves=real_sol_reserves,
        token_total_supply=token_total_supply,
        complete=complete,
    )


async def get_bonding_curve_state(bonding_curve_address: str) -> BondingCurveState:
    if not settings.pumpfun_program_id_confirmed:
        raise NotImplementedError(
            "El Program ID de pump.fun no está confirmado en esta instalación "
            "(PUMPFUN_PROGRAM_ID_CONFIRMED=false en .env). Verifica el layout real "
            "contra el programa en vivo antes de activar este módulo — ver el docstring "
            "de este archivo y docs/data-sources.md."
        )
    account = await solana_rpc.get_account_info(bonding_curve_address, encoding="base64")
    if not account:
        raise ValueError(f"no existe cuenta bonding curve en {bonding_curve_address}")
    raw_base64 = account["data"][0] if isinstance(account["data"], list) else account["data"]
    return _decode_bonding_curve(raw_base64)
