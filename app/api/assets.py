"""API de la marketplace de composants réutilisables."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.domain import Asset, User
from app.schemas.assets import AssetCreate, AssetResponse
from app.security import get_current_user
from app.services.assets import asset_service

router = APIRouter(prefix="/api/v1/assets", tags=["assets"])


@router.get("", response_model=list[AssetResponse])
async def list_assets(
    limit: int = Query(default=20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[Asset]:
    result = await db.scalars(select(Asset).order_by(Asset.created_at.desc()).limit(limit))
    return list(result)


@router.post("", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def create_asset(
    payload: AssetCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Asset:
    values = payload.model_dump()
    values["url"] = str(values["url"])
    return await asset_service.create(db, user.id, values)


@router.post("/{asset_id}/download", response_model=AssetResponse)
async def register_asset_download(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Asset:
    return await asset_service.register_download(db, asset_id)
