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
| pump.fun (lectura on-chain) | Riesgo/estado de bonding curve (lectura directa) | Sí (RPC) | No | ✅ **Verificado 7/sep/2026**: Program ID `6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P` y layout de la cuenta `BondingCurve` (81 bytes, incluye campo `creator`) confirmados contra el repo oficial `pump-fun/pump-public-docs` y bindings Anchor/Codama publicados en docs.rs, coincidentes con Bitquery, Solana Tracker y varios SDKs de terceros | — | Activado por defecto en `.env.example` (`PUMPFUN_PROGRAM_ID_CONFIRMED=true`). La migración "breaking" de fees de abril 2026 solo afecta a instrucciones de compra/venta, no a esta lectura de solo datos. |
| Solana RPC público | Fallback de último recurso | Sí | No | Confirmado no apto para uso sostenido | ~100 req/10s por IP | Usar RPC dedicado gratuito en su lugar. |
| Helius (free tier) | RPC recomendado | Requiere cuenta gratuita | Sí (gratis) | Documentado activo | ~1M créditos/mes, 10 RPS | No requiere wallet, solo email. |
| Birdeye | Enriquecimiento opcional | Requiere cuenta gratuita | Sí (gratis) | Documentado activo | Free tier pequeño (~30k CU/mes) | No es fuente primaria por lo limitado. |
| Solscan API no oficial | — (descartada) | — | — | ❌ Repo archivado en agosto 2026 (protección Cloudflare) | — | No usar. |
| X/Twitter API | — (fuera del MVP) | ❌ No | — | Confirmado: free tier cerrado a proyectos nuevos desde 6/feb/2026 | — | Sin alternativa gratuita fiable; queda fuera del alcance salvo que se pague. |

## Pendiente de confirmar antes de producción

- Rate limit oficial de RugCheck: **sigue sin encontrarse documentación
  oficial publicada** con cifras concretas (búsqueda dedicada el
  7/sep/2026 solo devolvió páginas de marketing y scrapers de terceros,
  no una doc técnica con números). RugCheck sí ofrece una API key
  gratuita opcional desde su dashboard — si el uso crece, vale la pena
  registrarse para tener un tier documentado en vez de depender del
  endpoint público sin key. Mientras tanto, `ResilientClient` ya está
  diseñado para no asumir un número y reaccionar a 429 reales.
- ~~Si el free tier de Helius permite websockets~~ ✅ **Resuelto (7/sep/2026)**:
  el plan Free de Helius permite **5 conexiones websocket simultáneas** y
  da acceso a los métodos **estándar** de Solana (`logsSubscribe`,
  `programSubscribe`, `accountSubscribe`, `signatureSubscribe`) sin coste.
  Los métodos *mejorados* propios de Helius (`transactionSubscribe`,
  filtros avanzados de `accountSubscribe`) sí requieren plan de pago, pero
  no son necesarios para este proyecto. Con esto, sí es viable "casi
  tiempo real" gratis: `logsSubscribe` sobre el Program ID de pump.fun
  para detectar lanzamientos nuevos, y `accountSubscribe` sobre las
  bonding curves de los tokens en watchlist para actualizaciones en vivo.
- ~~Program ID e IDL actuales de pump.fun~~ ✅ **Resuelto** (ver tabla de
  arriba y `backend/app/onchain/pumpfun_decoder.py`).
- Límite exacto de GeckoTerminal keyless contra su documentación oficial
  (sigue sin confirmarse con precisión).
- Programas de locker de LP más usados en Solana, para verificar
  "LP lock" de forma más robusta que el dato agregado de RugCheck.
