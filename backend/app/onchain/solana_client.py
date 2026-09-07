"""
Cliente JSON-RPC de Solana, deliberadamente minimalista.

Decisión de diseño: en vez de depender de solana-py/solders (que han
tenido bastante rotación de versiones), hablamos JSON-RPC crudo con
httpx. Es menos "cómodo" pero mucho más estable a largo plazo: un cambio
de rate limit o de proveedor de RPC no nos obliga a perseguir breaking
changes de una librería de terceros.

El endpoint se configura vía SOLANA_RPC_URL (ver app/config.py). Por
defecto NO se usa el RPC público de mainnet-beta porque está confirmado
que no es apto para uso sostenido (~100 req/10s por IP); hace falta un
RPC dedicado gratuito (Helius, Alchemy, Syndica...) configurado por el
usuario con su propia API key gratuita (nunca una wallet).
"""
from __future__ import annotations

from app.config import settings
from app.utils.http import http_client


class SolanaRpcClient:
    def __init__(self, rpc_url: str | None = None):
        self.rpc_url = rpc_url or settings.solana_rpc_url

    async def _call(self, method: str, params: list) -> dict:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params,
        }
        # Reutilizamos el cliente resiliente, pero aquí es POST con body JSON-RPC.
        resp = await http_client._client.post(self.rpc_url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise RuntimeError(f"Solana RPC error en {method}: {data['error']}")
        return data["result"]

    async def get_account_info(self, pubkey: str, encoding: str = "base64") -> dict | None:
        result = await self._call(
            "getAccountInfo",
            [pubkey, {"encoding": encoding}],
        )
        return result.get("value")

    async def get_token_largest_accounts(self, mint: str) -> list[dict]:
        result = await self._call("getTokenLargestAccounts", [mint])
        return result.get("value", [])

    async def get_token_supply(self, mint: str) -> dict:
        result = await self._call("getTokenSupply", [mint])
        return result.get("value", {})

    async def get_program_accounts(
        self, program_id: str, filters: list[dict] | None = None, encoding: str = "base64"
    ) -> list[dict]:
        config: dict = {"encoding": encoding}
        if filters:
            config["filters"] = filters
        result = await self._call("getProgramAccounts", [program_id, config])
        return result


solana_rpc = SolanaRpcClient()
