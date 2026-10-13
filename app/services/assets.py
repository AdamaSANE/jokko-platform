"""Règles métier de la marketplace."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import Asset


class AssetService:
    async def create(self, db: AsyncSession, author_id: UUID, values: dict[str, object]) -> Asset:
        asset = Asset(author_id=author_id, **values)
        db.add(asset)
        await db.commit()
        await db.refresh(asset)
        return asset

    async def register_download(self, db: AsyncSession, asset_id: UUID) -> Asset:
        asset = await db.get(Asset, asset_id)
        if asset is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Composant introuvable")
        asset.download_count += 1
        await db.commit()
        await db.refresh(asset)
        return asset


asset_service = AssetService()
