# Arquitectura

## Capas

1. **Fuentes externas** (`backend/app/sources/`): un adaptador por API
   externa (DexScreener, GeckoTerminal, Jupiter, RugCheck). Cada uno
   traduce su JSON propio a los esquemas normalizados de
   `backend/app/aggregation/schemas.py`.
2. **Lectura on-chain directa** (`backend/app/onchain/`): no depende de
   ningún tercero. Decodifica cuentas SPL Token directamente desde bytes
   RPC (`spl_token.py`) y, de forma experimental y sin verificar aún
   (`pumpfun_decoder.py`), la bonding curve de pump.fun.
3. **Orquestador de fallback** (`backend/app/aggregation/orchestrator.py`):
   prueba las fuentes de cada capacidad en orden de prioridad; si una
   falla, pasa a la siguiente automáticamente.
4. **Persistencia** (`backend/app/db/`): SQLite vía SQLAlchemy async.
   Guarda un snapshot cada vez que se consulta un token — es la única
   fuente de histórico real del sistema.
5. **Scoring** (`backend/app/scoring/rules.py`): reglas explícitas y
   pesos ajustables, nunca una caja negra. Nunca es una recomendación de
   compra/venta.
6. **API** (`backend/app/api/`): FastAPI, 100% lectura. No hay ningún
   endpoint que firme o envíe transacciones.
7. **Frontend** (`frontend/`): Next.js/React. Sin ninguna librería de
   wallets, sin conexión a wallets.

## Por qué fallback y no una sola fuente "buena"

Ninguna fuente gratuita de datos cripto tiene garantía contractual de
seguir siendo gratis o de seguir funcionando (ver `data-sources.md`).
Diseñar alrededor de una sola fuente "principal" hace que todo el sistema
se caiga cuando esa fuente cambia sus condiciones sin aviso — algo que ya
ha pasado varias veces en este ecosistema en 2026 (Solscan, pump.fun,
Twitter/X). El orquestador de fallback es la respuesta directa a ese
riesgo.

## Qué NO hace este sistema (por diseño)

- No ejecuta trading automático.
- No gestiona wallets, no pide ni almacena seed phrases ni claves
  privadas.
- No emite recomendaciones de compra/venta — solo un score de
  "merece investigarse" con su razonamiento explícito.
