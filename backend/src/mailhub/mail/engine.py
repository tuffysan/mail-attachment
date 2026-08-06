import asyncio
import email
import hashlib
import imaplib
import io
import re
import ssl
import zipfile
from dataclasses import dataclass, field
from datetime import UTC, datetime
from email.header import decode_header, make_header
from email.message import Message
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Callable

SAFE_NAME = re.compile(r"[^A-Za-z0-9._ -]+")


@dataclass
class ParsedAttachment:
    filename: str
    content_type: str
    content: bytes
    archive_parent_name: str | None = None

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.content).hexdigest()


@dataclass
class ParsedMessage:
    uid: int
    message_id: str | None
    sender: str | None
    recipients: str | None
    subject: str | None
    sent_at: datetime | None
    body_preview: str | None
    raw_size: int
    content_sha256: str
    attachments: list[ParsedAttachment] = field(default_factory=list)


def safe_filename(name: str) -> str:
    decoded = str(make_header(decode_header(name or "attachment.bin")))
    cleaned = SAFE_NAME.sub("_", decoded).strip(" .")
    return cleaned[:240] or "attachment.bin"


def _body_preview(message: Message) -> str | None:
    for part in message.walk():
        if part.get_content_type() == "text/plain" and part.get_content_disposition() != "attachment":
            payload = part.get_payload(decode=True) or b""
            charset = part.get_content_charset() or "utf-8"
            return payload.decode(charset, errors="replace").strip()[:1000]
    return None


def _extract_zip(parent: ParsedAttachment, max_files: int, max_total_bytes: int) -> list[ParsedAttachment]:
    if not zipfile.is_zipfile(io.BytesIO(parent.content)):
        return []
    output: list[ParsedAttachment] = []
    total = 0
    with zipfile.ZipFile(io.BytesIO(parent.content)) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            if len(output) >= max_files:
                raise ValueError("ZIP file contains too many files")
            total += info.file_size
            if total > max_total_bytes:
                raise ValueError("ZIP expanded size exceeds configured limit")
            output.append(
                ParsedAttachment(
                    filename=safe_filename(Path(info.filename).name),
                    content_type="application/octet-stream",
                    content=archive.read(info),
                    archive_parent_name=parent.filename,
                )
            )
    return output


def parse_message(uid: int, raw: bytes, extract_zip: bool, max_zip_files: int, max_zip_bytes: int) -> ParsedMessage:
    message = email.message_from_bytes(raw)
    attachments: list[ParsedAttachment] = []
    for part in message.walk():
        filename = part.get_filename()
        disposition = part.get_content_disposition()
        if not filename and disposition != "attachment":
            continue
        content = part.get_payload(decode=True) or b""
        item = ParsedAttachment(
            filename=safe_filename(filename or "attachment.bin"),
            content_type=part.get_content_type() or "application/octet-stream",
            content=content,
        )
        attachments.append(item)
        if extract_zip and item.filename.lower().endswith(".zip"):
            attachments.extend(_extract_zip(item, max_zip_files, max_zip_bytes))

    sent_at = None
    if message.get("Date"):
        try:
            sent_at = parsedate_to_datetime(message.get("Date"))
            if sent_at.tzinfo is None:
                sent_at = sent_at.replace(tzinfo=UTC)
        except (TypeError, ValueError):
            pass

    subject = str(make_header(decode_header(message.get("Subject", "")))) or None
    return ParsedMessage(
        uid=uid,
        message_id=message.get("Message-ID"),
        sender=message.get("From"),
        recipients=message.get("To"),
        subject=subject,
        sent_at=sent_at,
        body_preview=_body_preview(message),
        raw_size=len(raw),
        content_sha256=hashlib.sha256(raw).hexdigest(),
        attachments=attachments,
    )


def _oauth_auth_string(username: str, access_token: str) -> bytes:
    return f"user={username}\x01auth=Bearer {access_token}\x01\x01".encode()


def fetch_sync(
    *,
    host: str,
    port: int,
    username: str,
    password: str | None,
    access_token: str | None,
    mailbox: str,
    use_ssl: bool,
    start_uid: int,
    limit: int,
    timeout: float,
    extract_zip: bool,
    max_zip_files: int,
    max_zip_bytes: int,
) -> list[ParsedMessage]:
    connection = None
    try:
        connection = (
            imaplib.IMAP4_SSL(host, port, ssl_context=ssl.create_default_context(), timeout=timeout)
            if use_ssl else imaplib.IMAP4(host, port, timeout=timeout)
        )
        if access_token:
            connection.authenticate("XOAUTH2", lambda _: _oauth_auth_string(username, access_token))
        elif password:
            connection.login(username, password)
        else:
            raise ValueError("No usable credential")
        status, _ = connection.select(mailbox, readonly=True)
        if status != "OK":
            raise RuntimeError(f"Cannot open mailbox {mailbox}")
        status, data = connection.uid("search", None, f"UID {start_uid + 1}:*")
        if status != "OK" or not data:
            return []
        uids = [int(x) for x in data[0].split()][:limit]
        parsed: list[ParsedMessage] = []
        for uid in uids:
            status, payload = connection.uid("fetch", str(uid), "(RFC822)")
            if status != "OK" or not payload:
                continue
            raw = next((part[1] for part in payload if isinstance(part, tuple)), None)
            if raw:
                parsed.append(parse_message(uid, raw, extract_zip, max_zip_files, max_zip_bytes))
        return parsed
    finally:
        if connection:
            try:
                connection.logout()
            except Exception:
                pass


async def fetch_messages(**kwargs) -> list[ParsedMessage]:
    return await asyncio.to_thread(fetch_sync, **kwargs)
