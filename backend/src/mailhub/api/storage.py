from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mailhub.auth.dependencies import get_current_user
from mailhub.config import Settings, get_settings
from mailhub.db.models import RuleDestination, StorageDestination
from mailhub.db.session import get_session
from mailhub.storage.crypto import decrypt_config, encrypt_config
from mailhub.storage.providers import PROVIDERS, provider_definition
from mailhub.storage.rclone import test_destination
from mailhub.storage.schemas import (
    ProviderResponse,
    StorageDestinationCreate,
    StorageDestinationResponse,
    StorageDestinationUpdate,
    StorageTestResponse,
)

router = APIRouter(
    prefix="/api/v1/storage",
    tags=["storage"],
    dependencies=[Depends(get_current_user)],
)


def response(row: StorageDestination, secret: str) -> StorageDestinationResponse:
    config = decrypt_config(secret, row.encrypted_config)
    return StorageDestinationResponse(
        id=str(row.id),
        name=row.name,
        provider=row.provider,
        base_path=row.base_path,
        is_enabled=row.is_enabled,
        configured_fields=sorted(config.keys()),
        last_test_status=row.last_test_status,
        last_test_message=row.last_test_message,
        last_test_at=row.last_test_at,
    )


@router.get("/providers", response_model=list[ProviderResponse])
async def providers() -> list[ProviderResponse]:
    return [
        ProviderResponse(
            key=item.key, label=item.label,
            fields=list(item.fields), secret_fields=list(item.secret_fields)
        )
        for item in PROVIDERS.values()
    ]


@router.get("/destinations", response_model=list[StorageDestinationResponse])
async def destinations(
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> list[StorageDestinationResponse]:
    rows = (await session.scalars(
        select(StorageDestination).order_by(StorageDestination.name)
    )).all()
    return [response(row, settings.app_secret_key) for row in rows]


@router.post("/destinations", response_model=StorageDestinationResponse, status_code=201)
async def create_destination(
    request: StorageDestinationCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> StorageDestinationResponse:
    definition = provider_definition(request.provider)
    unknown = set(request.config) - set(definition.fields)
    if unknown:
        raise HTTPException(status_code=422, detail=f"Unknown config fields: {sorted(unknown)}")
    row = StorageDestination(
        name=request.name.strip(),
        provider=request.provider,
        base_path=request.base_path.strip(),
        encrypted_config=encrypt_config(settings.app_secret_key, request.config),
        is_enabled=request.is_enabled,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return response(row, settings.app_secret_key)


@router.patch("/destinations/{destination_id}", response_model=StorageDestinationResponse)
async def update_destination(
    destination_id: UUID,
    request: StorageDestinationUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> StorageDestinationResponse:
    row = await session.get(StorageDestination, destination_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Storage destination not found")
    values = request.model_dump(exclude_unset=True)
    config = values.pop("config", None)
    for key, value in values.items():
        setattr(row, key, value.strip() if isinstance(value, str) else value)
    if config is not None:
        definition = provider_definition(row.provider)
        unknown = set(config) - set(definition.fields)
        if unknown:
            raise HTTPException(status_code=422, detail=f"Unknown config fields: {sorted(unknown)}")
        row.encrypted_config = encrypt_config(settings.app_secret_key, config)
    await session.commit()
    await session.refresh(row)
    return response(row, settings.app_secret_key)


@router.delete("/destinations/{destination_id}", status_code=204)
async def delete_destination(
    destination_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    linked = await session.scalar(
        select(RuleDestination.id).where(RuleDestination.destination_id == destination_id).limit(1)
    )
    if linked:
        raise HTTPException(status_code=409, detail="Destination is used by one or more rules")
    row = await session.get(StorageDestination, destination_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Storage destination not found")
    await session.delete(row)
    await session.commit()
    return Response(status_code=204)


@router.post("/destinations/{destination_id}/test", response_model=StorageTestResponse)
async def test_storage_destination(
    destination_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> StorageTestResponse:
    row = await session.get(StorageDestination, destination_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Storage destination not found")
    result = await test_destination(
        row.provider, row.base_path,
        decrypt_config(settings.app_secret_key, row.encrypted_config)
    )
    row.last_test_status = "ok" if result.ok else "failed"
    row.last_test_message = result.message[:2000]
    row.last_test_at = datetime.now(UTC)
    await session.commit()
    if not result.ok:
        raise HTTPException(status_code=422, detail=result.message)
    return StorageTestResponse(status="ok", message=result.message)
