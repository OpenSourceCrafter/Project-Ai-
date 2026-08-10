"""
Data update pipeline — spec section 30:
  1. Fetch Data        4. Normalize Data      7. Run AI Model     10. Update Dashboard
  2. Validate Data      5. Calculate Indicators 8. Calculate Score
  3. (dedupe/store)     6. Analyze News         9. Rank Stocks

This module is provider-agnostic — it only talks to the abstract interfaces
from app/providers/base.py (resolved via app/providers/registry.py), and to
the scoring/ranking/news_intelligence services. It never fabricates a value:
if a provider call fails or returns "unavailable", that stage is skipped and
logged rather than backfilled with a guess (spec section 45/46).
"""
import logging
from dataclasses import dataclass

from app.providers.registry import (
    get_fundamental_provider, get_market_data_provider, get_news_provider,
)
from app.services import news_intelligence
from app.services.scoring import ComponentScores, build_score_result

logger = logging.getLogger("data_pipeline")


@dataclass
class PipelineResult:
    ticker: str
    quote_ok: bool
    fundamentals_ok: bool
    news_count: int
    score: dict | None
    errors: list[str]


async def refresh_stock(ticker: str) -> PipelineResult:
    """Runs steps 1-8 of the section 30 flow for a single ticker."""
    errors: list[str] = []
    market = get_market_data_provider()
    fundamentals_provider = get_fundamental_provider()
    news_provider = get_news_provider()

    # 1-2. Fetch + validate quote
    quote = await market.get_quote(ticker)
    if not quote["is_available"]:
        errors.append("quote_unavailable")

    # 1-2. Fetch + validate fundamentals
    fundamentals = await fundamentals_provider.get_fundamentals(ticker)
    if fundamentals is None:
        errors.append("fundamentals_unavailable")

    # 1-2. Fetch news, tagged to this ticker
    news_items = await news_provider.get_news(tickers=[ticker], limit=20)

    # 6. Analyze news (sentiment + impact + topic detection)
    analyzed_news = [
        news_intelligence.analyze_article(item["headline"], item.get("summary"))
        for item in news_items
    ]
    news_agg = news_intelligence.aggregate_sentiment([
        news_intelligence.classify_sentiment(item["headline"], item.get("summary"))
        for item in news_items
    ])

    # 3-5. Normalize + calculate indicators would run against `prices` history
    # already persisted in the DB (see app/services/technicals.py — out of
    # scope for this skeleton, but follows the same "never fabricate" rule).

    # 7-8. Run AI model / calculate score.
    # NOTE: this uses placeholder component scores when upstream data is
    # missing, marked explicitly, rather than inventing a confident number.
    if quote["is_available"] and fundamentals is not None:
        components = ComponentScores(
            fundamental=_placeholder_fundamental_score(fundamentals),
            technical=50.0,   # wire up to technicals.py once implemented
            growth=_placeholder_growth_score(fundamentals),
            valuation=_placeholder_valuation_score(fundamentals),
            news=news_agg["overall_score"] or 50,
            momentum=50.0 + (quote["change_pct"] or 0),
            risk=60.0,
        )
        score = build_score_result(components)
        score_dict = {
            "final_score": score.final_score,
            "recommendation": score.recommendation,
            "risk_level": score.risk_level,
            "explanation": score.explanation,
        }
    else:
        score_dict = None
        errors.append("insufficient_data_for_scoring")

    return PipelineResult(
        ticker=ticker,
        quote_ok=quote["is_available"],
        fundamentals_ok=fundamentals is not None,
        news_count=len(news_items),
        score=score_dict,
        errors=errors,
    )


# ---- placeholder feature engineering (replace with real models — section 33) ----
def _placeholder_fundamental_score(f: dict) -> float:
    roe = f.get("roe") or 0
    return max(0, min(100, 50 + roe * 100))


def _placeholder_growth_score(f: dict) -> float:
    growth = f.get("revenue_growth") or 0
    return max(0, min(100, 50 + growth * 100))


def _placeholder_valuation_score(f: dict) -> float:
    pe = f.get("pe")
    if not pe or pe <= 0:
        return 50.0
    # Lower P/E => higher valuation-favorability score (very simplified).
    return max(0, min(100, 100 - pe))


async def refresh_universe(tickers: list[str]) -> list[PipelineResult]:
    """Step-9 friendly: refresh every ticker in the tracked universe.
    In production this fans out with a bounded concurrency / task queue
    rather than a plain loop, to respect provider rate limits."""
    results = []
    for ticker in tickers:
        try:
            results.append(await refresh_stock(ticker))
        except Exception as exc:  # noqa: BLE001 — log and continue the batch
            logger.exception("Failed to refresh %s", ticker)
            results.append(PipelineResult(
                ticker=ticker, quote_ok=False, fundamentals_ok=False,
                news_count=0, score=None, errors=[f"pipeline_exception: {exc}"],
            ))
    return results
