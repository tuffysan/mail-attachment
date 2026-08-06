import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Mapping

from mailhub.db.models import AttachmentRule


@dataclass(frozen=True)
class RuleInput:
    email_account_id: str
    sender: str
    recipients: str
    subject: str
    filename: str
    content_type: str
    size_bytes: int
    sent_at: datetime | None


@dataclass(frozen=True)
class MatchResult:
    matched: bool
    reasons: tuple[str, ...]


def _matches(pattern: str | None, value: str) -> bool:
    if not pattern:
        return True
    return re.search(pattern, value or "", re.IGNORECASE) is not None


def evaluate_rule(rule: AttachmentRule, item: RuleInput) -> MatchResult:
    reasons: list[str] = []

    if rule.email_account_id and str(rule.email_account_id) != item.email_account_id:
        reasons.append("wrong_email_account")
    if not _matches(rule.sender_pattern, item.sender):
        reasons.append("sender")
    if not _matches(rule.recipient_pattern, item.recipients):
        reasons.append("recipient")
    if not _matches(rule.subject_pattern, item.subject):
        reasons.append("subject")
    if not _matches(rule.filename_pattern, item.filename):
        reasons.append("filename")
    if not _matches(rule.content_type_pattern, item.content_type):
        reasons.append("content_type")
    if rule.min_size_bytes is not None and item.size_bytes < rule.min_size_bytes:
        reasons.append("min_size")
    if rule.max_size_bytes is not None and item.size_bytes > rule.max_size_bytes:
        reasons.append("max_size")

    return MatchResult(matched=not reasons, reasons=tuple(reasons))


def sanitize_segment(value: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9._ -]+", "_", value or "unknown").strip(" .")
    return clean[:120] or "unknown"


def render_folder(template: str, item: RuleInput) -> str:
    timestamp = item.sent_at or datetime.utcnow()
    sender = item.sender.split("@")[0] if "@" in item.sender else item.sender
    values: Mapping[str, str] = {
        "year": f"{timestamp.year:04d}",
        "month": f"{timestamp.month:02d}",
        "day": f"{timestamp.day:02d}",
        "sender": sanitize_segment(sender),
        "sender_email": sanitize_segment(item.sender),
        "subject": sanitize_segment(item.subject),
        "filename": sanitize_segment(Path(item.filename).stem),
        "extension": sanitize_segment(Path(item.filename).suffix.lstrip(".")),
    }
    try:
        rendered = template.format_map(values)
    except KeyError as exc:
        raise ValueError(f"Unknown folder-template variable: {exc.args[0]}") from exc

    path = Path(rendered)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("Folder template must resolve to a relative safe path")
    return str(path)
