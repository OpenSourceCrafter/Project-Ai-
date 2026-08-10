"""
Provider interfaces (spec section 31). The rest of the app talks to these
abstract classes only — never to a specific vendor SDK directly — so the
underlying data source can be swapped via MARKET_DATA_PROVIDER / NEWS_PROVIDER
/ FUNDAMENTAL_PROVIDER / ECONOMIC_DATA_PROVIDER without touching business logic.

Every method returns None / [] / a well-defined "no data" shape instead of
fabricating a value — see app/services/data_pipeline.py for how callers must
handle that (spec section 45/46: never invent data).
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import TypedDict


class OHLCVBar(TypedDict):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


class QuoteData(TypedDict):
    ticker: str
    price: float | None
    change_pct: float | None
    as_of: datetime | None
    is_available: bool          # False => frontend must show "Data temporarily unavailable"


class FundamentalData(TypedDict, total=False):
    revenue: float | None
    revenue_growth: float | None
    eps: float | None
    eps_growth: float | None
    gross_margin: float | None
    operating_margin: float | None
    net_margin: float | None
    roe: float | None
    roa: float | None
    debt_to_equity: float | None
    free_cash_flow: float | None
    cash: float | None
    total_debt: float | None
    pe: float | None
    forward_pe: float | None
    peg: float | None
    pb: float | None
    ps: float | None
    ev_ebitda: float | None
    dividend_yield: float | None
    as_of: datetime | None


class NewsItem(TypedDict):
    external_id: str
    headline: str
    summary: str | None
    url: str
    source: str
    language: str
    published_at: datetime
    tickers: list[str]          # ticker-tagged, per spec section 31


class EconomicDataPoint(TypedDict):
    series: str                  # e.g. "FED_RATE", "US_CPI", "TH_GDP"
    country: str
    value: float
    as_of: datetime


class MarketDataProvider(ABC):
    """Live/intraday quotes + historical OHLCV. e.g. Alpha Vantage, Polygon, Finnhub, Twelve Data."""

    @abstractmethod
    async def get_quote(self, ticker: str) -> QuoteData: ...

    @abstractmethod
    async def get_ohlcv(self, ticker: str, interval: str, lookback_days: int) -> list[OHLCVBar]: ...

    @abstractmethod
    async def get_index_quote(self, symbol: str) -> QuoteData:
        """For market indices / commodities / FX, e.g. SET, SPX, XAU, USDTHB."""
        ...


class FundamentalProvider(ABC):
    """Financial statements & valuation ratios. e.g. Alpha Vantage, Financial Modeling Prep."""

    @abstractmethod
    async def get_fundamentals(self, ticker: str) -> FundamentalData | None: ...

    @abstractmethod
    async def get_financial_statements(self, ticker: str, statement_type: str) -> list[dict]: ...


class NewsProvider(ABC):
    """Ticker-tagged financial news with sentiment where the provider supplies it.
    e.g. Marketaux. Our own NLP layer (app/services/news_intelligence.py) can
    re-score sentiment/impact on top of whatever the provider returns."""

    @abstractmethod
    async def get_news(
        self, tickers: list[str] | None = None, languages: list[str] | None = None, limit: int = 50
    ) -> list[NewsItem]: ...


class EconomicDataProvider(ABC):
    """Macro data: interest rates, inflation, GDP, employment, PMI, oil, gold, bond yields."""

    @abstractmethod
    async def get_series(self, series: str, country: str) -> list[EconomicDataPoint]: ...
