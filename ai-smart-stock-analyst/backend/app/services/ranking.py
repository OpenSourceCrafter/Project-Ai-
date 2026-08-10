"""
Top 10 ranking — spec sections 20, 21, 22, 44.

Ranks by the full AI Score (not raw price gain), and produces SEPARATE
Top 10 lists per category so large-cap US names don't dominate every board:
THAI, US, GLOBAL, AI, GROWTH, DIVIDEND, MOMENTUM (spec section 44).
"""
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class RankableStock:
    ticker: str
    name: str
    country: str          # TH, US, JP, ...
    sector: str
    price: float
    week_change_pct: float
    month_change_pct: float
    year_change_pct: float
    final_score: float
    risk_level: str
    news_sentiment: str
    recommendation: str
    potential_return_low: float
    potential_return_high: float
    dividend_yield: float | None = None
    revenue_growth: float | None = None
    is_ai_related: bool = False


CATEGORY_FILTERS = {
    "THAI": lambda s: s.country == "TH",
    "US": lambda s: s.country == "US",
    "GLOBAL": lambda s: True,
    "AI": lambda s: s.is_ai_related,
    "GROWTH": lambda s: (s.revenue_growth or 0) >= 15,
    "DIVIDEND": lambda s: (s.dividend_yield or 0) >= 1.5,
    "MOMENTUM": lambda s: s.month_change_pct >= 5,
}


def rank_category(stocks: list[RankableStock], category: str, top_n: int = 10) -> list[dict]:
    if category not in CATEGORY_FILTERS:
        raise ValueError(f"Unknown ranking category: {category}")

    filtered = [s for s in stocks if CATEGORY_FILTERS[category](s)]
    ranked = sorted(filtered, key=lambda s: s.final_score, reverse=True)[:top_n]

    return [
        {
            "rank": i + 1,
            "ticker": s.ticker,
            "company": s.name,
            "country": s.country,
            "sector": s.sector,
            "current_price": s.price,
            "week_change_pct": s.week_change_pct,
            "month_change_pct": s.month_change_pct,
            "year_change_pct": s.year_change_pct,
            "ai_score": s.final_score,
            "risk": s.risk_level,
            "news_sentiment": s.news_sentiment,
            "potential_return": f"+{s.potential_return_low:.0f}% to +{s.potential_return_high:.0f}%",
            "recommendation": s.recommendation,
        }
        for i, s in enumerate(ranked)
    ]


def rank_all_categories(stocks: list[RankableStock], top_n: int = 10) -> dict[str, list[dict]]:
    return {category: rank_category(stocks, category, top_n) for category in CATEGORY_FILTERS}


def build_weekly_ranking_rows(stocks: list[RankableStock], top_n: int = 10) -> list[dict]:
    """Flat rows ready to bulk-insert into the `weekly_rankings` table —
    one row per category, `week_of` stamped at the Friday run time."""
    week_of = datetime.now(timezone.utc)
    rankings_by_category = rank_all_categories(stocks, top_n)
    return [
        {"category": category, "week_of": week_of, "rankings": rankings}
        for category, rankings in rankings_by_category.items()
    ]
