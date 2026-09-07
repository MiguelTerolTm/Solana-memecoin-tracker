"use client";

import { useState } from "react";
import { fetchToken, AggregatedToken } from "../lib/api";

export default function Home() {
  const [mint, setMint] = useState("");
  const [data, setData] = useState<AggregatedToken | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!mint.trim()) return;
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const result = await fetchToken(mint.trim());
      setData(result);
    } catch (err: any) {
      setError(err.message || "Error desconocido");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ maxWidth: 720, margin: "0 auto", padding: "2rem 1rem", fontFamily: "system-ui, sans-serif" }}>
      <h1 style={{ fontSize: "1.5rem", marginBottom: "0.25rem" }}>Solana Memecoin Intelligence Tracker</h1>
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
          <h2 style={{ marginTop: 0 }}>{data.mint}</h2>

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
            <section>
              <h3>Riesgo (fuente: {data.risk.source})</h3>
              <p>Mint authority activa: {String(data.risk.mint_authority_active)}</p>
              <p>Freeze authority activa: {String(data.risk.freeze_authority_active)}</p>
              <p>Top 10 holders: {data.risk.top10_holder_pct ?? "N/D"}%</p>
              <p>LP bloqueada: {data.risk.lp_locked_pct ?? "N/D"}%</p>
            </section>
          )}
        </div>
      )}
    </main>
  );
}
