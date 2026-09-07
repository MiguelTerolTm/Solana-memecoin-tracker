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

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export async function fetchToken(mint: string): Promise<AggregatedToken> {
  const res = await fetch(`${API_BASE_URL}/api/tokens/${mint}`, { cache: "no-store" });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Error ${res.status} consultando el token`);
  }
  return res.json();
}
