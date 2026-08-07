from mailhub.db.base import Base


TIMESTAMP_TABLES = {
    "system_metadata",
    "users",
    "email_accounts",
    "oauth_states",
    "mail_messages",
    "attachments",
    "sync_runs",
    "activity_events",
    "storage_destinations",
    "attachment_rules",
    "rule_destinations",
    "rule_executions",
    "api_keys",
    "notification_endpoints",
    "audit_logs",
}


def test_timestamp_mixin_columns_have_server_defaults() -> None:
    for table_name in sorted(TIMESTAMP_TABLES):
        table = Base.metadata.tables[table_name]
        assert table.c.created_at.server_default is not None, table_name
        assert table.c.updated_at.server_default is not None, table_name
