"""
Shared FastAPI dependencies: DB session, current-user auth, Redis rate limiting.
"""
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import Cache
from app.core.config import get_settings
from app.core.security import decode_token
from app.db.models import User
from app.db.session import get_db

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Returns None for anonymous access — routes that require auth should
    use `require_user` instead. Free-tier browsing works without a token."""
    if not token:
        return None
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        return None
    result = await db.execute(select(User).where(User.id == int(payload["sub"])))
    return result.scalar_one_or_none()


async def require_user(user: User | None = Depends(get_current_user)) -> User:
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentication required")
    return user


async def rate_limit(request: Request) -> None:
    """Simple Redis-backed rate limiter — keyed by client IP (or user id if
    authenticated, via request.state set upstream by auth middleware)."""
    identifier = request.client.host if request.client else "unknown"
    cache = Cache()
    if await cache.rate_limit_hit(identifier, settings.rate_limit_per_minute, window_seconds=60):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Rate limit exceeded")
