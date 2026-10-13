# Auteur : Adama SANE - Développeur autodidacte en apprentissage continu, sans parcours académique technologique classique | GitHub : [https://github.com/AdamaSANE](https://github.com/AdamaSANE)
"""Point d'entrée FastAPI.

Le sas d'authentification sera appliqué aux routeurs privés via une dépendance
``get_current_user``. Seuls auth et password_reset seront montés publiquement.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import assets, auth, exchanges, password_reset, private

app = FastAPI(title="JOKKO API", version="0.1.0")
app.add_middleware(GZipMiddleware, minimum_size=500)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router)
app.include_router(auth.router, prefix="/api/v1")
app.include_router(password_reset.router)
app.include_router(private.router)
app.include_router(exchanges.router)
app.include_router(assets.router)
REACT_DIST = Path(__file__).resolve().parent.parent / "frontend-react" / "dist"
LEGACY_FRONTEND = Path(__file__).resolve().parent.parent / "frontend"
frontend_directory = REACT_DIST if REACT_DIST.exists() else LEGACY_FRONTEND

app.mount("/", StaticFiles(directory=frontend_directory, html=True), name="frontend")
