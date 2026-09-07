# Metodología de scoring

El score (`backend/app/scoring/rules.py`) es una suma ponderada de
señales verificables, no un modelo de caja negra. Objetivo: ayudar a
decidir si un token **merece investigarse más a fondo** — nunca es una
recomendación de compra o venta.

## Factores y pesos actuales

| Factor | Peso | Fuente |
|---|---|---|
| Liquidez ≥ $10,000 | 20 | Mercado (DexScreener/GeckoTerminal/Jupiter) |
| Mint authority revocada | 20 | RugCheck, con fallback a lectura on-chain directa |
| Freeze authority revocada | 15 | RugCheck, con fallback a lectura on-chain directa |
| LP bloqueada ≥ 80% | 20 | RugCheck |
| Top 10 holders ≤ 40% del supply | 15 | RugCheck |
| Volumen 24h > $1,000 | 10 | Mercado |

Si faltan 3 o más factores (por caída de todas las fuentes relevantes),
el resultado se marca explícitamente como "datos insuficientes para
evaluar" en vez de forzar un número que dé falsa confianza.

## Por qué no incluye señal social (Twitter/X, Telegram)

El free tier de la API de X se cerró a proyectos nuevos el 6 de febrero
de 2026; no hay alternativa gratuita y fiable de lectura. Se decidió
dejarlo fuera del MVP en vez de depender de scraping no oficial (poco
fiable y contrario a los términos de servicio). Si en el futuro se paga
acceso a esa API, se añadiría como un factor más, con su propio peso y
sin sustituir a los factores estructurales on-chain.

## Ajustar los pesos

Los pesos están centralizados en el diccionario `_WEIGHTS` al principio
de `backend/app/scoring/rules.py`, precisamente para que se puedan
auditar y modificar sin tener que rastrear "números mágicos" repartidos
por el código.
