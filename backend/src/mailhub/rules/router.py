from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mailhub.config import Settings
from mailhub.db.models import (
    Attachment,
    AttachmentRule,
    MailMessage,
    RuleDestination,
    RuleExecution,
    StorageDestination,
)
from mailhub.rules.engine import RuleInput, evaluate_rule, render_folder
from mailhub.storage.crypto import decrypt_config
from mailhub.storage.rclone import upload_file


async def route_attachment(
    session: AsyncSession,
    attachment: Attachment,
    message: MailMessage,
    settings: Settings,
) -> int:
    rules = (await session.scalars(
        select(AttachmentRule)
        .where(AttachmentRule.is_enabled.is_(True))
        .order_by(AttachmentRule.priority, AttachmentRule.created_at)
    )).all()

    item = RuleInput(
        email_account_id=str(message.email_account_id),
        sender=message.sender or "",
        recipients=message.recipients or "",
        subject=message.subject or "",
        filename=attachment.original_filename,
        content_type=attachment.content_type,
        size_bytes=attachment.size_bytes,
        sent_at=message.sent_at,
    )
    routed = 0
    for rule in rules:
        match = evaluate_rule(rule, item)
        if not match.matched:
            continue

        links = (await session.scalars(
            select(RuleDestination).where(RuleDestination.rule_id == rule.id)
        )).all()
        for link in links:
            execution = await session.scalar(select(RuleExecution).where(
                RuleExecution.rule_id == rule.id,
                RuleExecution.attachment_id == attachment.id,
                RuleExecution.destination_id == link.destination_id,
            ))
            if execution and execution.status == "succeeded":
                continue

            destination = await session.get(StorageDestination, link.destination_id)
            if destination is None or not destination.is_enabled:
                continue

            execution = execution or RuleExecution(
                rule_id=rule.id,
                attachment_id=attachment.id,
                destination_id=destination.id,
                status="running",
            )
            session.add(execution)
            relative_path = str(
                Path(render_folder(rule.folder_template, item)) / attachment.safe_filename
            )
            result = await upload_file(
                destination.provider,
                destination.base_path,
                decrypt_config(settings.app_secret_key, destination.encrypted_config),
                attachment.local_path,
                relative_path,
                retries=settings.storage_retry_attempts,
            )
            execution.status = "succeeded" if result.ok else "failed"
            execution.target_path = result.target
            execution.error_message = None if result.ok else result.message[:2000]
            if result.ok:
                routed += 1
            await session.flush()

        if rule.stop_processing:
            break
    return routed
