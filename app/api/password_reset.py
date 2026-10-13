"""Routes publiques de récupération et renouvellement de mot de passe."""

from fastapi import APIRouter

router = APIRouter(prefix="/password-reset", tags=["password-reset"])
