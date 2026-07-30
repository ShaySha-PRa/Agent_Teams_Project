"""JWT authentication — stub implementation for MVP.

In production, replace with a real identity provider (Auth0, Keycloak, etc.)
or an application-managed user table.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Depends, Header, HTTPException, Request, status
from jose import JWTError, jwt
from pydantic import BaseModel

from core.config import get_settings

_settings = get_settings()


class TokenPayload(BaseModel):
    """Claims carried inside the JWT."""

    sub: str  # user_id
    exp: datetime | None = None
    iat: datetime | None = None
    jti: str | None = None


class CurrentUser(BaseModel):
    """Minimal user model injected into request handlers."""

    user_id: str
    name: str = "anonymous"


# ── Token helpers ──────────────────────────────────────────────────────


def create_access_token(user_id: str) -> str:
    """Create a signed JWT for the given user_id."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(minutes=_settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, _settings.jwt_secret_key, algorithm=_settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> TokenPayload:
    """Decode and validate a JWT; raises HTTPException on failure."""
    try:
        claims = jwt.decode(
            token,
            _settings.jwt_secret_key,
            algorithms=[_settings.JWT_ALGORITHM],
        )
        return TokenPayload(**claims)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


# ── FastAPI dependency ─────────────────────────────────────────────────


async def get_current_user(
    request: Request,
    authorization: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> CurrentUser:
    """Resolve the current user from the Authorization header (JWT) or
    fall back to the X-User-Id header (MVP convenience).

    This dependency is used on every authenticated route.
    """
    # ── MVP shortcut: dev-token or X-User-Id header ──
    if authorization and (authorization == "Bearer dev-token" or authorization == "dev-token"):
        return CurrentUser(user_id="dev-user", name="dev-user")

    if authorization is None and x_user_id:
        return CurrentUser(user_id=x_user_id, name=x_user_id)

    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
        )

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token required",
        )

    payload = decode_access_token(token)
    return CurrentUser(user_id=payload.sub)
