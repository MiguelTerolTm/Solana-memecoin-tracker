# Solana Memecoin Intelligence Tracker

Herramienta de investigación de solo lectura para memecoins de Solana.
Agrega varias fuentes gratuitas con fallback automático, calcula un score
transparente de "merece investigarse", y guarda histórico propio.

**Este proyecto NO ejecuta trading automático, no gestiona wallets, y
nunca requiere seed phrases ni claves privadas.** El score que genera es
informativo, no una recomendación financiera.

## Documentación de diseño

- [`docs/architecture.md`](docs/architecture.md) — capas del sistema y por qué existe el fallback.
- [`docs/data-sources.md`](docs/data-sources.md) — qué fuentes se usan, límites gratuitos y qué queda pendiente de verificar.
- [`docs/risk-methodology.md`](docs/risk-methodology.md) — cómo se calcula el score y por qué.

## Poner en marcha (desarrollo local)

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # rellena SOLANA_RPC_URL con tu RPC dedicado gratuito
uvicorn app.main:app --reload
```

La API queda en `http://localhost:8000` (docs interactivas en `/docs`).

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

El dashboard queda en `http://localhost:3000`.

### Con Docker

```bash
cp backend/.env.example backend/.env   # y rellénalo
docker compose up --build
```

## Estado del proyecto

Fase 1 (scaffold funcional): adaptadores con fallback, lectura on-chain
de mint/freeze authority y holders, scoring por reglas, API y dashboard
básico. Pendiente antes de producción: ver la sección "Pendiente de
confirmar" en `docs/data-sources.md` — en particular, el decoder de la
bonding curve de pump.fun está desactivado por defecto hasta verificarse
contra el programa real.
