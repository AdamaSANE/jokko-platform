# Auteur : Adama SANE - Développeur autodidacte en apprentissage continu, sans parcours académique technologique classique | GitHub : [https://github.com/AdamaSANE](https://github.com/AdamaSANE)
"""Création de l'engine asynchrone et de la fabrique de sessions."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings


def _async_database_url(database_url: str) -> str:
    """Use asyncpg when Neon provides a standard PostgreSQL URL."""
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    database_url = database_url.replace("sslmode=require", "ssl=require")
    return database_url.replace("&channel_binding=require", "")


engine = create_async_engine(_async_database_url(settings.database_url), pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Fournit une session isolée à une requête puis la ferme proprement."""
    async with SessionLocal() as session:
        yield session
