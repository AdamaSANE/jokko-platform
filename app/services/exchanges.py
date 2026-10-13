"""Règles métier du hub d'échanges et du score d'impact."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import (
    DeveloperProfile,
    Exchange,
    ExchangeSolution,
    ExchangeStatus,
    KarmaEvent,
    User,
)

SOLUTION_IMPACT_POINTS = 10


class ExchangeService:
    async def create(
        self, db: AsyncSession, author_id: UUID, values: dict[str, object]
    ) -> Exchange:
        exchange = Exchange(author_id=author_id, **values)
        db.add(exchange)
        await db.commit()
        await db.refresh(exchange)
        return exchange

    async def add_solution(
        self, db: AsyncSession, exchange_id: UUID, author_id: UUID, content: str
    ) -> ExchangeSolution:
        exchange = await db.get(Exchange, exchange_id)
        if exchange is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Échange introuvable")
        if exchange.author_id == author_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="L'auteur ne peut pas proposer sa propre solution",
            )
        solution = ExchangeSolution(exchange_id=exchange_id, author_id=author_id, content=content)
        db.add(solution)
        await db.commit()
        await db.refresh(solution)
        return solution

    async def solve(
        self, db: AsyncSession, exchange_id: UUID, solution_id: UUID, validator_id: UUID
    ) -> ExchangeSolution:
        exchange = await db.get(Exchange, exchange_id)
        solution = await db.get(ExchangeSolution, solution_id)
        if exchange is None or solution is None or solution.exchange_id != exchange_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solution introuvable")
        if exchange.author_id != validator_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seul l'auteur peut valider une solution",
            )
        if exchange.status == ExchangeStatus.SOLVED:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Échange déjà résolu")

        solution.is_accepted = True
        exchange.status = ExchangeStatus.SOLVED
        helper = await db.get(User, solution.author_id)
        if helper is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contributeur introuvable")
        profile = await db.scalar(select(DeveloperProfile).where(DeveloperProfile.user_id == helper.id))
        if profile is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Profil contributeur introuvable")
        profile.impact_score += SOLUTION_IMPACT_POINTS
        db.add(KarmaEvent(
            user_id=helper.id,
            exchange_id=exchange.id,
            points=SOLUTION_IMPACT_POINTS,
            reason="Solution validée par l'auteur",
        ))
        await db.commit()
        await db.refresh(solution)
        return solution


exchange_service = ExchangeService()
