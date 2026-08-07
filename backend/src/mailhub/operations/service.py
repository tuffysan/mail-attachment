from datetime import UTC, datetime

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from mailhub.config import Settings
from mailhub.core.lifecycle import worker_registry
from mailhub.db.models import (
    ActivityEvent,
    Attachment,
    EmailAccount,
    MailMessage,
    RuleExecution,
    StorageDestination,
    SyncRun,
)
from mailhub.health import run_readiness_checks
from mailhub.maintenance_control import read_backups, read_maintenance_status
from mailhub.operations.schemas import (
    OperationsActivity,
    OperationsBackupSummary,
    OperationsCounts,
    OperationsDashboardResponse,
    OperationsFailure,
    OperationsRecentSync,
    OperationsHealthCheck,
    OperationsWorker,
    StorageHealthItem,
)
from mailhub.operations.system_resources import collect_system_resources


async def _count(session: AsyncSession, model, *criteria) -> int:
    statement = select(func.count()).select_from(model)
    for criterion in criteria:
        statement = statement.where(criterion)
    return int(await session.scalar(statement) or 0)


async def build_operations_dashboard(
    session: AsyncSession,
    settings: Settings,
) -> OperationsDashboardResponse:
    checks = await run_readiness_checks(settings)

    counts = OperationsCounts(
        email_accounts=await _count(session, EmailAccount),
        enabled_email_accounts=await _count(
            session,
            EmailAccount,
            EmailAccount.is_enabled.is_(True),
        ),
        messages=await _count(session, MailMessage),
        attachments=await _count(session, Attachment),
        successful_routes=await _count(
            session,
            RuleExecution,
            RuleExecution.status == "succeeded",
        ),
        failed_routes=await _count(
            session,
            RuleExecution,
            RuleExecution.status == "failed",
        ),
        pending_routes=await _count(
            session,
            RuleExecution,
            RuleExecution.status.in_(["pending", "running", "retrying"]),
        ),
        healthy_storage_destinations=await _count(
            session,
            StorageDestination,
            StorageDestination.last_test_status == "ok",
        ),
        failed_storage_destinations=await _count(
            session,
            StorageDestination,
            StorageDestination.last_test_status == "failed",
        ),
    )

    storage_rows = (
        await session.scalars(
            select(StorageDestination).order_by(StorageDestination.name)
        )
    ).all()
    storage = [
        StorageHealthItem(
            id=str(row.id),
            name=row.name,
            provider=row.provider,
            enabled=row.is_enabled,
            status=row.last_test_status or "unknown",
            message=row.last_test_message,
            checked_at=row.last_test_at,
        )
        for row in storage_rows
    ]

    activity_rows = (
        await session.scalars(
            select(ActivityEvent)
            .order_by(desc(ActivityEvent.created_at))
            .limit(20)
        )
    ).all()
    recent_activity = [
        OperationsActivity(
            id=str(row.id),
            level=row.level,
            event_type=row.event_type,
            message=row.message,
            created_at=row.created_at,
        )
        for row in activity_rows
    ]

    route_failures = (
        await session.scalars(
            select(RuleExecution)
            .where(RuleExecution.status == "failed")
            .order_by(desc(RuleExecution.created_at))
            .limit(10)
        )
    ).all()
    sync_failures = (
        await session.scalars(
            select(SyncRun)
            .where(SyncRun.status == "failed")
            .order_by(desc(SyncRun.created_at))
            .limit(10)
        )
    ).all()

    recent_failures = [
        OperationsFailure(
            id=str(row.id),
            kind="routing",
            subject=row.target_path or str(row.attachment_id),
            detail=row.error_message or "Routing failed",
            created_at=row.created_at,
        )
        for row in route_failures
    ]
    recent_failures.extend(
        OperationsFailure(
            id=str(row.id),
            kind="sync",
            subject=str(row.email_account_id),
            detail=row.error_message or "Synchronization failed",
            created_at=row.created_at,
        )
        for row in sync_failures
    )
    recent_failures.sort(key=lambda item: item.created_at, reverse=True)
    recent_failures = recent_failures[:20]


    recent_sync_rows = (
        await session.execute(
            select(SyncRun, EmailAccount)
            .join(
                EmailAccount,
                EmailAccount.id == SyncRun.email_account_id,
            )
            .order_by(desc(SyncRun.started_at))
            .limit(12)
        )
    ).all()
    recent_syncs = [
        OperationsRecentSync(
            id=str(sync_run.id),
            email_account_id=str(sync_run.email_account_id),
            account_name=account.name,
            email_address=account.email_address,
            status=sync_run.status,
            started_at=sync_run.started_at,
            finished_at=sync_run.finished_at,
            messages_seen=sync_run.messages_seen,
            messages_created=sync_run.messages_created,
            attachments_created=sync_run.attachments_created,
            error_message=sync_run.error_message,
        )
        for sync_run, account in recent_sync_rows
    ]

    backup_rows = read_backups()
    maintenance = read_maintenance_status()

    def backup_created(item):
        value = item.get("created_at")
        if not value:
            return datetime.min.replace(tzinfo=UTC)
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            return (
                parsed.replace(tzinfo=UTC)
                if parsed.tzinfo is None
                else parsed.astimezone(UTC)
            )
        except ValueError:
            return datetime.min.replace(tzinfo=UTC)

    sorted_backups = sorted(
        backup_rows,
        key=backup_created,
        reverse=True,
    )
    latest_backup = sorted_backups[0] if sorted_backups else None
    latest_created_at = (
        backup_created(latest_backup)
        if latest_backup and latest_backup.get("created_at")
        else None
    )
    backup_summary = OperationsBackupSummary(
        count=len(sorted_backups),
        latest_id=(
            str(latest_backup.get("id"))
            if latest_backup
            else None
        ),
        latest_created_at=latest_created_at,
        latest_size_bytes=(
            int(latest_backup.get("size_bytes") or 0)
            if latest_backup
            else 0
        ),
        total_size_bytes=sum(
            int(item.get("size_bytes") or 0)
            for item in sorted_backups
        ),
        status=str(maintenance.get("state") or "idle"),
        message=(
            str(maintenance.get("message"))
            if maintenance.get("message")
            else None
        ),
    )

    system = collect_system_resources()

    workers = [
        OperationsWorker(
            name=item.name,
            state=str(item.state),
            started_at=item.started_at,
            heartbeat_at=item.heartbeat_at,
            last_activity_at=item.last_activity_at,
            processed_cycles=item.processed_cycles,
            failures=item.failures,
            last_error=item.last_error,
        )
        for item in worker_registry.snapshots()
    ]

    health = {
        item.name: OperationsHealthCheck(
            status="ok" if item.healthy else "failed",
            detail=item.detail,
            latency_ms=item.latency_ms,
        )
        for item in checks
    }

    degraded = (
        any(item.status == "failed" for item in health.values())
        or counts.failed_routes > 0
        or counts.failed_storage_destinations > 0
        or any(item.state == "failed" for item in workers)
        or system.memory_used_percent >= 95
        or system.disk_used_percent >= 95
        or backup_summary.status == "error"
    )

    return OperationsDashboardResponse(
        generated_at=datetime.now(UTC),
        overall_status="degraded" if degraded else "ok",
        counts=counts,
        health=health,
        workers=workers,
        storage=storage,
        recent_activity=recent_activity,
        recent_failures=recent_failures,
        recent_syncs=recent_syncs,
        system=system,
        backups=backup_summary,
    )
