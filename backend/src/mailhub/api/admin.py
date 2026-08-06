import hashlib
import json
import secrets
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from mailhub.auth.dependencies import get_current_user
from mailhub.db.models import ApiKey, Attachment, AuditLog, EmailAccount, MailMessage, RuleExecution, User
from mailhub.db.session import get_session

router = APIRouter(prefix="/api/v1/admin", tags=["administration"])


async def require_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Administrator access required")
    return user


class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


@router.get("/stats", dependencies=[Depends(require_admin)])
async def stats(session: Annotated[AsyncSession, Depends(get_session)]):
    async def count(model):
        return int(await session.scalar(select(func.count()).select_from(model)) or 0)
    return {
        "email_accounts": await count(EmailAccount),
        "messages": await count(MailMessage),
        "attachments": await count(Attachment),
        "successful_routes": int(await session.scalar(
            select(func.count()).select_from(RuleExecution).where(RuleExecution.status == "succeeded")
        ) or 0),
        "failed_routes": int(await session.scalar(
            select(func.count()).select_from(RuleExecution).where(RuleExecution.status == "failed")
        ) or 0),
    }


@router.post("/api-keys", dependencies=[Depends(require_admin)])
async def create_api_key(
    payload: ApiKeyCreate,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(require_admin)],
):
    raw = "mah_" + secrets.token_urlsafe(32)
    digest = hashlib.sha256(raw.encode()).hexdigest()
    row = ApiKey(name=payload.name, key_hash=digest, prefix=raw[:12])
    session.add(row)
    session.add(AuditLog(
        user_id=user.id, action="api_key.created", entity_type="api_key",
        entity_id=str(row.id), remote_address=request.client.host if request.client else None,
    ))
    await session.commit()
    return {"id": str(row.id), "name": row.name, "key": raw, "prefix": row.prefix}


@router.get("/api-keys", dependencies=[Depends(require_admin)])
async def list_api_keys(session: Annotated[AsyncSession, Depends(get_session)]):
    rows = (await session.scalars(select(ApiKey).order_by(desc(ApiKey.created_at)))).all()
    return [{"id":str(x.id),"name":x.name,"prefix":x.prefix,"is_active":x.is_active,"last_used_at":x.last_used_at} for x in rows]


@router.get("/audit", dependencies=[Depends(require_admin)])
async def audit(session: Annotated[AsyncSession, Depends(get_session)], limit: int = 100):
    rows=(await session.scalars(select(AuditLog).order_by(desc(AuditLog.created_at)).limit(min(limit,500)))).all()
    return [{"id":str(x.id),"action":x.action,"entity_type":x.entity_type,"entity_id":x.entity_id,
             "details":json.loads(x.details_json) if x.details_json else None,"created_at":x.created_at} for x in rows]
