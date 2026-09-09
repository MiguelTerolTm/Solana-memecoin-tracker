# Roadmap / Visión a largo plazo

Este documento es la visión completa del proyecto, tal como la definió el
usuario. Se mantiene íntegro como referencia de hacia dónde vamos, pero
**no todo aquí es gratis de verdad** — ver la nota de realismo al principio
antes de asumir que una fase concreta se puede construir sin coste.

## Nota de realismo (importante, leer antes de priorizar una fase)

Gran parte de este documento SÍ es alcanzable con fuentes 100% gratuitas
(ver `docs/data-sources.md`): descubrimiento de tokens nuevos, holders,
autoridades del mint, liquidez/volumen/precio, scoring por reglas, paper
trading, alertas básicas.

Pero varias fases asumen una escala de indexación que un RPC gratuito
(incluido Helius free) no sostiene para "todo el universo de tokens":

- **Clustering de wallets / detección de bundles a escala**: requiere
  cruzar el historial de miles de wallets contra miles de transacciones.
  Herramientas como Nansen/Arkham cobran precisamente porque mantienen su
  propio indexador — es infraestructura real, no una API que se pueda
  esquivar con paciencia. Es viable a pequeña escala (un token concreto
  que el usuario está mirando activamente), no como barrido continuo de
  todo lo que aparece.
- **"Smart money" con histórico de cientos de wallets**: mismo problema,
  trackear el historial completo de muchas wallets en el tiempo no
  escala con RPC gratuito a "todo el universo de tokens".
- **Backtesting con datos históricos**: solo hay histórico real a partir
  del día en que este propio proyecto empieza a guardarlo (ninguna
  fuente gratuita da histórico retroactivo, ver `docs/data-sources.md`).

Construimos hacia esta visión por fases, priorizando siempre lo
verificadamente gratis, y dejando explícitamente marcado qué partes
necesitarían presupuesto si en el futuro se quiere escalar más allá de
"tokens que el usuario vigila activamente".

## Progreso hasta ahora

- ✅ Fase 1: scaffold backend + frontend, adaptadores con fallback, motor
  de scoring por reglas, dashboard básico.
- ✅ Fase 2: Program ID/IDL de pump.fun verificados, websockets
  casi-tiempo-real (gratis en Helius), watchlist e histórico en el
  dashboard.
- 🔄 Fase 3 (en curso): conectar el listener de websocket a un worker que
  guarda automáticamente los lanzamientos nuevos en la base de datos.

## Documento de visión original (íntegro)

*(pegado tal cual lo definió el usuario, sin editar contenido — algunas
partes requieren presupuesto para escalar más allá de un puñado de
tokens vigilados activamente, ver la nota de realismo arriba)*

---

You are an elite team consisting of:

- Senior Solana blockchain engineer
- Blockchain data engineer
- Quantitative developer
- On-chain forensic analyst
- Memecoin market-structure analyst
- Cybersecurity / rug-pull analyst
- Full-stack engineer
- Data visualization engineer
- UI/UX designer
- Performance engineer

Your task is to BUILD THE BEST FREE SOLANA MEMECOIN TRACKER / INTELLIGENCE TERMINAL POSSIBLE.

(... documento completo disponible en el historial de la conversación con
el usuario; se resume aquí por espacio, pero las 43 fases (Fase 0 a Fase
43) descritas cubren: arquitectura free-first con fallback entre
proveedores, descubrimiento de tokens en tiempo real, inteligencia de
holders y distribución ajustada, análisis de creador y wallets
relacionadas, detección de bundles/coordinación, forense de liquidez,
motor de momentum y extensión, motor de riesgo con explicación factor
por factor, motor de oportunidad, motor de alertas con prioridades,
tabla de tokens en vivo con pestañas, página de forense por token,
gráfico de relaciones de wallets, timeline por token, inteligencia
social solo con fuentes gratuitas, integración de solo lectura con
Axiom (sin claves privadas), optimización móvil, paper trading, registro
de rendimiento de señales, backtesting, panel de salud de proveedores de
datos, y panel de coste — con la regla explícita de que el modo "FREE
MAXIMUM" debe seguir siendo 100% funcional sin ninguna API de pago.)

---
