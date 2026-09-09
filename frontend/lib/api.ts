export interface TokenScore {
  value: number;
  label: string;
  reasons: string[];
  missing_data: string[];
}

export interface MarketSnapshot {
  price_usd: number | null;
  liquidity_usd: number | null;
  volume_24h_usd: number | null;
  price_change_24h_pct: number | null;
  source: string;
}

export interface RiskReport {
  risk_score: number | null;
  mint_authority_active: boolean | null;
  freeze_authority_active: boolean | null;
  top10_holder_pct: number | null;
  lp_locked_pct: number | null;
  flags: string[];
  source: string;
}

export interface AggregatedToken {
  mint: string;
  market: MarketSnapshot | null;
  risk: RiskReport | null;
  score: TokenScore | null;
}

export interface WatchlistEntry {
  mint: string;
  symbol: string | null;
  added_at: string;
  note: string | null;
}

export interface HistoryPoint {
  fetched_at: string;
  price_usd: number | null;
  liquidity_usd: number | null;
  tracker_score: number | null;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export async function fetchToken(mint: string): Promise<AggregatedToken> {
  const res = await fetch(`${API_BASE_URL}/api/tokens/${mint}`, { cache: "no-store" });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Error ${res.status} consultando el token`);
  }
  return res.json();
}

export async function fetchTokenHistory(mint: string): Promise<HistoryPoint[]> {
  const res = await fetch(`${API_BASE_URL}/api/tokens/${mint}/history`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Error ${res.status} consultando el histórico`);
  return res.json();
}

export async function fetchWatchlist(): Promise<WatchlistEntry[]> {
  const res = await fetch(`${API_BASE_URL}/api/watchlist`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Error ${res.status} consultando la watchlist`);
  return res.json();
}

export async function addToWatchlist(mint: string, note?: string): Promise<void> {
  const url = new URL(`${API_BASE_URL}/api/watchlist/${mint}`);
  if (note) url.searchParams.set("note", note);
  const res = await fetch(url.toString(), { method: "POST" });
  if (!res.ok) throw new Error(`Error ${res.status} añadiendo a la watchlist`);
}
