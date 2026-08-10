"""
GET /api/top-stocks
GET /api/top-stocks/weekly
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, rate_limit
from app.core.cache import Cache
from app.db.models import WeeklyRanking
from app.schemas.stock import TopStocksResponse

router = APIRouter(prefix="/api/top-stocks", tags=["top-stocks"], dependencies=[Depends(rate_limit)])

VALID_CATEGORIES = {"THAI", "US", "GLOBAL", "AI", "GROWTH", "DIVIDEND", "MOMENTUM"}


@router.get("", response_model=TopStocksResponse)
async def get_top_stocks(
    category: str = Query("GLOBAL", description="THAI | US | GLOBAL | AI | GROWTH | DIVIDEND | MOMENTUM"),
    db: AsyncSession = Depends(get_db),
):
    category = category.upper()
    if category not in VALID_CATEGORIES:
        raise HTTPException(400, f"category must be one of {sorted(VALID_CATEGORIES)}")

    cache = Cache()
    cache_key = f"top_stocks:{category}"
    cached = await cache.get_json(cache_key)
    if cached:
        return cached

    result = await db.execute(
        select(WeeklyRanking)
        .where(WeeklyRanking.category == category)
        .order_by(WeeklyRanking.week_of.desc())
        .limit(1)
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "No ranking has been generated yet for this category.")

    response = TopStocksResponse(category=category, week_of=row.week_of, stocks=row.rankings)
    await cache.set_json(cache_key, response.model_dump(), ttl=Cache.TTL_TOP10)
    return response


@router.get("/weekly")
async def get_all_weekly_rankings(db: AsyncSession = Depends(get_db)):
    """All 7 category boards for the most recent week (spec section 44),
    used to render the full Top 10 page with tabs."""
    out = {}
    for category in VALID_CATEGORIES:
        result = await db.execute(
            select(WeeklyRanking)
            .where(WeeklyRanking.category == category)
            .order_by(WeeklyRanking.week_of.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        out[category] = row.rankings if row else []
    return out
