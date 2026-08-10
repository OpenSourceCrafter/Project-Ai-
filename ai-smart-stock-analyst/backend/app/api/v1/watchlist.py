"""
POST /api/watchlist
GET  /api/watchlist
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, rate_limit, require_user
from app.db.models import Stock, User, Watchlist

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"], dependencies=[Depends(rate_limit)])


class AddWatchlistItem(BaseModel):
    ticker: str


@router.get("")
async def list_watchlist(user: User = Depends(require_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Stock.ticker, Stock.name).join(Watchlist, Watchlist.stock_id == Stock.id)
        .where(Watchlist.user_id == user.id)
    )
    return [{"ticker": t, "name": n} for t, n in result.all()]


@router.post("")
async def add_to_watchlist(
    item: AddWatchlistItem, user: User = Depends(require_user), db: AsyncSession = Depends(get_db)
):
    stock_result = await db.execute(select(Stock).where(Stock.ticker == item.ticker))
    stock = stock_result.scalar_one_or_none()
    if stock is None:
        return {"error": f"Unknown ticker: {item.ticker}"}

    db.add(Watchlist(user_id=user.id, stock_id=stock.id))
    await db.commit()
    return {"status": "added", "ticker": item.ticker}
