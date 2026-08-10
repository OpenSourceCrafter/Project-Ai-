"""
ORM models — one class per table from spec section 39:
users, stocks, prices, fundamentals, financial_statements, news, sentiments,
technical_indicators, ai_scores, predictions, watchlists, portfolios, alerts,
weekly_rankings, model_performance, market_data.
"""
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    JSON, BigInteger, Boolean, DateTime, Enum, Float, ForeignKey, Integer,
    Numeric, String, Text, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


# ---------- enums ----------
class RecommendationEnum(str, PyEnum):
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    ACCUMULATE = "ACCUMULATE"
    HOLD = "HOLD"
    WATCH = "WATCH"
    REDUCE = "REDUCE"
    SELL = "SELL"


class RiskLevelEnum(str, PyEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class SentimentEnum(str, PyEnum):
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"


class AlertTypeEnum(str, PyEnum):
    PRICE_TARGET = "PRICE_TARGET"
    SUPPORT_BREAK = "SUPPORT_BREAK"
    RSI_LOW = "RSI_LOW"
    RSI_HIGH = "RSI_HIGH"
    NEWS_HIGH_IMPACT = "NEWS_HIGH_IMPACT"
    EARNINGS = "EARNINGS"
    AI_SCORE_CHANGE = "AI_SCORE_CHANGE"
    RECOMMENDATION_CHANGE = "RECOMMENDATION_CHANGE"
    RISK_CHANGE = "RISK_CHANGE"


# ---------- core entities ----------
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str | None] = mapped_column(String(100))
    subscription_tier: Mapped[str] = mapped_column(String(20), default="FREE")  # FREE | PRO | PREMIUM
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    watchlists: Mapped[list["Watchlist"]] = relationship(back_populates="user")
    portfolios: Mapped[list["Portfolio"]] = relationship(back_populates="user")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="user")


class Stock(Base):
    __tablename__ = "stocks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ticker: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    country: Mapped[str] = mapped_column(String(4))          # ISO country code: TH, US, JP, HK, CN, KR, GB, DE, AU...
    exchange: Mapped[str] = mapped_column(String(20))         # SET, mai, NYSE, NASDAQ, TSE, HKEX, ...
    sector: Mapped[str] = mapped_column(String(50))
    industry: Mapped[str | None] = mapped_column(String(100))
    currency: Mapped[str] = mapped_column(String(6), default="USD")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    prices: Mapped[list["Price"]] = relationship(back_populates="stock")
    fundamentals: Mapped[list["Fundamental"]] = relationship(back_populates="stock")


class Price(Base):
    """OHLCV bar. `interval` distinguishes intraday vs daily bars."""
    __tablename__ = "prices"
    __table_args__ = (UniqueConstraint("stock_id", "timestamp", "interval", name="uq_price_bar"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id", ondelete="CASCADE"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    interval: Mapped[str] = mapped_column(String(10), default="1d")  # 1m,5m,15m,1h,1d,1wk
    open: Mapped[float] = mapped_column(Numeric(18, 4))
    high: Mapped[float] = mapped_column(Numeric(18, 4))
    low: Mapped[float] = mapped_column(Numeric(18, 4))
    close: Mapped[float] = mapped_column(Numeric(18, 4))
    volume: Mapped[int] = mapped_column(BigInteger)
    source: Mapped[str] = mapped_column(String(50))  # which provider this bar came from

    stock: Mapped["Stock"] = relationship(back_populates="prices")


class Fundamental(Base):
    """Latest-known fundamental/valuation snapshot for a stock (refreshed daily)."""
    __tablename__ = "fundamentals"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id", ondelete="CASCADE"), index=True)
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    revenue: Mapped[float | None] = mapped_column(Numeric(20, 2))
    revenue_growth: Mapped[float | None] = mapped_column(Float)
    eps: Mapped[float | None] = mapped_column(Numeric(10, 4))
    eps_growth: Mapped[float | None] = mapped_column(Float)
    gross_margin: Mapped[float | None] = mapped_column(Float)
    operating_margin: Mapped[float | None] = mapped_column(Float)
    net_margin: Mapped[float | None] = mapped_column(Float)
    roe: Mapped[float | None] = mapped_column(Float)
    roa: Mapped[float | None] = mapped_column(Float)
    debt_to_equity: Mapped[float | None] = mapped_column(Float)
    free_cash_flow: Mapped[float | None] = mapped_column(Numeric(20, 2))
    cash: Mapped[float | None] = mapped_column(Numeric(20, 2))
    total_debt: Mapped[float | None] = mapped_column(Numeric(20, 2))

    pe: Mapped[float | None] = mapped_column(Float)
    forward_pe: Mapped[float | None] = mapped_column(Float)
    peg: Mapped[float | None] = mapped_column(Float)
    pb: Mapped[float | None] = mapped_column(Float)
    ps: Mapped[float | None] = mapped_column(Float)
    ev_ebitda: Mapped[float | None] = mapped_column(Float)
    dividend_yield: Mapped[float | None] = mapped_column(Float)

    source: Mapped[str] = mapped_column(String(50))

    stock: Mapped["Stock"] = relationship(back_populates="fundamentals")


class FinancialStatement(Base):
    """Raw statement line items (quarterly/annual), kept separate from the
    derived `fundamentals` snapshot so nothing is ever fabricated on gaps."""
    __tablename__ = "financial_statements"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id", ondelete="CASCADE"), index=True)
    period: Mapped[str] = mapped_column(String(10))       # e.g. "2026Q2", "2025FY"
    statement_type: Mapped[str] = mapped_column(String(20))  # income | balance | cashflow
    line_items: Mapped[dict] = mapped_column(JSON)         # raw provider payload, normalized keys
    source: Mapped[str] = mapped_column(String(50))
    filed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class NewsArticle(Base):
    __tablename__ = "news"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    external_id: Mapped[str] = mapped_column(String(255), unique=True)  # dedupe key from provider
    headline: Mapped[str] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(100))
    language: Mapped[str] = mapped_column(String(8))       # th, en, ja, zh, ko, de, ...
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    tickers: Mapped[list[str]] = mapped_column(JSON)        # ticker-tagged, per spec section 31
    topics: Mapped[list[str]] = mapped_column(JSON, default=list)  # Earnings, FDA, M&A, etc. (section 16)
    is_high_impact: Mapped[bool] = mapped_column(Boolean, default=False)

    sentiments: Mapped[list["NewsSentiment"]] = relationship(back_populates="article")


class NewsSentiment(Base):
    """Per-article, per-ticker sentiment score (an article can tag >1 ticker)."""
    __tablename__ = "sentiments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    news_id: Mapped[int] = mapped_column(ForeignKey("news.id", ondelete="CASCADE"))
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id", ondelete="CASCADE"), index=True)
    sentiment: Mapped[SentimentEnum] = mapped_column(Enum(SentimentEnum, name="sentiment_enum"))
    sentiment_score: Mapped[float] = mapped_column(Float)   # -1.0 .. +1.0
    impact_score: Mapped[int] = mapped_column(Integer)      # 0-100, section 14/17
    model_name: Mapped[str] = mapped_column(String(50))     # e.g. "finbert-v1"
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    article: Mapped["NewsArticle"] = relationship(back_populates="sentiments")


class TechnicalIndicator(Base):
    """Computed indicator snapshot per stock per day (not fetched — derived from `prices`)."""
    __tablename__ = "technical_indicators"
    __table_args__ = (UniqueConstraint("stock_id", "as_of", name="uq_indicator_day"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id", ondelete="CASCADE"), index=True)
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    ma20: Mapped[float | None] = mapped_column(Float)
    ma50: Mapped[float | None] = mapped_column(Float)
    ma100: Mapped[float | None] = mapped_column(Float)
    ma200: Mapped[float | None] = mapped_column(Float)
    ema: Mapped[float | None] = mapped_column(Float)
    rsi: Mapped[float | None] = mapped_column(Float)
    macd: Mapped[float | None] = mapped_column(Float)
    macd_signal: Mapped[float | None] = mapped_column(Float)
    bollinger_upper: Mapped[float | None] = mapped_column(Float)
    bollinger_lower: Mapped[float | None] = mapped_column(Float)
    support: Mapped[float | None] = mapped_column(Float)
    resistance: Mapped[float | None] = mapped_column(Float)


class AIScore(Base):
    """Final weighted AI Investment Score — the output of app/services/scoring.py.
    One row per stock per scoring run (history is kept for the 'AI Score changed' alert)."""
    __tablename__ = "ai_scores"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id", ondelete="CASCADE"), index=True)
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    fundamental_score: Mapped[float] = mapped_column(Float)
    technical_score: Mapped[float] = mapped_column(Float)
    growth_score: Mapped[float] = mapped_column(Float)
    valuation_score: Mapped[float] = mapped_column(Float)
    news_score: Mapped[float] = mapped_column(Float)
    momentum_score: Mapped[float] = mapped_column(Float)
    risk_score: Mapped[float] = mapped_column(Float)

    final_score: Mapped[float] = mapped_column(Float)        # 0-100, weighted per section 21
    recommendation: Mapped[RecommendationEnum] = mapped_column(Enum(RecommendationEnum, name="recommendation_enum"))
    risk_level: Mapped[RiskLevelEnum] = mapped_column(Enum(RiskLevelEnum, name="risk_level_enum"))
    explanation: Mapped[dict] = mapped_column(JSON)          # {"positive": [...], "negative": [...]}


class Prediction(Base):
    """AI price forecast range for a stock at a given horizon."""
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id", ondelete="CASCADE"), index=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    horizon: Mapped[str] = mapped_column(String(10))         # 7d, 30d, 3m, 6m, 12m
    range_low: Mapped[float] = mapped_column(Numeric(18, 4))
    range_high: Mapped[float] = mapped_column(Numeric(18, 4))
    confidence: Mapped[int] = mapped_column(Integer)          # 0-100
    confidence_factors: Mapped[dict] = mapped_column(JSON)    # {"positive": [...], "caution": [...]}
    model_version: Mapped[str] = mapped_column(String(50))

    # Historical accuracy is tracked separately once the horizon has elapsed —
    # see ModelPerformance. A Prediction never claims certainty (section 46).


class Watchlist(Base):
    __tablename__ = "watchlists"
    __table_args__ = (UniqueConstraint("user_id", "stock_id", name="uq_watchlist_stock"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id", ondelete="CASCADE"), index=True)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="watchlists")


class Portfolio(Base):
    __tablename__ = "portfolios"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100), default="My Portfolio")
    cash_thb: Mapped[float] = mapped_column(Numeric(20, 2), default=0)
    holdings: Mapped[list[dict]] = mapped_column(JSON)   # [{"ticker": "NVDA", "weight_pct": 25.0, "shares": 10}, ...]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="portfolios")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id", ondelete="CASCADE"), index=True)
    alert_type: Mapped[AlertTypeEnum] = mapped_column(Enum(AlertTypeEnum, name="alert_type_enum"))
    threshold: Mapped[dict | None] = mapped_column(JSON)   # e.g. {"price": 150} or {"rsi_below": 30}
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="alerts")


class WeeklyRanking(Base):
    """Snapshot of a Top-10 list for one category/week — produced by the Friday cron job."""
    __tablename__ = "weekly_rankings"
    __table_args__ = (UniqueConstraint("category", "week_of", name="uq_ranking_week"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    category: Mapped[str] = mapped_column(String(30), index=True)  # THAI, US, GLOBAL, AI, GROWTH, DIVIDEND, MOMENTUM
    week_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    rankings: Mapped[list[dict]] = mapped_column(JSON)  # [{"rank":1,"ticker":"NVDA","score":94,...}, ...]
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ModelPerformance(Base):
    """Historical Model Performance (never "prediction accuracy guaranteed") — section 35."""
    __tablename__ = "model_performance"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    horizon: Mapped[str] = mapped_column(String(10))     # 7d, 30d, 90d
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    directional_accuracy: Mapped[float] = mapped_column(Float)
    precision: Mapped[float] = mapped_column(Float)
    recall: Mapped[float] = mapped_column(Float)
    f1_score: Mapped[float] = mapped_column(Float)
    mae: Mapped[float] = mapped_column(Float)
    rmse: Mapped[float] = mapped_column(Float)
    sample_size: Mapped[int] = mapped_column(Integer)


class MarketData(Base):
    """Index levels, macro & commodity data (SET, S&P500, Fed rate, oil, gold, USD/THB, ...)."""
    __tablename__ = "market_data"
    __table_args__ = (UniqueConstraint("symbol", "timestamp", name="uq_market_data_point"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(30), index=True)   # SET, SPX, NDX, XAU, BTCUSD, USDTHB, FED_RATE...
    category: Mapped[str] = mapped_column(String(20))              # index | commodity | fx | crypto | macro
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    value: Mapped[float] = mapped_column(Numeric(20, 6))
    change_pct: Mapped[float | None] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(50))
