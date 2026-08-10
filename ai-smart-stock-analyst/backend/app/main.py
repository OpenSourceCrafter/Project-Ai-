"""
FastAPI app entrypoint.

Architecture (spec section 40): API Layer (this + app/api) / Service Layer
(app/services) / AI Layer (scoring.py, news_intelligence.py, + ML models
plugged into data_pipeline.py) / Data Layer (app/db, app/providers) /
Scheduler (app/scheduler) / Database (PostgreSQL) / Cache (Redis).
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import alerts, auth, market, portfolio, stocks, top_stocks, watchlist
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="AI Smart Stock Analyst API",
    description=(
        "ระบบวิเคราะห์หุ้นอัจฉริยะ — analysis and estimates for informational/"
        "educational purposes only. Not investment advice; no returns are guaranteed."
    ),
    version="0.1.0",
)

# --- CORS (section 49) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list or ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


# --- Security headers (section 49: XSS protection, secure defaults) ---
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # HSTS should be set at the reverse-proxy/load-balancer level in front of
    # this service, where TLS actually terminates.
    return response


# --- Routers (spec section 42 endpoint map) ---
app.include_router(auth.router)
app.include_router(stocks.router)
app.include_router(top_stocks.router)
app.include_router(market.router)
app.include_router(watchlist.router)
app.include_router(portfolio.router)
app.include_router(alerts.router)


@app.get("/healthz", tags=["meta"])
async def health_check():
    return {"status": "ok"}
