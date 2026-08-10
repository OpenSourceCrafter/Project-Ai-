"""
POST /api/portfolio
GET  /api/portfolio

Implements the AI Portfolio (section 26) and Portfolio Optimization (section 27)
contracts. The optimizer itself is a modeling concern (mean-variance / risk-parity
over the tracked universe's AI Scores + covariance) — stubbed here with a
documented interface so it's obvious where to plug in the real allocator.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import rate_limit, require_user
from app.db.models import User

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"], dependencies=[Depends(rate_limit)])

OPTIMIZATION_DISCLAIMER = (
    "ตัวอย่างการจัดสรรพอร์ตเพื่อการวิเคราะห์ ไม่ใช่คำแนะนำทางการเงินเฉพาะบุคคล"
)


class PortfolioRequest(BaseModel):
    cash_thb: float
    tickers: list[str]


@router.post("")
async def analyze_portfolio(payload: PortfolioRequest, user: User = Depends(require_user)):
    """
    Returns Expected Return Range / Risk / Diversification / Sector Exposure /
    Country Exposure / Portfolio Score (section 26). Requires per-ticker
    AIScore + sector/country lookups plus a covariance/correlation model for
    the risk & diversification figures — wire up once those services exist.
    """
    return {
        "status": "not_implemented",
        "note": (
            "Pull latest AIScore + sector/country for each ticker in payload.tickers, "
            "compute weighted expected-return range and a diversification/HHI score, "
            "then return the PortfolioAnalysis shape."
        ),
    }


@router.post("/optimize")
async def optimize_portfolio(payload: PortfolioRequest, user: User = Depends(require_user)):
    """Suggests an allocation (section 27). Must always include the disclaimer."""
    return {
        "status": "not_implemented",
        "disclaimer": OPTIMIZATION_DISCLAIMER,
        "note": "Plug in a mean-variance or risk-parity optimizer over AIScore-weighted expected returns.",
    }


@router.get("")
async def get_portfolios(user: User = Depends(require_user)):
    return {"status": "not_implemented", "note": "Query Portfolio table filtered by user_id."}
