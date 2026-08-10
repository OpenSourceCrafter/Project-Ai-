# AI Smart Stock Analyst — Backend

FastAPI + PostgreSQL + Redis backend skeleton implementing the architecture
described in the product spec (sections 30–49). This is a **structural
skeleton**: the plumbing, interfaces, database schema, scoring formula, and
API contracts are real and internally consistent; a handful of DB-query
"glue" methods are left as documented `# TODO` / `501 not_implemented` stubs
where they depend on your actual populated database rather than on
architecture decisions.

## Architecture

```
alembic/
├── env.py                   # async-aware migration runtime, reads DATABASE_URL from app settings
├── script.py.mako            # template for new migrations
└── versions/
    └── ..._initial_schema.py  # creates all 16 tables + enum types (revision zero)
alembic.ini                  # script_location + logging config (no secrets — see env.py)

app/
├── main.py                 # FastAPI app, CORS, security headers, routers
├── core/
│   ├── config.py            # env-var settings (pydantic-settings)
│   ├── security.py          # JWT + password hashing
│   └── cache.py              # Redis client + cache/rate-limit helpers
├── db/
│   ├── session.py            # async SQLAlchemy engine/session
│   └── models.py             # ORM models — one per table (see below)
├── providers/                # DATA LAYER — pluggable data sources (spec §31)
│   ├── base.py                # abstract interfaces (Market/News/Fundamental/Economic)
│   ├── alpha_vantage.py        # concrete impl: quotes, OHLCV, fundamentals
│   ├── marketaux.py            # concrete impl: ticker-tagged news + sentiment
│   └── registry.py             # env-driven factory — swap providers without touching callers
├── services/                 # SERVICE / AI LAYER
│   ├── scoring.py              # AI Investment Score weighted formula (spec §7/21/24)
│   ├── news_intelligence.py    # topic detection, sentiment, impact scoring (§14-17)
│   ├── ranking.py               # Top 10 ranking + category separation (§20-22/44)
│   └── data_pipeline.py         # orchestrates fetch→validate→score (§30)
├── scheduler/
│   ├── jobs.py                  # weekly ranking + daily refresh job bodies (§43)
│   └── scheduler.py              # APScheduler process entrypoint
├── schemas/
│   └── stock.py                  # Pydantic response models
└── api/v1/                    # API LAYER (spec §42 endpoint map)
    ├── auth.py, stocks.py, top_stocks.py, market.py,
    └── watchlist.py, portfolio.py, alerts.py
```

## Design decisions worth knowing

**Providers are swappable by contract, not by convention.** Everything in
`services/` and `api/` talks to the abstract classes in `providers/base.py`.
`providers/registry.py` resolves `MARKET_DATA_PROVIDER=alpha_vantage` (etc.,
from `.env`) to a concrete class. Adding Polygon or Finnhub later means
writing one new file and registering it — no other code changes.

**Nothing is fabricated.** Every provider call that comes back empty
propagates an explicit `is_available: False` / `None` rather than a guessed
number (spec §45/46). The scoring pipeline skips ranking a stock entirely if
its inputs are incomplete, rather than scoring it on partial/fake data.

**Scoring formula is separate from feature engineering.** `services/scoring.py`
only knows the weights (`Fundamental 25% / Technical 20% / Growth 15% /
Valuation 15% / News 10% / Momentum 5% / Risk 10%`) and how to explain a
result. The actual sub-scores are computed in `data_pipeline.py` — currently
placeholder heuristics clearly marked for replacement with real
XGBoost/LightGBM/ensemble models (spec §33) without touching the weighting
or explanation logic.

**Scheduler runs as its own process**, not inside API request handlers —
see the `scheduler` service in `docker-compose.yml`. A slow weekly ranking
run never blocks user-facing traffic.

## What's stubbed and why

A few endpoints (`GET /api/stocks`, `.../analysis`, portfolio analysis,
alerts creation) return `501 not_implemented` with a comment describing the
exact query/join needed. These all depend on a live, populated
Postgres database — the schema (`db/models.py`) and the shape of the
response (`schemas/stock.py`) are fully defined; only the "select this,
join that" glue was left out since it can't be meaningfully written (or
tested) without real data behind it.

Not implemented at all (flagged as future work per spec §33/34/35):
- Trained ML models (XGBoost/LightGBM/LSTM/Transformer, FinBERT) — the
  `data_pipeline.py` and `news_intelligence.py` placeholders show exactly
  where these plug in.
- Backtesting engine (§34).
- Model performance tracking dashboard (§35) — table (`ModelPerformance`)
  exists; the accuracy-computation job does not.

## Running locally

```bash
cp .env.example .env        # fill in real API keys + a random secret key
docker compose up --build   # starts postgres, redis, api, scheduler
```

Then apply migrations (see **Schema versioning** below):

```bash
alembic upgrade head
```

API docs: `http://localhost:8000/docs` (FastAPI's built-in Swagger UI).

## Schema versioning (Alembic)

Migrations live in `alembic/versions/`. `alembic/env.py` reads `DATABASE_URL`
from the same `app.core.config.get_settings()` the app uses — so `.env` is
the single source of truth; nothing is duplicated into `alembic.ini`.

**Apply all migrations** (fresh database → latest schema):
```bash
alembic upgrade head
```

**After changing a model** in `app/db/models.py`, generate the next migration
automatically by diffing against a running database:
```bash
alembic revision --autogenerate -m "add sector benchmark table"
```
Always read the generated file before committing it — autogenerate is good
at columns/tables/indexes, but it doesn't reliably catch things like renamed
columns (it'll propose drop+add instead) or data migrations.

**Roll back one revision:**
```bash
alembic downgrade -1
```

**Included migration:** `18036708941b_initial_schema.py` creates all 16
tables from spec §39 (users, stocks, prices, fundamentals,
financial_statements, news, sentiments, technical_indicators, ai_scores,
predictions, watchlists, portfolios, alerts, weekly_rankings,
model_performance, market_data) plus the 4 Postgres ENUM types used by the
ORM (`sentiment_enum`, `recommendation_enum`, `risk_level_enum`,
`alert_type_enum`). It was hand-written to match `db/models.py` exactly
(no live database was available to autogenerate from while drafting this
skeleton) — treat it as revision zero and let `--autogenerate` take over
for every change from here on.

## Security checklist (spec §49)

| Requirement            | Where |
|---|---|
| JWT Authentication     | `core/security.py`, `api/v1/auth.py` |
| Password Hashing       | `core/security.py` (bcrypt via passlib) |
| Rate Limiting           | `core/cache.py` + `api/deps.py::rate_limit` (Redis-backed) |
| API Key Encryption      | keys live only in env vars / secret manager — never in code or frontend |
| Input Validation        | Pydantic models on every request body |
| SQL Injection Protection | SQLAlchemy ORM (parameterized queries) — no raw string SQL |
| XSS Protection / CORS   | `main.py` middleware + `CORSMiddleware` |
| HTTPS / Secure Cookies  | terminate TLS at the reverse proxy in front of this service |
