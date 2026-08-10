/**
 * API client — talks to the FastAPI backend (see ../../backend).
 *
 * Every function here fails SOFT: if the backend isn't running, is still
 * empty (no data seeded yet), or a specific endpoint is still a `501` stub
 * (see backend/README.md "What's stubbed"), these functions return `null`
 * instead of throwing. The UI then falls back to local demo data and shows
 * a "DEMO DATA" badge instead of "LIVE" — so the app is always usable, and
 * it's always visually obvious whether you're looking at real backend data.
 */
const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function safeFetch(path, options) {
  try {
    const res = await fetch(`${BASE_URL}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    if (!res.ok) return null; // includes 501 for not-yet-wired endpoints
    return await res.json();
  } catch {
    return null; // network error / backend not running
  }
}

/** Market indices strip (SET, S&P500, NASDAQ, ...) — GET /api/market */
export async function fetchMarketOverview() {
  return safeFetch("/api/market");
}

/** Top 10 board for one category — GET /api/top-stocks?category=... */
export async function fetchTopStocks(category = "GLOBAL") {
  return safeFetch(`/api/top-stocks?category=${category}`);
}

/** Live quote for one ticker — GET /api/stocks/{ticker}/price */
export async function fetchQuote(ticker) {
  return safeFetch(`/api/stocks/${ticker}/price`);
}

/** Fundamentals snapshot — GET /api/stocks/{ticker}/fundamentals */
export async function fetchFundamentals(ticker) {
  return safeFetch(`/api/stocks/${ticker}/fundamentals`);
}

/** Ticker-tagged news + sentiment/impact — GET /api/stocks/{ticker}/news */
export async function fetchStockNews(ticker) {
  return safeFetch(`/api/stocks/${ticker}/news`);
}

/** General market news — GET /api/news */
export async function fetchGeneralNews(limit = 10) {
  return safeFetch(`/api/news?limit=${limit}`);
}

/** Aggregated Positive/Neutral/Negative sentiment — GET /api/stocks/{ticker}/sentiment */
export async function fetchStockSentiment(ticker) {
  return safeFetch(`/api/stocks/${ticker}/sentiment`);
}

/** Register a new account — POST /api/v1/auth/register */
export async function registerUser(email, password, displayName) {
  return safeFetch("/api/v1/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, display_name: displayName }),
  });
}

/** Quick reachability check, used to flip the LIVE/DEMO badge on load. */
export async function pingBackend() {
  const result = await safeFetch("/healthz");
  return result?.status === "ok";
}
