# Auteur : Adama SANE - Développeur autodidacte en apprentissage continu, sans parcours académique technologique classique | GitHub : [https://github.com/AdamaSANE](https://github.com/AdamaSANE)
"""Service applicatif d'authentification et de gestion des sessions."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.domain import Session, User

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthenticationService:
    """Encapsule les opérations sensibles pour garder les routes minces."""

    def hash_password(self, password: str) -> str:
        """Produit uniquement un hash bcrypt, jamais le mot de passe en clair."""
        return password_context.hash(password)

    def verify_password(self, password: str, password_hash: str) -> bool:
        """Compare un secret fourni au hash persistant."""
        return password_context.verify(password, password_hash)

    async def authenticate(
        self, db: AsyncSession, email: str, password: str
    ) -> User | None:
        """Retourne un compte actif si les identifiants sont valides."""
        user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
        if user is None or not user.is_active or not self.verify_password(password, user.hashed_password):
            return None
        return user

    def create_token(self, user: User) -> tuple[str, Session]:
        """Crée un JWT court et sa session révocable correspondante."""
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=settings.access_token_expire_minutes)
        jti = uuid4().hex
        session = Session(user_id=user.id, token_jti=jti, expires_at=expires_at)
        payload = {"sub": str(user.id), "jti": jti, "iat": now, "exp": expires_at}
        token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        return token, session


authentication_service = AuthenticationService()
