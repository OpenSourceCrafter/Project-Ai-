"""
Standalone scheduler process (run via `python -m app.scheduler.scheduler`,
see docker-compose.yml `scheduler` service — kept separate from the API
process so a slow ranking run never blocks HTTP traffic).
"""
import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import get_settings
from app.scheduler.jobs import run_daily_refresh, run_weekly_ranking

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scheduler")

settings = get_settings()


def build_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=settings.weekly_ranking_timezone)

    # Weekly Top 10 — every Friday after markets close (section 43)
    scheduler.add_job(
        run_weekly_ranking,
        trigger=CronTrigger(
            day_of_week=settings.weekly_ranking_cron_day,
            hour=settings.weekly_ranking_cron_hour,
            minute=0,
        ),
        id="weekly_ranking",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    # Daily fundamentals/news/technical refresh (section 30)
    scheduler.add_job(
        run_daily_refresh,
        trigger=CronTrigger(hour=6, minute=0),  # once daily, pre-market
        id="daily_refresh",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    return scheduler


async def main() -> None:
    scheduler = build_scheduler()
    scheduler.start()
    logger.info("Scheduler started. Jobs: %s", [j.id for j in scheduler.get_jobs()])
    try:
        await asyncio.Event().wait()  # run forever
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
