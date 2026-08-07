import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mailhub.config import Settings
from mailhub.db.models import ActivityEvent, Attachment, EmailAccount, MailMessage, SyncRun
from mailhub.mail.crypto import CredentialCipher
from mailhub.mail.engine import ParsedAttachment, fetch_messages
from mailhub.mail.oauth import refresh_access_token
from mailhub.rules.router import route_attachment


async def activity(session: AsyncSession, event_type: str, message: str, account_id=None, level="info", details=None):
    session.add(ActivityEvent(
        event_type=event_type, message=message, email_account_id=account_id,
        level=level, details_json=json.dumps(details) if details else None
    ))


async def _credential(account: EmailAccount, settings: Settings, session: AsyncSession):
    cipher = CredentialCipher(settings.app_secret_key)
    if account.auth_type == "oauth":
        if not account.encrypted_refresh_token:
            raise ValueError("OAuth account has no refresh token")
        now = datetime.now(UTC)
        if account.encrypted_access_token and account.access_token_expires_at and account.access_token_expires_at > now + timedelta(minutes=2):
            return None, cipher.decrypt(account.encrypted_access_token)
        tokens = await refresh_access_token(
            account.oauth_provider or "", cipher.decrypt(account.encrypted_refresh_token), settings, session
        )
        access = tokens["access_token"]
        account.encrypted_access_token = cipher.encrypt(access)
        account.access_token_expires_at = now + timedelta(seconds=int(tokens.get("expires_in", 3600)))
        await session.flush()
        return None, access
    if not account.encrypted_password:
        raise ValueError("Password account has no password")
    return cipher.decrypt(account.encrypted_password), None


async def sync_account(account_id: UUID, session: AsyncSession, settings: Settings, attempt: int = 1) -> SyncRun:
    account = await session.get(EmailAccount, account_id)
    if not account or not account.is_enabled:
        raise ValueError("Email account not found or disabled")
    run = SyncRun(
        email_account_id=account.id, status="running", attempt=attempt, started_at=datetime.now(UTC)
    )
    session.add(run)
    await session.commit()
    try:
        password, access_token = await _credential(account, settings, session)
        messages = await fetch_messages(
            host=account.host, port=account.port, username=account.username,
            password=password, access_token=access_token, mailbox=account.mailbox,
            use_ssl=account.use_ssl, start_uid=account.last_uid,
            limit=settings.sync_batch_size, timeout=settings.imap_timeout_seconds,
            extract_zip=settings.extract_zip_attachments,
            max_zip_files=settings.max_zip_files,
            max_zip_bytes=settings.max_zip_expanded_bytes,
        )
        run.messages_seen = len(messages)
        base = Path(settings.attachment_data_dir)
        base.mkdir(parents=True, exist_ok=True)
        for parsed in messages:
            existing = await session.scalar(select(MailMessage).where(
                MailMessage.email_account_id == account.id,
                MailMessage.mailbox == account.mailbox,
                MailMessage.uid == parsed.uid,
            ))
            if existing:
                account.last_uid = max(account.last_uid, parsed.uid)
                continue
            message = MailMessage(
                email_account_id=account.id, mailbox=account.mailbox, uid=parsed.uid,
                message_id=parsed.message_id, sender=parsed.sender, recipients=parsed.recipients,
                subject=parsed.subject, sent_at=parsed.sent_at, body_preview=parsed.body_preview,
                raw_size=parsed.raw_size, content_sha256=parsed.content_sha256,
            )
            session.add(message)
            await session.flush()
            run.messages_created += 1
            message_dir = base / str(account.id) / str(message.id)
            message_dir.mkdir(parents=True, exist_ok=True)
            parent_by_name = {}
            for item in parsed.attachments:
                duplicate = await session.scalar(select(Attachment).where(
                    Attachment.mail_message_id == message.id,
                    Attachment.sha256 == item.sha256,
                    Attachment.safe_filename == item.filename,
                ))
                if duplicate:
                    continue
                path = message_dir / item.filename
                suffix = 1
                while path.exists():
                    path = message_dir / f"{path.stem}-{suffix}{path.suffix}"
                    suffix += 1
                path.write_bytes(item.content)
                attachment = Attachment(
                    mail_message_id=message.id, original_filename=item.filename,
                    safe_filename=path.name, content_type=item.content_type,
                    size_bytes=len(item.content), sha256=item.sha256, local_path=str(path),
                    archive_parent_id=parent_by_name.get(item.archive_parent_name),
                )
                session.add(attachment)
                await session.flush()
                parent_by_name[item.filename] = attachment.id
                run.attachments_created += 1
            account.last_uid = max(account.last_uid, parsed.uid)
        account.last_sync_at = datetime.now(UTC)
        run.status = "succeeded"
        await activity(session, "sync_succeeded", f"Synced {run.messages_created} new messages", account.id,
                       details={"attachments": run.attachments_created})
    except Exception as exc:
        run.status = "failed"
        run.error_message = str(exc)[:2000]
        await activity(session, "sync_failed", str(exc), account.id, "error")
    finally:
        run.finished_at = datetime.now(UTC)
        await session.commit()
    return run
