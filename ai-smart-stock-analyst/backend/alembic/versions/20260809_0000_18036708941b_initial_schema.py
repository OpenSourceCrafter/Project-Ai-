"""initial schema — all tables from spec section 39

Revision ID: 18036708941b
Revises:
Create Date: 2026-08-09 00:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "18036708941b"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---------- users ----------
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(100), nullable=True),
        sa.Column("subscription_tier", sa.String(20), nullable=False, server_default="FREE"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ---------- stocks ----------
    op.create_table(
        "stocks",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("country", sa.String(4), nullable=False),
        sa.Column("exchange", sa.String(20), nullable=False),
        sa.Column("sector", sa.String(50), nullable=False),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column("currency", sa.String(6), nullable=False, server_default="USD"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_stocks_ticker", "stocks", ["ticker"], unique=True)

    # ---------- prices ----------
    op.create_table(
        "prices",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("stock_id", sa.BigInteger(),
                  sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("interval", sa.String(10), nullable=False, server_default="1d"),
        sa.Column("open", sa.Numeric(18, 4), nullable=False),
        sa.Column("high", sa.Numeric(18, 4), nullable=False),
        sa.Column("low", sa.Numeric(18, 4), nullable=False),
        sa.Column("close", sa.Numeric(18, 4), nullable=False),
        sa.Column("volume", sa.BigInteger(), nullable=False),
        sa.Column("source", sa.String(50), nullable=False),
        sa.UniqueConstraint("stock_id", "timestamp", "interval", name="uq_price_bar"),
    )
    op.create_index("ix_prices_stock_id", "prices", ["stock_id"])
    op.create_index("ix_prices_timestamp", "prices", ["timestamp"])

    # ---------- fundamentals ----------
    op.create_table(
        "fundamentals",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("stock_id", sa.BigInteger(),
                  sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revenue", sa.Numeric(20, 2), nullable=True),
        sa.Column("revenue_growth", sa.Float(), nullable=True),
        sa.Column("eps", sa.Numeric(10, 4), nullable=True),
        sa.Column("eps_growth", sa.Float(), nullable=True),
        sa.Column("gross_margin", sa.Float(), nullable=True),
        sa.Column("operating_margin", sa.Float(), nullable=True),
        sa.Column("net_margin", sa.Float(), nullable=True),
        sa.Column("roe", sa.Float(), nullable=True),
        sa.Column("roa", sa.Float(), nullable=True),
        sa.Column("debt_to_equity", sa.Float(), nullable=True),
        sa.Column("free_cash_flow", sa.Numeric(20, 2), nullable=True),
        sa.Column("cash", sa.Numeric(20, 2), nullable=True),
        sa.Column("total_debt", sa.Numeric(20, 2), nullable=True),
        sa.Column("pe", sa.Float(), nullable=True),
        sa.Column("forward_pe", sa.Float(), nullable=True),
        sa.Column("peg", sa.Float(), nullable=True),
        sa.Column("pb", sa.Float(), nullable=True),
        sa.Column("ps", sa.Float(), nullable=True),
        sa.Column("ev_ebitda", sa.Float(), nullable=True),
        sa.Column("dividend_yield", sa.Float(), nullable=True),
        sa.Column("source", sa.String(50), nullable=False),
    )
    op.create_index("ix_fundamentals_stock_id", "fundamentals", ["stock_id"])
    op.create_index("ix_fundamentals_as_of", "fundamentals", ["as_of"])

    # ---------- financial_statements ----------
    op.create_table(
        "financial_statements",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("stock_id", sa.BigInteger(),
                  sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("period", sa.String(10), nullable=False),
        sa.Column("statement_type", sa.String(20), nullable=False),
        sa.Column("line_items", sa.JSON(), nullable=False),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("filed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_financial_statements_stock_id", "financial_statements", ["stock_id"])

    # ---------- news ----------
    op.create_table(
        "news",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("external_id", sa.String(255), nullable=False),
        sa.Column("headline", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("language", sa.String(8), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tickers", sa.JSON(), nullable=False),
        sa.Column("topics", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("is_high_impact", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_news_external_id", "news", ["external_id"], unique=True)
    op.create_index("ix_news_published_at", "news", ["published_at"])

    # ---------- sentiments (depends on: news, stocks) ----------
    op.create_table(
        "sentiments",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("news_id", sa.BigInteger(),
                  sa.ForeignKey("news.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stock_id", sa.BigInteger(),
                  sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "sentiment",
            sa.Enum("POSITIVE", "NEUTRAL", "NEGATIVE", name="sentiment_enum"),
            nullable=False,
        ),
        sa.Column("sentiment_score", sa.Float(), nullable=False),
        sa.Column("impact_score", sa.Integer(), nullable=False),
        sa.Column("model_name", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_sentiments_stock_id", "sentiments", ["stock_id"])

    # ---------- technical_indicators ----------
    op.create_table(
        "technical_indicators",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("stock_id", sa.BigInteger(),
                  sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ma20", sa.Float(), nullable=True),
        sa.Column("ma50", sa.Float(), nullable=True),
        sa.Column("ma100", sa.Float(), nullable=True),
        sa.Column("ma200", sa.Float(), nullable=True),
        sa.Column("ema", sa.Float(), nullable=True),
        sa.Column("rsi", sa.Float(), nullable=True),
        sa.Column("macd", sa.Float(), nullable=True),
        sa.Column("macd_signal", sa.Float(), nullable=True),
        sa.Column("bollinger_upper", sa.Float(), nullable=True),
        sa.Column("bollinger_lower", sa.Float(), nullable=True),
        sa.Column("support", sa.Float(), nullable=True),
        sa.Column("resistance", sa.Float(), nullable=True),
        sa.UniqueConstraint("stock_id", "as_of", name="uq_indicator_day"),
    )
    op.create_index("ix_technical_indicators_stock_id", "technical_indicators", ["stock_id"])
    op.create_index("ix_technical_indicators_as_of", "technical_indicators", ["as_of"])

    # ---------- ai_scores ----------
    op.create_table(
        "ai_scores",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("stock_id", sa.BigInteger(),
                  sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fundamental_score", sa.Float(), nullable=False),
        sa.Column("technical_score", sa.Float(), nullable=False),
        sa.Column("growth_score", sa.Float(), nullable=False),
        sa.Column("valuation_score", sa.Float(), nullable=False),
        sa.Column("news_score", sa.Float(), nullable=False),
        sa.Column("momentum_score", sa.Float(), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("final_score", sa.Float(), nullable=False),
        sa.Column(
            "recommendation",
            sa.Enum("STRONG_BUY", "BUY", "ACCUMULATE", "HOLD", "WATCH", "REDUCE", "SELL",
                    name="recommendation_enum"),
            nullable=False,
        ),
        sa.Column(
            "risk_level",
            sa.Enum("LOW", "MEDIUM", "HIGH", "VERY_HIGH", name="risk_level_enum"),
            nullable=False,
        ),
        sa.Column("explanation", sa.JSON(), nullable=False),
    )
    op.create_index("ix_ai_scores_stock_id", "ai_scores", ["stock_id"])
    op.create_index("ix_ai_scores_as_of", "ai_scores", ["as_of"])

    # ---------- predictions ----------
    op.create_table(
        "predictions",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("stock_id", sa.BigInteger(),
                  sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("horizon", sa.String(10), nullable=False),
        sa.Column("range_low", sa.Numeric(18, 4), nullable=False),
        sa.Column("range_high", sa.Numeric(18, 4), nullable=False),
        sa.Column("confidence", sa.Integer(), nullable=False),
        sa.Column("confidence_factors", sa.JSON(), nullable=False),
        sa.Column("model_version", sa.String(50), nullable=False),
    )
    op.create_index("ix_predictions_stock_id", "predictions", ["stock_id"])
    op.create_index("ix_predictions_generated_at", "predictions", ["generated_at"])

    # ---------- watchlists (depends on: users, stocks) ----------
    op.create_table(
        "watchlists",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("user_id", sa.BigInteger(),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stock_id", sa.BigInteger(),
                  sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("added_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "stock_id", name="uq_watchlist_stock"),
    )
    op.create_index("ix_watchlists_user_id", "watchlists", ["user_id"])
    op.create_index("ix_watchlists_stock_id", "watchlists", ["stock_id"])

    # ---------- portfolios (depends on: users) ----------
    op.create_table(
        "portfolios",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("user_id", sa.BigInteger(),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False, server_default="My Portfolio"),
        sa.Column("cash_thb", sa.Numeric(20, 2), nullable=False, server_default="0"),
        sa.Column("holdings", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_portfolios_user_id", "portfolios", ["user_id"])

    # ---------- alerts (depends on: users, stocks) ----------
    op.create_table(
        "alerts",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("user_id", sa.BigInteger(),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stock_id", sa.BigInteger(),
                  sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "alert_type",
            sa.Enum(
                "PRICE_TARGET", "SUPPORT_BREAK", "RSI_LOW", "RSI_HIGH", "NEWS_HIGH_IMPACT",
                "EARNINGS", "AI_SCORE_CHANGE", "RECOMMENDATION_CHANGE", "RISK_CHANGE",
                name="alert_type_enum",
            ),
            nullable=False,
        ),
        sa.Column("threshold", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_triggered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_alerts_user_id", "alerts", ["user_id"])
    op.create_index("ix_alerts_stock_id", "alerts", ["stock_id"])

    # ---------- weekly_rankings ----------
    op.create_table(
        "weekly_rankings",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("week_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rankings", sa.JSON(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("category", "week_of", name="uq_ranking_week"),
    )
    op.create_index("ix_weekly_rankings_category", "weekly_rankings", ["category"])
    op.create_index("ix_weekly_rankings_week_of", "weekly_rankings", ["week_of"])

    # ---------- model_performance ----------
    op.create_table(
        "model_performance",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("horizon", sa.String(10), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("directional_accuracy", sa.Float(), nullable=False),
        sa.Column("precision", sa.Float(), nullable=False),
        sa.Column("recall", sa.Float(), nullable=False),
        sa.Column("f1_score", sa.Float(), nullable=False),
        sa.Column("mae", sa.Float(), nullable=False),
        sa.Column("rmse", sa.Float(), nullable=False),
        sa.Column("sample_size", sa.Integer(), nullable=False),
    )
    op.create_index("ix_model_performance_evaluated_at", "model_performance", ["evaluated_at"])

    # ---------- market_data ----------
    op.create_table(
        "market_data",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("symbol", sa.String(30), nullable=False),
        sa.Column("category", sa.String(20), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("value", sa.Numeric(20, 6), nullable=False),
        sa.Column("change_pct", sa.Float(), nullable=True),
        sa.Column("source", sa.String(50), nullable=False),
        sa.UniqueConstraint("symbol", "timestamp", name="uq_market_data_point"),
    )
    op.create_index("ix_market_data_symbol", "market_data", ["symbol"])
    op.create_index("ix_market_data_timestamp", "market_data", ["timestamp"])


def downgrade() -> None:
    # Drop in reverse dependency order so FKs never block a table drop.
    op.drop_table("market_data")
    op.drop_table("model_performance")
    op.drop_table("weekly_rankings")
    op.drop_table("alerts")
    op.drop_table("portfolios")
    op.drop_table("watchlists")
    op.drop_table("predictions")
    op.drop_table("ai_scores")
    op.drop_table("technical_indicators")
    op.drop_table("sentiments")
    op.drop_table("news")
    op.drop_table("financial_statements")
    op.drop_table("fundamentals")
    op.drop_table("prices")
    op.drop_table("stocks")
    op.drop_table("users")

    # Postgres ENUM types aren't dropped automatically with their columns —
    # remove them explicitly so `downgrade` fully reverses `upgrade`.
    bind = op.get_bind()
    for enum_name in ("alert_type_enum", "risk_level_enum", "recommendation_enum", "sentiment_enum"):
        sa.Enum(name=enum_name).drop(bind, checkfirst=True)
