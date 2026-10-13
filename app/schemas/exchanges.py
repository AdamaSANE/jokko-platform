"""Contrats HTTP du hub d'échanges et de la réputation."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.domain import ExchangeKind, ExchangeStatus


class ExchangeCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=1, max_length=20000)
    code: str | None = Field(default=None, max_length=50000)
    language: str | None = Field(default=None, max_length=50)
    kind: ExchangeKind = ExchangeKind.PROBLEM


class ExchangeSolutionCreate(BaseModel):
    content: str = Field(min_length=1, max_length=20000)


class ExchangeSolveRequest(BaseModel):
    solution_id: UUID


class ExchangeResponse(BaseModel):
    id: UUID
    author_id: UUID
    title: str
    description: str
    code: str | None
    language: str | None
    kind: ExchangeKind
    status: ExchangeStatus
    created_at: datetime

    class Config:
        from_attributes = True


class SolutionResponse(BaseModel):
    id: UUID
    exchange_id: UUID
    author_id: UUID
    content: str
    is_accepted: bool
    created_at: datetime

    class Config:
        from_attributes = True


class LeaderboardEntry(BaseModel):
    user_id: UUID
    username: str
    display_name: str
    country: str | None
    impact_score: int


class PortfolioResponse(LeaderboardEntry):
    skills: list[str]
    solved_exchanges: int
