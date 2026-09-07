"""
Decoder de la cuenta "bonding curve" del programa de pump.fun.

✅ VERIFICADO el 7 de septiembre de 2026 contra fuentes oficiales/independientes
coincidentes: el repositorio público de documentación de pump.fun
(github.com/pump-fun/pump-public-docs), los bindings generados con Anchor/Codama
publicados en docs.rs, y el Program ID confirmado igual en Bitquery, Solana
Tracker y varios SDKs de terceros.

Program ID oficial (mainnet y devnet): 6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P

Layout real de la cuenta BondingCurve (81 bytes total):

   Offset  Tamaño  Campo
   0       8       discriminador Anchor
   8       8       virtual_token_reserves (u64)
   16      8       virtual_sol_reserves (u64)
   24      8       real_token_reserves (u64)
   32      8       real_sol_reserves (u64)
   40      8       token_total_supply (u64)
   48      1       complete (bool)
   49      32      creator (Pubkey) — wallet que creó el token, útil para
                    heurísticas de riesgo (ej. cruzar contra otros tokens
                    creados por el mismo wallet)

Nota sobre la actualización "breaking" de pump.fun del 28/abr/2026: esa
migración añadió una cuenta nueva de fee recipient a las INSTRUCCIONES de
compra/venta (buy/sell), no cambió el layout de datos de esta cuenta. Como
este proyecto solo LEE datos y nunca construye instrucciones de trading,
esa migración no nos afecta.

Aun así, pump.fun no tiene compromiso contractual de estabilidad de este
layout: si en el futuro `_decode_bonding_curve` empieza a fallar o a dar
números sin sentido, es la primera señal de que el programa cambió de
nuevo y hay que re-verificar contra las fuentes citadas arriba.
"""
from __future__ import annotations

import base64
import base58
from dataclasses import dataclass

from app.config import settings
from app.onchain.solana_client import solana_rpc

_BONDING_CURVE_LEN = 81  # 8 + 5*8 + 1 + 32, verificado contra el struct oficial


@dataclass
class BondingCurveState:
    virtual_token_reserves: int
    virtual_sol_reserves: int
    real_token_reserves: int
    real_sol_reserves: int
    token_total_supply: int
    complete: bool
    creator: str | None

    @property
    def progress_pct(self) -> float | None:
        """Progreso aproximado de la curva hacia la migración a AMM (0-100)."""
        if not self.token_total_supply:
            return None
        sold = self.token_total_supply - self.real_token_reserves
        return max(0.0, min(100.0, sold / self.token_total_supply * 100))


def _decode_bonding_curve(raw_base64: str) -> BondingCurveState:
    raw = base64.b64decode(raw_base64)
    if len(raw) < _BONDING_CURVE_LEN:
        raise ValueError(
            f"cuenta bonding curve de {len(raw)} bytes, se esperaban {_BONDING_CURVE_LEN}. "
            "El layout verificado en este módulo pudo cambiar: revisa "
            "github.com/pump-fun/pump-public-docs antes de confiar en este resultado."
        )
    off = 8  # saltar discriminador Anchor
    virtual_token_reserves = int.from_bytes(raw[off : off + 8], "little")
    virtual_sol_reserves = int.from_bytes(raw[off + 8 : off + 16], "little")
    real_token_reserves = int.from_bytes(raw[off + 16 : off + 24], "little")
    real_sol_reserves = int.from_bytes(raw[off + 24 : off + 32], "little")
    token_total_supply = int.from_bytes(raw[off + 32 : off + 40], "little")
    complete = bool(raw[off + 40])
    creator_bytes = raw[off + 41 : off + 73]
    creator = base58.b58encode(creator_bytes).decode() if len(creator_bytes) == 32 else None

    return BondingCurveState(
        virtual_token_reserves=virtual_token_reserves,
        virtual_sol_reserves=virtual_sol_reserves,
        real_token_reserves=real_token_reserves,
        real_sol_reserves=real_sol_reserves,
        token_total_supply=token_total_supply,
        complete=complete,
        creator=creator,
    )


async def get_bonding_curve_state(bonding_curve_address: str) -> BondingCurveState:
    if not settings.pumpfun_program_id_confirmed:
        raise NotImplementedError(
            "PUMPFUN_PROGRAM_ID_CONFIRMED=false en .env. El layout ya está verificado "
            "en este módulo (ver docstring), pero se mantiene este interruptor explícito "
            "a propósito: confírmalo tú mismo re-leyendo la fuente oficial antes de activarlo, "
            "no te fíes solo de este comentario con el paso del tiempo."
        )
    account = await solana_rpc.get_account_info(bonding_curve_address, encoding="base64")
    if not account:
        raise ValueError(f"no existe cuenta bonding curve en {bonding_curve_address}")
    raw_base64 = account["data"][0] if isinstance(account["data"], list) else account["data"]
    return _decode_bonding_curve(raw_base64)
