import shutil
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mailhub.db.models import (
    Attachment,
    AttachmentRule,
    MailMessage,
    RuleDestination,
    RuleExecution,
    StorageDestination,
)
from mailhub.rules.engine import RuleInput, evaluate_rule, render_folder


async def route_attachment(
    session: AsyncSession,
    attachment: Attachment,
    message: MailMessage,
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
        result = evaluate_rule(rule, item)
        if not result.matched:
            continue

        links = (await session.scalars(
            select(RuleDestination).where(RuleDestination.rule_id == rule.id)
        )).all()
        for link in links:
            existing = await session.scalar(select(RuleExecution).where(
                RuleExecution.rule_id == rule.id,
                RuleExecution.attachment_id == attachment.id,
                RuleExecution.destination_id == link.destination_id,
            ))
            if existing and existing.status == "succeeded":
                continue

            destination = await session.get(StorageDestination, link.destination_id)
            if destination is None or not destination.is_enabled:
                continue

            execution = existing or RuleExecution(
                rule_id=rule.id,
                attachment_id=attachment.id,
                destination_id=destination.id,
                status="running",
            )
            session.add(execution)
            try:
                relative = Path(render_folder(rule.folder_template, item)) / attachment.safe_filename
                target = Path(destination.base_path) / relative
                target.parent.mkdir(parents=True, exist_ok=True)

                if destination.provider != "local":
                    raise RuntimeError(
                        f"Provider {destination.provider!r} is configured but will be implemented in Step 010"
                    )

                shutil.copy2(attachment.local_path, target)
                execution.status = "succeeded"
                execution.target_path = str(target)
                execution.error_message = None
                routed += 1
            except Exception as exc:
                execution.status = "failed"
                execution.error_message = str(exc)[:2000]
            await session.flush()

        if rule.stop_processing:
            break
    return routed
