from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import models  # noqa: F401
from app.db import Base, engine
from app.guard import GuardMiddleware
from app.redis_client import get_redis
from app.routers import admin, links


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="LinkGuard", lifespan=lifespan)
app.add_middleware(GuardMiddleware)


@app.get("/health")
def health():
    try:
        redis_ok = bool(get_redis().ping())
    except Exception:
        redis_ok = False
    return {"status": "ok" if redis_ok else "degraded", "redis": redis_ok}


app.include_router(admin.router)
app.include_router(links.api)
app.include_router(links.public)  