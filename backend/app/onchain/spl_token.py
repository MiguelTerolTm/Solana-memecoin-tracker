"""
Lectura directa de la cuenta "mint" del SPL Token Program.

El layout de la cuenta mint es un estándar estable de Solana (no ha
cambiado desde el lanzamiento del programa), así que decodificarlo a mano
es seguro y no depende de ninguna librería que pueda quedar desactualizada:

Offset  Tamaño  Campo
0       4       mint_authority_option (0 = None, 1 = Some)
4       32      mint_authority (pubkey)
36      8       supply (u64, little-endian)
44      1       decimals
45      1       is_initialized (bool)
46      4       freeze_authority_option (0 = None, 1 = Some)
50      32      freeze_authority (pubkey)

Referencia: layout público del SPL Token Program (Token-2022 añade
extensiones DETRÁS de estos primeros 82 bytes, así que este parseo sigue
siendo válido incluso para tokens Token-2022 en sus campos base).
"""
from __future__ import annotations

import base64
import base58
from datetime import datetime, timezone

from app.aggregation.schemas import OnchainTokenFacts
from app.onchain.solana_client import solana_rpc

_MINT_LAYOUT_MIN_LEN = 82


def _decode_mint_account(raw_base64: str) -> dict:
    raw = base64.b64decode(raw_base64)
    if len(raw) < _MINT_LAYOUT_MIN_LEN:
        raise ValueError(
            f"cuenta mint más corta de lo esperado ({len(raw)} bytes, se esperaban >= {_MINT_LAYOUT_MIN_LEN}); "
            "el layout del programa pudo cambiar, revisar antes de confiar en este resultado"
        )

    mint_authority_option = int.from_bytes(raw[0:4], "little")
    mint_authority = base58.b58encode(raw[4:36]).decode() if mint_authority_option else None

    supply = int.from_bytes(raw[36:44], "little")
    decimals = raw[44]

    freeze_authority_option = int.from_bytes(raw[46:50], "little")
    freeze_authority = base58.b58encode(raw[50:82]).decode() if freeze_authority_option else None

    return {
        "mint_authority": mint_authority,
        "freeze_authority": freeze_authority,
        "supply": supply,
        "decimals": decimals,
    }


async def get_onchain_token_facts(mint: str) -> OnchainTokenFacts:
    """
    Combina getAccountInfo (autoridades/supply/decimales) con
    getTokenLargestAccounts (top holders) para dar una foto de riesgo
    calculada 100% desde la blockchain, sin depender de ningún proveedor
    externo de datos.
    """
    account = await solana_rpc.get_account_info(mint, encoding="base64")
    if not account:
        raise ValueError(f"no existe cuenta mint para {mint} en este RPC")

    raw_base64 = account["data"][0] if isinstance(account["data"], list) else account["data"]
    decoded = _decode_mint_account(raw_base64)

    largest = await solana_rpc.get_token_largest_accounts(mint)
    total_supply = decoded["supply"] or 1  # evitar división por cero
    top_holders = [
        {
            "address": entry.get("address"),
            "amount": entry.get("amount"),
            "pct": (int(entry.get("amount", 0)) / total_supply * 100) if total_supply else None,
        }
        for entry in largest
    ]

    return OnchainTokenFacts(
        mint=mint,
        decimals=decoded["decimals"],
        supply=decoded["supply"],
        mint_authority=decoded["mint_authority"],
        freeze_authority=decoded["freeze_authority"],
        top_holders=top_holders,
        fetched_at=datetime.now(timezone.utc),
    )
