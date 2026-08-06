from datetime import UTC, datetime

from mailhub.operations.schemas import (
    OperationsCounts,
    OperationsDashboardResponse,
)


def test_operations_dashboard_schema() -> None:
    response = OperationsDashboardResponse(
        generated_at=datetime.now(UTC),
        overall_status="ok",
        counts=OperationsCounts(
            email_accounts=1,
            enabled_email_accounts=1,
            messages=2,
            attachments=3,
            successful_routes=3,
            failed_routes=0,
            pending_routes=0,
            healthy_storage_destinations=1,
            failed_storage_destinations=0,
        ),
        health={},
        workers=[],
        storage=[],
        recent_activity=[],
        recent_failures=[],
    )

    assert response.overall_status == "ok"
    assert response.counts.attachments == 3
