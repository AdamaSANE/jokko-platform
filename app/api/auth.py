# Auteur : Adama SANE - Développeur autodidacte en apprentissage continu, sans parcours académique technologique classique | GitHub : [https://github.com/AdamaSANE](https://github.com/AdamaSANE)
"""Routes publiques d'inscription, connexion et révocation de session."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.models.domain import DeveloperProfile, Session, User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.security import get_current_user, oauth2_scheme
from app.services.auth import authentication_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> User:
    """Crée simultanément le compte et son profil développeur initial."""
    existing = (await db.execute(
        select(User).where((User.email == payload.email) | (User.username == payload.username))
    )).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email ou nom déjà utilisé")
    user = User(
        email=payload.email,
        username=payload.username,
        hashed_password=authentication_service.hash_password(payload.password),
    )
    user.profile = DeveloperProfile(
        display_name=payload.display_name,
        location=payload.country,
        skills=payload.tech_stack,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """Authentifie un compte et persiste la session liée au JWT."""
    user = await authentication_service.authenticate(db, payload.email, payload.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Identifiants invalides")
    token, session = authentication_service.create_token(user)
    db.add(session)
    await db.commit()
    return TokenResponse(access_token=token, expires_in=settings.access_token_expire_minutes * 60)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> None:
    """Révoque la session du token courant."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        jti = payload.get("jti")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalide") from None
    if not jti:
        raise HTTPException(status_code=401, detail="Token invalide")
    session = (await db.execute(select(Session).where(Session.token_jti == jti))).scalar_one_or_none()
    if session is not None:
        session.revoked_at = datetime.now(timezone.utc)
        await db.commit()


@router.get("/me", response_model=UserResponse)
async def current_user(user: User = Depends(get_current_user)) -> User:
    """Retourne le compte authentifié."""
    return user
