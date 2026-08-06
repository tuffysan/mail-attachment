from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from mailhub.rules.engine import RuleInput, evaluate_rule, render_folder


def rule(**kwargs):
    defaults = dict(
        email_account_id=None,
        sender_pattern=None,
        recipient_pattern=None,
        subject_pattern=None,
        filename_pattern=None,
        content_type_pattern=None,
        min_size_bytes=None,
        max_size_bytes=None,
        folder_template="{year}/{month}/{sender}",
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def item(**kwargs):
    defaults = dict(
        email_account_id="a",
        sender="invoice@example.com",
        recipients="accounts@example.com",
        subject="Invoice 123",
        filename="invoice.pdf",
        content_type="application/pdf",
        size_bytes=1000,
        sent_at=datetime(2026, 8, 6, tzinfo=UTC),
    )
    defaults.update(kwargs)
    return RuleInput(**defaults)


def test_matching_rule():
    result = evaluate_rule(rule(sender_pattern="example", filename_pattern=r"\.pdf$"), item())
    assert result.matched is True


def test_non_matching_rule_explains_reason():
    result = evaluate_rule(rule(subject_pattern="receipt"), item())
    assert result.matched is False
    assert "subject" in result.reasons


def test_folder_template():
    assert render_folder("{year}/{month}/{sender}", item()) == "2026/08/invoice"


def test_folder_template_rejects_traversal():
    with pytest.raises(ValueError):
        render_folder("../secret", item())
