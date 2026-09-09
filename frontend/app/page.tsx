"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  fetchToken,
  fetchTokenHistory,
  addToWatchlist,
  AggregatedToken,
  HistoryPoint,
} from "../lib/api";
import Sparkline from "./components/Sparkline";

function HomeContent() {
  const searchParams = useSearchParams();
  const [mint, setMint] = useState(searchParams.get("mint") || "");
  const [data, setData] = useState<AggregatedToken | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [history, setHistory] = useState<HistoryPoint[] | null>(null);
  const [historyLoading, setHistoryLoading] = useState(false);

  const [watchlistStatus, setWatchlistStatus] = useState<string | null>(null);

  async function runSearch(targetMint: string) {
    if (!targetMint.trim()) return;
    setLoading(true);
    setError(null);
    setData(null);
    setHistory(null);
    setWatchlistStatus(null);
    try {
      const result = await fetchToken(targetMint.trim());
      setData(result);
    } catch (err: any) {
      setError(err.message || "Error desconocido");
    } finally {
      setLoading(false);
    }
  }

  // Si llegamos desde /watchlist con ?mint=..., analizar automáticamente.
  useEffect(() => {
    const fromUrl = searchParams.get("mint");
    if (fromUrl) {
      setMint(fromUrl);
      runSearch(fromUrl);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    await runSearch(mint);
  }

  async function handleAddToWatchlist() {
    if (!data) return;
    try {
      await addToWatchlist(data.mint);
      setWatchlistStatus("Añadido a la watchlist.");
    } catch (err: any) {
      setWatchlistStatus(err.message || "Error añadiendo a la watchlist");
    }
  }

  async function handleShowHistory() {
    if (!data) return;
    setHistoryLoading(true);
    try {
      const points = await fetchTokenHistory(data.mint);
      setHistory(points);
    } catch (err: any) {
      setError(err.message || "Error consultando el histórico");
    } finally {
      setHistoryLoading(false);
    }
  }

  return (
    <main style={{ maxWidth: 720, margin: "0 auto", padding: "2rem 1rem", fontFamily: "system-ui, sans-serif" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <h1 style={{ fontSize: "1.5rem", marginBottom: "0.25rem" }}>Solana Memecoin Intelligence Tracker</h1>
        <Link href="/watchlist" style={{ color: "#111", fontSize: "0.9rem" }}>
          Ver watchlist →
        </Link>
      </div>
      <p style={{ color: "#666", marginBottom: "1.5rem" }}>
        Herramienta de investigación de solo lectura. No es asesoramiento financiero, no ejecuta
        trading y no requiere conectar ninguna wallet.
      </p>

      <form onSubmit={handleSearch} style={{ display: "flex", gap: "0.5rem", marginBottom: "1.5rem" }}>
        <input
          value={mint}
          onChange={(e) => setMint(e.target.value)}
          placeholder="Dirección del mint (ej. DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263)"
          style={{ flex: 1, padding: "0.6rem", border: "1px solid #ccc", borderRadius: 6 }}
        />
        <button
          type="submit"
          disabled={loading}
          style={{ padding: "0.6rem 1.2rem", borderRadius: 6, border: "none", background: "#111", color: "#fff" }}
        >
          {loading ? "Analizando..." : "Analizar"}
        </button>
      </form>

      {error && <p style={{ color: "#c00" }}>{error}</p>}

      {data && (
        <div style={{ border: "1px solid #e2e2e2", borderRadius: 10, padding: "1.25rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
            <h2 style={{ marginTop: 0 }}>{data.mint}</h2>
            <button
              onClick={handleAddToWatchlist}
              style={{
                padding: "0.4rem 0.8rem",
                borderRadius: 6,
                border: "1px solid #111",
                background: "#fff",
                cursor: "pointer",
                whiteSpace: "nowrap",
              }}
            >
              + Watchlist
            </button>
          </div>
          {watchlistStatus && <p style={{ color: "#666", fontSize: "0.85rem" }}>{watchlistStatus}</p>}

          {data.score && (
            <div style={{ marginBottom: "1rem" }}>
              <strong>Score: {data.score.value}/100</strong> — {data.score.label}
              <ul>
                {data.score.reasons.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
              {data.score.missing_data.length > 0 && (
                <p style={{ color: "#a66", fontSize: "0.9rem" }}>
                  Datos no disponibles: {data.score.missing_data.join(", ")}
                </p>
              )}
            </div>
          )}

          {data.market && (
            <section style={{ marginBottom: "1rem" }}>
              <h3>Mercado (fuente: {data.market.source})</h3>
              <p>Precio: {data.market.price_usd ?? "N/D"} USD</p>
              <p>Liquidez: {data.market.liquidity_usd ?? "N/D"} USD</p>
              <p>Volumen 24h: {data.market.volume_24h_usd ?? "N/D"} USD</p>
            </section>
          )}

          {data.risk && (
            <section style={{ marginBottom: "1rem" }}>
              <h3>Riesgo (fuente: {data.risk.source})</h3>
              <p>Mint authority activa: {String(data.risk.mint_authority_active)}</p>
              <p>Freeze authority activa: {String(data.risk.freeze_authority_active)}</p>
              <p>Top 10 holders: {data.risk.top10_holder_pct ?? "N/D"}%</p>
              <p>LP bloqueada: {data.risk.lp_locked_pct ?? "N/D"}%</p>
            </section>
          )}

          <section>
            <button
              onClick={handleShowHistory}
              disabled={historyLoading}
              style={{ padding: "0.4rem 0.8rem", borderRadius: 6, border: "1px solid #ccc", background: "#fff" }}
            >
              {historyLoading ? "Cargando histórico..." : "Ver histórico"}
            </button>
            {history && (
              <div style={{ marginTop: "1rem" }}>
                <h3>Histórico de precio (propio, guardado en cada consulta)</h3>
                <Sparkline
                  values={history.map((h) => h.price_usd).filter((v): v is number => v !== null)}
                />
                <p style={{ color: "#888", fontSize: "0.85rem" }}>
                  {history.length} snapshot(s) guardados. Consulta este token varias veces a lo
                  largo del tiempo para que el histórico sea más útil — ninguna fuente gratuita
                  nos da histórico real, así que este es el único hilo de continuidad temporal
                  que tenemos (ver docs/architecture.md).
                </p>
              </div>
            )}
          </section>
        </div>
      )}
    </main>
  );
}

export default function Home() {
  return (
    <Suspense fallback={null}>
      <HomeContent />
    </Suspense>
  );
}
