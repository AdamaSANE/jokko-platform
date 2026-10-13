"""Contrats HTTP de la marketplace de composants."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl

from app.models.domain import AssetKind


class AssetCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=1, max_length=10000)
    url: HttpUrl
    kind: AssetKind
    language: str | None = Field(default=None, max_length=50)
    license: str = Field(default="MIT", min_length=1, max_length=80)


class AssetResponse(BaseModel):
    id: UUID
    author_id: UUID
    title: str
    description: str
    url: str
    kind: AssetKind
    language: str | None
    license: str
    download_count: int
    created_at: datetime

    class Config:
        from_attributes = True
