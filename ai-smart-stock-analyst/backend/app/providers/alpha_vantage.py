"""
Alpha Vantage implementation of MarketDataProvider + FundamentalProvider.
Chosen as the default because it covers a wide range of global tickers plus
historical OHLCV, fundamentals, and technical indicators in one API (spec section 31).

API key is injected via settings — never hard-coded (spec section 31/49).
"""
from datetime import datetime, timezone

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.providers.base import (
    FundamentalData, FundamentalProvider, MarketDataProvider, OHLCVBar, QuoteData,
)

BASE_URL = "https://www.alphavantage.co/query"


class AlphaVantageProvider(MarketDataProvider, FundamentalProvider):
    def __init__(self, api_key: str | None = None):
        settings = get_settings()
        self.api_key = api_key or settings.market_data_api_key
        self._client = httpx.AsyncClient(base_url=BASE_URL, timeout=15.0)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    async def _get(self, params: dict) -> dict:
        params = {**params, "apikey": self.api_key}
        resp = await self._client.get("", params=params)
        resp.raise_for_status()
        return resp.json()

    # ---------- MarketDataProvider ----------
    async def get_quote(self, ticker: str) -> QuoteData:
        data = await self._get({"function": "GLOBAL_QUOTE", "symbol": ticker})
        quote = data.get("Global Quote") or {}
        price = quote.get("05. price")
        change_pct_raw = quote.get("10. change percent", "").rstrip("%")

        if not price:
            # Never fabricate a number — surface unavailability explicitly (section 45).
            return QuoteData(ticker=ticker, price=None, change_pct=None, as_of=None, is_available=False)

        return QuoteData(
            ticker=ticker,
            price=float(price),
            change_pct=float(change_pct_raw) if change_pct_raw else None,
            as_of=datetime.now(timezone.utc),
            is_available=True,
        )

    async def get_ohlcv(self, ticker: str, interval: str, lookback_days: int) -> list[OHLCVBar]:
        function = "TIME_SERIES_DAILY" if interval in ("1d", "1wk") else "TIME_SERIES_INTRADAY"
        params = {"function": function, "symbol": ticker, "outputsize": "compact"}
        if function == "TIME_SERIES_INTRADAY":
            params["interval"] = interval

        data = await self._get(params)
        series_key = next((k for k in data if "Time Series" in k), None)
        if not series_key:
            return []

        bars: list[OHLCVBar] = []
        for ts_str, ohlcv in list(data[series_key].items())[:lookback_days]:
            bars.append(OHLCVBar(
                timestamp=datetime.fromisoformat(ts_str),
                open=float(ohlcv["1. open"]),
                high=float(ohlcv["2. high"]),
                low=float(ohlcv["3. low"]),
                close=float(ohlcv["4. close"]),
                volume=int(ohlcv["5. volume"]),
            ))
        return list(reversed(bars))  # oldest -> newest

    async def get_index_quote(self, symbol: str) -> QuoteData:
        # Alpha Vantage exposes indices/FX/crypto through separate endpoints;
        # this dispatches based on a simple symbol convention.
        if symbol.upper() in ("USDTHB", "EURUSD"):
            base, quote = symbol[:3], symbol[3:]
            data = await self._get({
                "function": "CURRENCY_EXCHANGE_RATE",
                "from_currency": base, "to_currency": quote,
            })
            rate = data.get("Realtime Currency Exchange Rate", {}).get("5. Exchange Rate")
            if not rate:
                return QuoteData(ticker=symbol, price=None, change_pct=None, as_of=None, is_available=False)
            return QuoteData(ticker=symbol, price=float(rate), change_pct=None,
                              as_of=datetime.now(timezone.utc), is_available=True)

        # Fall back to treating it as a regular quote (works for many index ETF proxies).
        return await self.get_quote(symbol)

    # ---------- FundamentalProvider ----------
    async def get_fundamentals(self, ticker: str) -> FundamentalData | None:
        overview = await self._get({"function": "OVERVIEW", "symbol": ticker})
        if not overview or "Symbol" not in overview:
            return None

        def f(key: str) -> float | None:
            val = overview.get(key)
            try:
                return float(val) if val not in (None, "None", "-") else None
            except ValueError:
                return None

        return FundamentalData(
            revenue=f("RevenueTTM"),
            revenue_growth=f("QuarterlyRevenueGrowthYOY"),
            eps=f("EPS"),
            eps_growth=f("QuarterlyEarningsGrowthYOY"),
            gross_margin=f("GrossProfitTTM"),
            operating_margin=f("OperatingMarginTTM"),
            net_margin=f("ProfitMargin"),
            roe=f("ReturnOnEquityTTM"),
            roa=f("ReturnOnAssetsTTM"),
            debt_to_equity=None,  # not directly provided — derive from BALANCE_SHEET if needed
            free_cash_flow=None,
            cash=None,
            total_debt=None,
            pe=f("PERatio"),
            forward_pe=f("ForwardPE"),
            peg=f("PEGRatio"),
            pb=f("PriceToBookRatio"),
            ps=f("PriceToSalesRatioTTM"),
            ev_ebitda=f("EVToEBITDA"),
            dividend_yield=f("DividendYield"),
            as_of=datetime.now(timezone.utc),
        )

    async def get_financial_statements(self, ticker: str, statement_type: str) -> list[dict]:
        function_map = {
            "income": "INCOME_STATEMENT",
            "balance": "BALANCE_SHEET",
            "cashflow": "CASH_FLOW",
        }
        function = function_map.get(statement_type)
        if not function:
            raise ValueError(f"Unknown statement_type: {statement_type}")

        data = await self._get({"function": function, "symbol": ticker})
        return data.get("quarterlyReports", [])
