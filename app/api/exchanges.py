"""API publique de démonstration du hub d'échanges entre développeurs."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.domain import DeveloperProfile, Exchange, ExchangeSolution, User
from app.schemas.exchanges import (
    ExchangeCreate,
    ExchangeResponse,
    ExchangeSolveRequest,
    ExchangeSolutionCreate,
    LeaderboardEntry,
    PortfolioResponse,
    SolutionResponse,
)
from app.security import get_current_user
from app.services.exchanges import exchange_service

router = APIRouter(prefix="/api/v1", tags=["exchanges"])


@router.post("/exchanges/", response_model=ExchangeResponse, status_code=status.HTTP_201_CREATED)
async def create_exchange(
    payload: ExchangeCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Exchange:
    return await exchange_service.create(db, user.id, payload.model_dump())


@router.get("/exchanges/", response_model=list[ExchangeResponse])
async def list_exchanges(
    offset: int = Query(default=0, ge=0, le=100_000),
    limit: int = Query(default=20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[Exchange]:
    result = await db.scalars(
        select(Exchange).order_by(Exchange.created_at.desc()).offset(offset).limit(limit)
    )
    return list(result)


@router.post(
    "/exchanges/{exchange_id}/solutions",
    response_model=SolutionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def propose_solution(
    exchange_id: UUID,
    payload: ExchangeSolutionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExchangeSolution:
    return await exchange_service.add_solution(db, exchange_id, user.id, payload.content)


@router.get("/exchanges/{exchange_id}/solutions", response_model=list[SolutionResponse])
async def list_solutions(
    exchange_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[ExchangeSolution]:
    result = await db.scalars(
        select(ExchangeSolution)
        .where(ExchangeSolution.exchange_id == exchange_id)
        .order_by(ExchangeSolution.created_at.asc())
    )
    return list(result)


@router.put("/exchanges/{exchange_id}/solve", response_model=SolutionResponse)
async def solve_exchange(
    exchange_id: UUID,
    payload: ExchangeSolveRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExchangeSolution:
    return await exchange_service.solve(db, exchange_id, payload.solution_id, user.id)


@router.get("/devs/leaderboard", response_model=list[LeaderboardEntry])
async def leaderboard(
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[LeaderboardEntry]:
    rows = await db.execute(
        select(User, DeveloperProfile)
        .join(DeveloperProfile, DeveloperProfile.user_id == User.id)
        .where(User.is_active.is_(True))
        .order_by(DeveloperProfile.impact_score.desc(), User.username)
        .limit(limit)
    )
    return [
        LeaderboardEntry(
            user_id=user.id,
            username=user.username,
            display_name=profile.display_name,
            country=profile.location,
            impact_score=profile.impact_score,
        )
        for user, profile in rows.all()
    ]


@router.get("/devs/portfolio/{user_id}", response_model=PortfolioResponse)
async def portfolio(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PortfolioResponse:
    row = await db.execute(
        select(User, DeveloperProfile)
        .join(DeveloperProfile, DeveloperProfile.user_id == User.id)
        .where(User.id == user_id, User.is_active.is_(True))
    )
    user_and_profile = row.one_or_none()
    if user_and_profile is None:
        raise HTTPException(status_code=404, detail="Développeur introuvable")
    user, profile = user_and_profile
    solved_exchanges = await db.scalar(
        select(func.count())
        .select_from(ExchangeSolution)
        .join(Exchange, Exchange.id == ExchangeSolution.exchange_id)
        .where(ExchangeSolution.author_id == user_id, ExchangeSolution.is_accepted.is_(True))
    )
    return PortfolioResponse(
        user_id=user.id,
        username=user.username,
        display_name=profile.display_name,
        country=profile.location,
        impact_score=profile.impact_score,
        skills=profile.skills or [],
        solved_exchanges=solved_exchanges or 0,
    )
