# Fuentes de datos

Estado investigado y, cuando fue posible, verificado en vivo el 6 de
septiembre de 2026. Los límites gratuitos de estas APIs cambian sin
aviso — **no confiar en esta tabla como verdad permanente**, sino como
punto de partida a revalidar periódicamente (el propio `ResilientClient`
de `backend/app/utils/http.py` está diseñado para no asumir un número
fijo y reaccionar a los códigos HTTP reales).

| Fuente | Uso en el proyecto | Gratis | Key | Estado verificado | Límite aprox. | Notas |
|---|---|---|---|---|---|---|
| DexScreener | Mercado (1ª prioridad) | Sí | No | ✅ Probado en vivo (`api.dexscreener.com/latest/dex/search`) | ~300 req/min | Sin histórico OHLCV. ToS prohíbe construir un competidor directo. |
| GeckoTerminal (CoinGecko onchain keyless) | Mercado (2ª prioridad) | Sí | No | Documentado como activo | ~10-30 req/min (cifra no confirmada de forma oficial, ver pendientes) | Sí da OHLC. |
| Jupiter Price API (`lite-api.jup.ag`) | Mercado (3ª prioridad) | Sí | No | Documentado como activo tras migración de plataforma (corte 30/jun/2026) | No confirmado tras la migración | Solo precio, sin liquidez/volumen. |
| RugCheck (`api.rugcheck.xyz`) | Riesgo (1ª prioridad) | Sí | No | Reportado "healthy" en directorios recientes | No confirmado con la doc oficial | Mejor fuente gratis de mint/freeze authority, holders, LP lock. |
| pump.fun (API no oficial) | — (descartada como dependencia principal) | — | — | ❌ Tuvo caída de DNS en junio 2026 | — | No tiene API oficial. Se usa lectura on-chain directa en su lugar. |
| Solana RPC público | Fallback de último recurso | Sí | No | Confirmado no apto para uso sostenido | ~100 req/10s por IP | Usar RPC dedicado gratuito en su lugar. |
| Helius (free tier) | RPC recomendado | Requiere cuenta gratuita | Sí (gratis) | Documentado activo | ~1M créditos/mes, 10 RPS | No requiere wallet, solo email. |
| Birdeye | Enriquecimiento opcional | Requiere cuenta gratuita | Sí (gratis) | Documentado activo | Free tier pequeño (~30k CU/mes) | No es fuente primaria por lo limitado. |
| Solscan API no oficial | — (descartada) | — | — | ❌ Repo archivado en agosto 2026 (protección Cloudflare) | — | No usar. |
| X/Twitter API | — (fuera del MVP) | ❌ No | — | Confirmado: free tier cerrado a proyectos nuevos desde 6/feb/2026 | — | Sin alternativa gratuita fiable; queda fuera del alcance salvo que se pague. |

## Pendiente de confirmar antes de producción

- Rate limit oficial documentado directamente por RugCheck (no de
  terceros).
- Si el free tier de Helius (u otro RPC gratuito) permite websockets
  (`accountSubscribe`/`logsSubscribe`) para acercarse a tiempo real.
- Program ID e IDL actuales de pump.fun, para verificar
  `backend/app/onchain/pumpfun_decoder.py` contra el programa real antes
  de activarlo (`PUMPFUN_PROGRAM_ID_CONFIRMED=true`).
- Límite exacto de GeckoTerminal keyless contra su documentación oficial.
- Programas de locker de LP más usados en Solana, para verificar
  "LP lock" de forma más robusta que el dato agregado de RugCheck.
