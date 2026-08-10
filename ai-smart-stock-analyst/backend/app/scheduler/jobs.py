"""
Weekly ranking job — spec section 43:

  Fetch Latest Data -> Update Fundamentals -> Fetch News -> Analyze Sentiment
  -> Calculate Technical Indicators -> Run AI -> Calculate Score
  -> Rank Global Stocks -> Generate Top 10 -> Generate Weekly Report
  -> Save Database -> Notify Users

Runs every Friday after major markets close (spec section 43), timezone-aware
per WEEKLY_RANKING_TIMEZONE (defaults to America/New_York — i.e. US close).
Thai/other-market timezone handling: `TRACKED_UNIVERSE` below tags each
ticker's home market; when scheduling per-market close times, wrap the same
`run_weekly_ranking` body with market-specific triggers instead of a single
global one, if strict close-of-that-market timing is required.
"""
import logging
from datetime import datetime, timezone

from sqlalchemy import insert

from app.core.cache import Cache
from app.db.models import WeeklyRanking
from app.db.session import AsyncSessionLocal
from app.services.data_pipeline import refresh_universe
from app.services.ranking import RankableStock, build_weekly_ranking_rows

logger = logging.getLogger("scheduler.jobs")

# In production this comes from the `stocks` table (is_active=True);
# kept as a static list here to keep the skeleton self-contained.
TRACKED_UNIVERSE = [
    "NVDA", "MSFT", "GOOGL", "AMZN", "AVGO", "META", "TSM", "AMD",
    "PTT.BK", "DELTA.BK", "AAPL", "JPM",
]


async def run_weekly_ranking() -> None:
    logger.info("Weekly ranking job started at %s", datetime.now(timezone.utc).isoformat())

    # 1-8: fetch, validate, normalize, indicators, news, sentiment, score
    pipeline_results = await refresh_universe(TRACKED_UNIVERSE)

    # Build RankableStock objects only from tickers that scored successfully —
    # never rank on fabricated/partial data (section 45/46).
    rankable: list[RankableStock] = []
    for result in pipeline_results:
        if result.score is None:
            logger.warning("Skipping %s from ranking: %s", result.ticker, result.errors)
            continue
        # NOTE: price/change/sector/country/etc. would be pulled from the
        # `stocks` + `prices` tables here, joined with `result.score`.
        # Left as a TODO hook — this skeleton focuses on the pipeline shape.

    if not rankable:
        logger.error("No stocks had sufficient data to rank this week — aborting publish.")
        return

    # 9. Rank Global + category-separated Top 10s (section 44)
    rows = build_weekly_ranking_rows(rankable, top_n=10)

    # 10-11. Save to database
    async with AsyncSessionLocal() as session:
        await session.execute(insert(WeeklyRanking), rows)
        await session.commit()

    # Invalidate cached Top-10 responses so the API serves the fresh ranking immediately
    cache = Cache()
    for row in rows:
        await cache.invalidate(f"top_stocks:{row['category']}")

    # 12. Notify users (push/email) — hook up to a notification service here.
    logger.info("Weekly ranking job completed: %d categories published.", len(rows))


async def run_daily_refresh() -> None:
    """Daily job (spec section 30): fundamentals/news/technical — lighter
    than the weekly ranking, does NOT regenerate Top 10."""
    logger.info("Daily refresh started at %s", datetime.now(timezone.utc).isoformat())
    await refresh_universe(TRACKED_UNIVERSE)
    logger.info("Daily refresh completed.")
