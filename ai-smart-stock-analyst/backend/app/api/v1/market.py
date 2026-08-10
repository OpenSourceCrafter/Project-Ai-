"""
GET /api/market
GET /api/sectors
GET /api/news
"""
from fastapi import APIRouter, Depends

from app.api.deps import rate_limit
from app.core.cache import Cache
from app.providers.registry import get_market_data_provider, get_news_provider
from app.services import news_intelligence

router = APIRouter(tags=["market"], dependencies=[Depends(rate_limit)])

# Spec section 3: indices/commodities/FX tracked on the dashboard
TRACKED_INDICES = [
    "SET", "SET50", "SPX", "NDX", "DJI", "N225", "HSI", "SHCOMP", "BTCUSD", "XAU", "USDTHB",
]


@router.get("/api/market")
async def get_market_overview():
    cache = Cache()
    cache_key = "market_overview"
    cached = await cache.get_json(cache_key)
    if cached:
        return cached

    provider = get_market_data_provider()
    results = []
    for symbol in TRACKED_INDICES:
        quote = await provider.get_index_quote(symbol)
        results.append({
            "symbol": symbol,
            "value": quote["price"],
            "change_pct": quote["change_pct"],
            "is_available": quote["is_available"],
            "data_updated": quote["as_of"],
        })

    await cache.set_json(cache_key, results, ttl=Cache.TTL_QUOTE)
    return results


@router.get("/api/sectors")
async def get_sector_heatmap():
    """
    Sector heatmap (spec section 19). In production this aggregates the
    average AI Score / week-change across all stocks in each sector —
    a DB aggregation query, not a live provider call.
    """
    return {"message": "Aggregate ai_scores + prices by Stock.sector — see spec section 19."}


@router.get("/api/news")
async def get_general_news(limit: int = 30, languages: str | None = None):
    provider = get_news_provider()
    lang_list = languages.split(",") if languages else None
    items = await provider.get_news(languages=lang_list, limit=limit)
    return [
        {**item, **news_intelligence.analyze_article(item["headline"], item.get("summary"))}
        for item in items
    ]
