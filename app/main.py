from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import models  
from app.db import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="LinkGuard", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}