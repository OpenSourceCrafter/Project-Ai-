"""
GET /api/stocks
GET /api/stocks/{ticker}
GET /api/stocks/{ticker}/price
GET /api/stocks/{ticker}/fundamentals
GET /api/stocks/{ticker}/news
GET /api/stocks/{ticker}/sentiment
GET /api/stocks/{ticker}/analysis
GET /api/stocks/{ticker}/forecast
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import rate_limit
from app.core.cache import Cache
from app.providers.registry import (
    get_fundamental_provider, get_market_data_provider, get_news_provider,
)
from app.schemas.stock import DataMeta, QuoteResponse
from app.services import news_intelligence

router = APIRouter(prefix="/api/stocks", tags=["stocks"], dependencies=[Depends(rate_limit)])


@router.get("")
async def search_stocks(
    q: str | None = Query(None, description="Ticker or company name substring"),
    country: str | None = None,
    sector: str | None = None,
    min_ai_score: float | None = None,
    risk: str | None = None,
    limit: int = 25,
):
    """
    Search + filter (spec section 38). In production this queries the
    `stocks` table joined with the latest `ai_scores` row per stock;
    left as a documented contract here since it depends on live DB data.
    """
    raise HTTPException(501, "Wire this up to the `stocks` + `ai_scores` tables in your DB.")


@router.get("/{ticker}")
async def get_stock(ticker: str):
    raise HTTPException(501, "Return Stock row + latest AIScore joined — see StockAnalysisResponse.")


@router.get("/{ticker}/price", response_model=QuoteResponse)
async def get_price(ticker: str):
    cache = Cache()
    cache_key = f"quote:{ticker}"
    cached = await cache.get_json(cache_key)
    if cached:
        return cached

    provider = get_market_data_provider()
    quote = await provider.get_quote(ticker)

    response = QuoteResponse(
        ticker=quote["ticker"],
        price=quote["price"],
        change_pct=quote["change_pct"],
        meta=DataMeta(
            data_updated=quote["as_of"],
            data_source="Alpha Vantage",
            is_available=quote["is_available"],
        ),
    )
    if quote["is_available"]:
        await cache.set_json(cache_key, response.model_dump(), ttl=Cache.TTL_QUOTE)
    return response


@router.get("/{ticker}/fundamentals")
async def get_fundamentals(ticker: str):
    cache = Cache()
    cache_key = f"fundamentals:{ticker}"
    cached = await cache.get_json(cache_key)
    if cached:
        return cached

    provider = get_fundamental_provider()
    data = await provider.get_fundamentals(ticker)

    if data is None:
        # spec section 45 — never fabricate; return an explicit "insufficient data" shape
        return {
            "ticker": ticker,
            "available": False,
            "message": "ข้อมูลไม่เพียงพอสำหรับการประเมิน",
        }

    result = {"ticker": ticker, "available": True, **data}
    await cache.set_json(cache_key, result, ttl=Cache.TTL_FUNDAMENTAL)
    return result


@router.get("/{ticker}/news")
async def get_stock_news(ticker: str, limit: int = 20):
    cache = Cache()
    cache_key = f"news:{ticker}:{limit}"
    cached = await cache.get_json(cache_key)
    if cached:
        return cached

    provider = get_news_provider()
    items = await provider.get_news(tickers=[ticker], limit=limit)

    analyzed = [
        {**item, **news_intelligence.analyze_article(item["headline"], item.get("summary"))}
        for item in items
    ]
    await cache.set_json(cache_key, analyzed, ttl=Cache.TTL_NEWS)
    return analyzed


@router.get("/{ticker}/sentiment")
async def get_stock_sentiment(ticker: str):
    provider = get_news_provider()
    items = await provider.get_news(tickers=[ticker], limit=50)
    sentiments = [
        news_intelligence.classify_sentiment(item["headline"], item.get("summary"))
        for item in items
    ]
    return news_intelligence.aggregate_sentiment(sentiments)


@router.get("/{ticker}/analysis")
async def get_stock_analysis(ticker: str):
    """
    Full Stock Analysis Page payload (spec section 6-9): quote + AI score +
    support/resistance + AI estimated range. Aggregates the other endpoints
    above — in production, prefer joining from the DB over re-fetching live,
    since AIScore/TechnicalIndicator rows are already computed by the pipeline.
    """
    raise HTTPException(
        501,
        "Compose QuoteResponse + latest AIScore + TechnicalIndicator row "
        "into StockAnalysisResponse — see app/schemas/stock.py.",
    )


@router.get("/{ticker}/forecast")
async def get_stock_forecast(ticker: str):
    """AI Price Forecast (spec section 11) — reads the most recent Prediction
    rows per horizon (7d/30d/3m/6m/12m), produced offline by the forecasting
    model and written to the `predictions` table."""
    raise HTTPException(501, "Query `predictions` table for latest row per horizon for this ticker.")
