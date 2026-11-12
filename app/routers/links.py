import secrets
import string

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.guard import check_key_quota
from app.models import ApiKey, Link
from app.safebrowsing import UrlChecker, get_url_checker
from app.schemas import LinkCreate, LinkOut, LinkStats
from app.security import require_api_key

ALPHABET = string.ascii_letters + string.digits

api = APIRouter(prefix="/api/v1/links", tags=["links"])
public = APIRouter(tags=["redirect"])


def _new_code() -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(7))


def _short_url(code: str) -> str:
    return f"{get_settings().base_url.rstrip('/')}/{code}"


@api.post("", response_model=LinkOut, status_code=status.HTTP_201_CREATED)
def create_link(
    payload: LinkCreate,
    api_key: ApiKey = Depends(require_api_key),
    db: Session = Depends(get_db),
    checker: UrlChecker = Depends(get_url_checker),
):
    check_key_quota(api_key.id)

    url = str(payload.url)
    if not checker.is_safe(url):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "URL flagged as unsafe by Safe Browsing")

    for _ in range(5):
        link = Link(code=_new_code(), target_url=url, api_key_id=api_key.id)
        db.add(link)
        try:
            db.commit()
            break
        except IntegrityError:
            db.rollback()
    else:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Could not allocate a short code")

    return LinkOut(code=link.code, short_url=_short_url(link.code), target_url=link.target_url)


@api.get("/{code}/stats", response_model=LinkStats)
def link_stats(code: str, api_key: ApiKey = Depends(require_api_key), db: Session = Depends(get_db)):
    link = db.scalar(select(Link).where(Link.code == code))
    if link is None or link.api_key_id != api_key.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Link not found")
    return LinkStats(code=link.code, target_url=link.target_url, clicks=link.clicks, created_at=link.created_at)


@public.get("/{code}", include_in_schema=False)
def redirect(code: str, db: Session = Depends(get_db)):
    target = db.scalar(select(Link.target_url).where(Link.code == code))
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Link not found")
    db.execute(update(Link).where(Link.code == code).values(clicks=Link.clicks + 1))
    db.commit()
    return RedirectResponse(target, status_code=status.HTTP_307_TEMPORARY_REDIRECT)