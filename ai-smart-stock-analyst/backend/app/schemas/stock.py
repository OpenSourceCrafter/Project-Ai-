from datetime import datetime

from pydantic import BaseModel


class DataMeta(BaseModel):
    """Attached to every response carrying market/financial data — spec section 45:
    every important data point must show Data Updated + Data Source."""
    data_updated: datetime | None
    data_source: str
    is_available: bool = True


class QuoteResponse(BaseModel):
    ticker: str
    price: float | None
    change_pct: float | None
    meta: DataMeta


class AIScoreResponse(BaseModel):
    fundamental: float
    technical: float
    growth: float
    valuation: float
    news: float
    momentum: float
    risk: float
    final_score: float
    recommendation: str
    risk_level: str
    explanation: dict
    meta: DataMeta


class ForecastRange(BaseModel):
    horizon: str
    range_low: float
    range_high: float
    confidence: int
    confidence_factors: dict


class StockAnalysisResponse(BaseModel):
    ticker: str
    name: str
    country: str
    sector: str
    quote: QuoteResponse
    ai_score: AIScoreResponse
    support: float | None
    resistance: float | None
    ai_estimated_range: tuple[float, float] | None
    forecasts: list[ForecastRange]


class TopStockCard(BaseModel):
    rank: int
    ticker: str
    company: str
    country: str
    sector: str
    current_price: float
    week_change_pct: float
    month_change_pct: float
    year_change_pct: float
    ai_score: float
    risk: str
    news_sentiment: str
    potential_return: str
    recommendation: str


class TopStocksResponse(BaseModel):
    category: str
    week_of: datetime
    stocks: list[TopStockCard]
    disclaimer: str = (
        "การวิเคราะห์และประมาณการนี้จัดทำเพื่อการศึกษาเท่านั้น ไม่ใช่คำแนะนำการลงทุน "
        "และไม่รับประกันผลตอบแทนหรือผลกำไร"
    )
