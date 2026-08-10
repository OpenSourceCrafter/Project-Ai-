"""
Marketaux implementation of NewsProvider — chosen because it provides
ticker-tagged news with baseline sentiment out of the box (spec section 31).
Our own NLP layer (news_intelligence.py) re-scores impact/importance on top.
"""
from datetime import datetime

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.providers.base import NewsItem, NewsProvider

BASE_URL = "https://api.marketaux.com/v1/news/all"


class MarketauxProvider(NewsProvider):
    def __init__(self, api_key: str | None = None):
        settings = get_settings()
        self.api_key = api_key or settings.news_api_key
        self._client = httpx.AsyncClient(timeout=15.0)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    async def get_news(
        self, tickers: list[str] | None = None, languages: list[str] | None = None, limit: int = 50
    ) -> list[NewsItem]:
        params = {
            "api_token": self.api_key,
            "limit": min(limit, 100),
        }
        if tickers:
            params["symbols"] = ",".join(tickers)
        if languages:
            params["language"] = ",".join(languages)  # e.g. th, en, ja, zh, ko, de

        resp = await self._client.get(BASE_URL, params=params)
        resp.raise_for_status()
        payload = resp.json()

        items: list[NewsItem] = []
        for article in payload.get("data", []):
            tagged_tickers = [e["symbol"] for e in article.get("entities", []) if e.get("symbol")]
            items.append(NewsItem(
                external_id=article["uuid"],
                headline=article["title"],
                summary=article.get("description"),
                url=article["url"],
                source=article.get("source", "unknown"),
                language=article.get("language", "en"),
                published_at=datetime.fromisoformat(article["published_at"].replace("Z", "+00:00")),
                tickers=tagged_tickers,
            ))
        return items
