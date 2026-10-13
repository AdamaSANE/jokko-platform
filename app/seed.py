"""Peuple une base PostgreSQL JOKKO avec des données de démonstration.

À lancer après ``alembic upgrade head`` avec ``python -m app.seed``.
"""

import asyncio

from sqlalchemy import select

from app.db import SessionLocal
from app.models.domain import (
    Asset,
    AssetKind,
    Conversation,
    ConversationMember,
    DeveloperProfile,
    Exchange,
    ExchangeKind,
    ExchangeSolution,
    ExchangeStatus,
    KarmaEvent,
    Message,
    Notification,
    NotificationType,
    User,
)
from app.services.auth import authentication_service


DEMO_DEVELOPERS = (
    ("adama_dev", "adama@jokko.sn", "Adama SANE", "Sénégal", ["Python", "FastAPI", "Docker", "PostgreSQL"], 45),
    ("awa_fall", "awa@jokko.sn", "Awa Fall", "Côte d'Ivoire", ["JavaScript", "Vue.js", "Tailwind", "FastAPI"], 60),
    ("chinedu_tech", "chinedu@jokko.ng", "Chinedu O.", "Nigeria", ["Python", "PyTorch", "FastAPI"], 80),
)


async def seed_database() -> None:
    async with SessionLocal() as db:
        existing = await db.scalar(select(User.id).where(User.email == DEMO_DEVELOPERS[0][1]))
        if existing is not None:
            print("Base de données déjà alimentée.")
            return

        users: list[User] = []
        for username, email, display_name, country, skills, impact_score in DEMO_DEVELOPERS:
            user = User(
                username=username,
                email=email,
                hashed_password=authentication_service.hash_password("Password123!"),
            )
            user.profile = DeveloperProfile(
                display_name=display_name,
                location=country,
                skills=skills,
                impact_score=impact_score,
            )
            users.append(user)
        db.add_all(users)
        await db.flush()

        exchange = Exchange(
            author_id=users[0].id,
            title="Optimiser SQLAlchemy async avec FastAPI",
            description="Comment éviter le lazy-loading bloquant dans les endpoints async ?",
            language="python",
            kind=ExchangeKind.PROBLEM,
            status=ExchangeStatus.SOLVED,
        )
        db.add(exchange)
        await db.flush()
        solution = ExchangeSolution(
            exchange_id=exchange.id,
            author_id=users[1].id,
            content="Utiliser selectinload et charger explicitement les relations nécessaires.",
            is_accepted=True,
        )
        db.add(solution)
        db.add(KarmaEvent(
            user_id=users[1].id,
            exchange_id=exchange.id,
            points=10,
            reason="Solution de démonstration validée",
        ))
        conversation = Conversation()
        db.add(conversation)
        await db.flush()
        db.add_all([
            ConversationMember(conversation_id=conversation.id, user_id=users[0].id),
            ConversationMember(conversation_id=conversation.id, user_id=users[1].id),
        ])
        for index in range(8):
            db.add(Message(
                conversation_id=conversation.id,
                sender_id=users[index % 2].id,
                recipient_id=users[(index + 1) % 2].id,
                body=f"Message de démonstration #{index + 1}: partageons nos pratiques de développement.",
            ))
        for index in range(9):
            db.add(Notification(
                user_id=users[index % 3].id,
                type=NotificationType.SYSTEM,
                title=f"Notification de démonstration #{index + 1}",
                body="Une nouvelle activité est disponible dans JOKKO.",
            ))
        db.add_all([
            Asset(
                author_id=users[0].id,
                title="Middleware USSD FastAPI",
                description="Base légère pour connecter un service USSD africain.",
                url="https://github.com/jokko-community/fastapi-ussd",
                kind=AssetKind.USSD,
                language="Python",
                license="MIT",
            ),
            Asset(
                author_id=users[2].id,
                title="Docker Compose Mobile Money",
                description="Configuration de démonstration pour un environnement local.",
                url="https://github.com/jokko-community/mobile-money-compose",
                kind=AssetKind.DOCKER,
                language="Docker",
                license="Apache-2.0",
            ),
        ])
        await db.commit()
        print("Seeding JOKKO terminé avec 8 messages et 9 notifications.")


if __name__ == "__main__":
    asyncio.run(seed_database())
