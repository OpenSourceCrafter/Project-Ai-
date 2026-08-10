"""
POST /api/alerts

Smart Alert triggers (spec section 37): price target reached, support break,
RSI extremes, high-impact news, earnings, AI Score change, recommendation
change, risk change. This endpoint registers the alert; the actual trigger
evaluation runs inside the daily/weekly pipeline jobs (compare new AIScore /
TechnicalIndicator rows against each active Alert's threshold) and pushes
via a notification service (email/push) — not shown here.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import rate_limit, require_user
from app.db.models import AlertTypeEnum, User

router = APIRouter(prefix="/api/alerts", tags=["alerts"], dependencies=[Depends(rate_limit)])


class CreateAlertRequest(BaseModel):
    ticker: str
    alert_type: AlertTypeEnum
    threshold: dict | None = None  # e.g. {"price": 150} or {"rsi_below": 30}


@router.post("")
async def create_alert(payload: CreateAlertRequest, user: User = Depends(require_user)):
    return {
        "status": "not_implemented",
        "note": "Look up Stock by ticker, insert an Alert row for user.id, return its id.",
    }
