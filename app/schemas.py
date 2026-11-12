from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class LinkCreate(BaseModel):
    url: HttpUrl


class LinkOut(BaseModel):
    code: str
    short_url: str
    target_url: str


class LinkStats(BaseModel):
    code: str
    target_url: str
    clicks: int
    created_at: datetime


class ApiKeyCreate(BaseModel):
    owner: str = Field(min_length=1, max_length=100)


class ApiKeyOut(BaseModel):
    id: int
    owner: str
    key_prefix: str
    api_key: str