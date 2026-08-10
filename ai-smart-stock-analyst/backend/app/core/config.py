"""
Centralized settings. Everything is read from environment variables
(via .env in development) — no secrets are ever hard-coded here.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- App ---
    app_env: str = "development"
    app_secret_key: str
    app_cors_origins: str = ""

    # --- Database ---
    database_url: str

    # --- Cache ---
    redis_url: str

    # --- Auth ---
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 14

    # --- Data providers (names only — keys are injected per-provider) ---
    market_data_provider: str = "alpha_vantage"
    market_data_api_key: str = ""

    news_provider: str = "marketaux"
    news_api_key: str = ""

    fundamental_provider: str = "alpha_vantage"
    fundamental_api_key: str = ""

    economic_data_provider: str = "alpha_vantage"
    economic_data_api_key: str = ""

    # --- AI ---
    ai_api_key: str = ""
    ai_model: str = "claude-sonnet-4-6"

    # --- Rate limiting ---
    rate_limit_per_minute: int = 60

    # --- Scheduler ---
    weekly_ranking_cron_day: str = "fri"
    weekly_ranking_cron_hour: int = 17
    weekly_ranking_timezone: str = "America/New_York"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.app_cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    # lru_cache means .env is read once per process
    return Settings()
