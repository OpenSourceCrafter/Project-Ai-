"""
Factory that resolves the *interface* the rest of the app depends on
(MarketDataProvider, NewsProvider, FundamentalProvider, EconomicDataProvider)
to a concrete implementation chosen via environment variables.

To add a new vendor: implement the relevant interface in this package,
then register it in the maps below. No other code needs to change —
this is the whole point of the interface split in spec section 31.
"""
from functools import lru_cache

from app.core.config import get_settings
from app.providers.alpha_vantage import AlphaVantageProvider
from app.providers.base import (
    EconomicDataProvider, FundamentalProvider, MarketDataProvider, NewsProvider,
)
from app.providers.marketaux import MarketauxProvider

_MARKET_DATA_PROVIDERS = {
    "alpha_vantage": AlphaVantageProvider,
    # "polygon": PolygonProvider,        # add when implemented
    # "finnhub": FinnhubProvider,
    # "twelve_data": TwelveDataProvider,
}

_FUNDAMENTAL_PROVIDERS = {
    "alpha_vantage": AlphaVantageProvider,
    # "financial_modeling_prep": FMPProvider,
}

_NEWS_PROVIDERS = {
    "marketaux": MarketauxProvider,
    # "finnhub_news": FinnhubNewsProvider,
}

_ECONOMIC_PROVIDERS = {
    "alpha_vantage": AlphaVantageProvider,  # supports FEDERAL_FUNDS_RATE, CPI, etc.
}


@lru_cache
def get_market_data_provider() -> MarketDataProvider:
    settings = get_settings()
    cls = _MARKET_DATA_PROVIDERS.get(settings.market_data_provider)
    if not cls:
        raise ValueError(f"Unknown MARKET_DATA_PROVIDER: {settings.market_data_provider}")
    return cls(api_key=settings.market_data_api_key)


@lru_cache
def get_fundamental_provider() -> FundamentalProvider:
    settings = get_settings()
    cls = _FUNDAMENTAL_PROVIDERS.get(settings.fundamental_provider)
    if not cls:
        raise ValueError(f"Unknown FUNDAMENTAL_PROVIDER: {settings.fundamental_provider}")
    return cls(api_key=settings.fundamental_api_key)


@lru_cache
def get_news_provider() -> NewsProvider:
    settings = get_settings()
    cls = _NEWS_PROVIDERS.get(settings.news_provider)
    if not cls:
        raise ValueError(f"Unknown NEWS_PROVIDER: {settings.news_provider}")
    return cls(api_key=settings.news_api_key)


@lru_cache
def get_economic_data_provider() -> EconomicDataProvider:
    settings = get_settings()
    cls = _ECONOMIC_PROVIDERS.get(settings.economic_data_provider)
    if not cls:
        raise ValueError(f"Unknown ECONOMIC_DATA_PROVIDER: {settings.economic_data_provider}")
    return cls(api_key=settings.economic_data_api_key)
