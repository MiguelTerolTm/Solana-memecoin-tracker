"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { fetchWatchlist, WatchlistEntry } from "../../lib/api";

export default function WatchlistPage() {
  const [entries, setEntries] = useState<WatchlistEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchWatchlist()
      .then(setEntries)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main style={{ maxWidth: 720, margin: "0 auto", padding: "2rem 1rem", fontFamily: "system-ui, sans-serif" }}>
      <Link href="/" style={{ color: "#666" }}>
        ← Volver al analizador
      </Link>
      <h1 style={{ fontSize: "1.5rem" }}>Tu watchlist</h1>

      {loading && <p>Cargando...</p>}
      {error && <p style={{ color: "#c00" }}>{error}</p>}

      {!loading && entries.length === 0 && (
        <p style={{ color: "#666" }}>
          Todavía no has añadido ningún token. Analiza uno en la página principal y pulsa
          "Añadir a watchlist".
        </p>
      )}

      <ul style={{ listStyle: "none", padding: 0 }}>
        {entries.map((e) => (
          <li
            key={e.mint}
            style={{
              border: "1px solid #e2e2e2",
              borderRadius: 8,
              padding: "0.75rem 1rem",
              marginBottom: "0.5rem",
            }}
          >
            <Link href={`/?mint=${e.mint}`} style={{ fontWeight: 600, color: "#111" }}>
              {e.symbol || e.mint}
            </Link>
            <p style={{ margin: "0.25rem 0 0", color: "#888", fontSize: "0.85rem" }}>
              {e.mint} · añadido {new Date(e.added_at).toLocaleString()}
              {e.note ? ` · ${e.note}` : ""}
            </p>
          </li>
        ))}
      </ul>
    </main>
  );
}
