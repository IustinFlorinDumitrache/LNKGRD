from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import models  # noqa: F401
from app.db import Base, engine
from app.routers import admin, links


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="LinkGuard", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(admin.router)
app.include_router(links.api)
app.include_router(links.public)  