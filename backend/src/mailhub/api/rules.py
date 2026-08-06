from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from mailhub.auth.dependencies import get_current_user
from mailhub.db.models import AttachmentRule, RuleDestination, StorageDestination
from mailhub.db.session import get_session
from mailhub.rules.engine import RuleInput, evaluate_rule, render_folder
from mailhub.rules.schemas import (
    AttachmentRuleCreate,
    AttachmentRuleResponse,
    RuleSimulationRequest,
    RuleSimulationResult,
    StorageDestinationCreate,
    StorageDestinationResponse,
)

router = APIRouter(prefix="/api/v1", tags=["rules"], dependencies=[Depends(get_current_user)])


async def destination_ids(session: AsyncSession, rule_id: UUID) -> list[str]:
    values = await session.scalars(
        select(RuleDestination.destination_id).where(RuleDestination.rule_id == rule_id)
    )
    return [str(value) for value in values]


async def rule_response(session: AsyncSession, rule: AttachmentRule) -> AttachmentRuleResponse:
    return AttachmentRuleResponse(
        id=str(rule.id), name=rule.name,
        email_account_id=str(rule.email_account_id) if rule.email_account_id else None,
        priority=rule.priority, is_enabled=rule.is_enabled,
        stop_processing=rule.stop_processing,
        sender_pattern=rule.sender_pattern, recipient_pattern=rule.recipient_pattern,
        subject_pattern=rule.subject_pattern, filename_pattern=rule.filename_pattern,
        content_type_pattern=rule.content_type_pattern,
        min_size_bytes=rule.min_size_bytes, max_size_bytes=rule.max_size_bytes,
        folder_template=rule.folder_template,
        destination_ids=await destination_ids(session, rule.id),
    )


@router.get("/storage-destinations", response_model=list[StorageDestinationResponse])
async def list_storage_destinations(
    session: Annotated[AsyncSession, Depends(get_session)]
) -> list[StorageDestinationResponse]:
    rows = (await session.scalars(
        select(StorageDestination).order_by(StorageDestination.name)
    )).all()
    return [
        StorageDestinationResponse(
            id=str(row.id), name=row.name, provider=row.provider,
            base_path=row.base_path, is_enabled=row.is_enabled
        )
        for row in rows
    ]


@router.post("/storage-destinations", response_model=StorageDestinationResponse, status_code=201)
async def create_storage_destination(
    request: StorageDestinationCreate,
    session: Annotated[AsyncSession, Depends(get_session)]
) -> StorageDestinationResponse:
    row = StorageDestination(
        name=request.name.strip(), provider=request.provider,
        base_path=request.base_path.strip(), is_enabled=request.is_enabled
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return StorageDestinationResponse(
        id=str(row.id), name=row.name, provider=row.provider,
        base_path=row.base_path, is_enabled=row.is_enabled
    )


@router.get("/rules", response_model=list[AttachmentRuleResponse])
async def list_rules(
    session: Annotated[AsyncSession, Depends(get_session)]
) -> list[AttachmentRuleResponse]:
    rows = (await session.scalars(
        select(AttachmentRule).order_by(AttachmentRule.priority, AttachmentRule.created_at)
    )).all()
    return [await rule_response(session, row) for row in rows]


@router.post("/rules", response_model=AttachmentRuleResponse, status_code=201)
async def create_rule(
    request: AttachmentRuleCreate,
    session: Annotated[AsyncSession, Depends(get_session)]
) -> AttachmentRuleResponse:
    if request.min_size_bytes is not None and request.max_size_bytes is not None:
        if request.min_size_bytes > request.max_size_bytes:
            raise HTTPException(status_code=422, detail="Minimum size cannot exceed maximum size")

    destination_uuid = [UUID(value) for value in request.destination_ids]
    found = (await session.scalars(
        select(StorageDestination.id).where(StorageDestination.id.in_(destination_uuid))
    )).all()
    if len(found) != len(set(destination_uuid)):
        raise HTTPException(status_code=422, detail="One or more storage destinations do not exist")

    rule = AttachmentRule(
        name=request.name.strip(),
        email_account_id=UUID(request.email_account_id) if request.email_account_id else None,
        priority=request.priority,
        is_enabled=request.is_enabled,
        stop_processing=request.stop_processing,
        sender_pattern=request.sender_pattern or None,
        recipient_pattern=request.recipient_pattern or None,
        subject_pattern=request.subject_pattern or None,
        filename_pattern=request.filename_pattern or None,
        content_type_pattern=request.content_type_pattern or None,
        min_size_bytes=request.min_size_bytes,
        max_size_bytes=request.max_size_bytes,
        folder_template=request.folder_template.strip(),
    )
    session.add(rule)
    await session.flush()
    session.add_all([
        RuleDestination(rule_id=rule.id, destination_id=destination_id)
        for destination_id in destination_uuid
    ])
    await session.commit()
    await session.refresh(rule)
    return await rule_response(session, rule)


@router.delete("/rules/{rule_id}", status_code=204)
async def delete_rule(
    rule_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)]
) -> Response:
    rule = await session.get(AttachmentRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    await session.delete(rule)
    await session.commit()
    return Response(status_code=204)


@router.post("/rules/simulate", response_model=list[RuleSimulationResult])
async def simulate_rules(
    request: RuleSimulationRequest,
    session: Annotated[AsyncSession, Depends(get_session)]
) -> list[RuleSimulationResult]:
    rows = (await session.scalars(
        select(AttachmentRule)
        .where(AttachmentRule.is_enabled.is_(True))
        .order_by(AttachmentRule.priority, AttachmentRule.created_at)
    )).all()
    item = RuleInput(
        email_account_id=request.email_account_id,
        sender=request.sender,
        recipients=request.recipients,
        subject=request.subject,
        filename=request.filename,
        content_type=request.content_type,
        size_bytes=request.size_bytes,
        sent_at=request.sent_at,
    )
    output = []
    for rule in rows:
        result = evaluate_rule(rule, item)
        output.append(RuleSimulationResult(
            rule_id=str(rule.id), rule_name=rule.name,
            matched=result.matched, reasons=list(result.reasons),
            rendered_folder=render_folder(rule.folder_template, item) if result.matched else None,
            destination_ids=await destination_ids(session, rule.id),
        ))
        if result.matched and rule.stop_processing:
            break
    return output
