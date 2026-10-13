# Auteur : Adama SANE - Développeur autodidacte en apprentissage continu, sans parcours académique technologique classique | GitHub : [https://github.com/AdamaSANE](https://github.com/AdamaSANE)
"""Contrats HTTP de l'authentification."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    """Données minimales nécessaires à la création d'un compte."""

    email: EmailStr
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=100)
    country: str | None = Field(default=None, min_length=2, max_length=100)
    tech_stack: list[str] = Field(default_factory=list, max_length=30)


class LoginRequest(BaseModel):
    """Identifiants de connexion JSON, sans dépendance multipart."""

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    """Réponse standard Bearer utilisée par le frontend."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """Représentation publique minimale du compte."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    username: str
    is_active: bool
