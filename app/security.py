# Auteur : Adama SANE - Développeur autodidacte en apprentissage continu, sans parcours académique technologique classique | GitHub : [https://github.com/AdamaSANE](https://github.com/AdamaSANE)
"""Dépendances de sécurité partagées par tous les endpoints privés."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.db import get_db
from app.models.domain import Session, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Refuse toute requête sans JWT valide et sans session non révoquée.

    La vérification de la session en base est volontaire : elle permet à la
    déconnexion de prendre effet immédiatement, contrairement à un JWT autonome.
    """
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentification requise",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        subject = payload.get("sub")
        jti = payload.get("jti")
        if not subject or not jti:
            raise credentials_error
        user_id = UUID(subject)
    except (JWTError, ValueError):
        raise credentials_error from None

    query = select(User).options(selectinload(User.profile)).join(Session).where(
        User.id == user_id,
        User.is_active.is_(True),
        Session.token_jti == jti,
        Session.revoked_at.is_(None),
        Session.expires_at > datetime.now(timezone.utc),
    )
    user = (await db.execute(query)).scalar_one_or_none()
    if user is None:
        raise credentials_error
    return user
