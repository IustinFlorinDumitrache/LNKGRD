import hashlib
import hmac
import secrets

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models import ApiKey


def generate_api_key() -> str:
    return "lg_" + secrets.token_urlsafe(32)


def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def require_api_key(
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> ApiKey:
    if not x_api_key:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing X-API-Key header")
    api_key = db.scalar(select(ApiKey).where(ApiKey.key_hash == hash_key(x_api_key)))
    if api_key is None or not api_key.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid API key")
    return api_key


def require_admin(x_admin_token: str | None = Header(default=None)) -> None:
    expected = get_settings().admin_token
    if not expected:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "ADMIN_TOKEN not set")
    if not x_admin_token or not hmac.compare_digest(x_admin_token, expected):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Invalid admin token")