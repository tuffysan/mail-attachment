from fastapi.testclient import TestClient

from mailhub.health import ProbeResult
from mailhub.main import app


def test_root_metadata() -> None:
    with TestClient(app) as client:
        response = client.get("/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "Mail Attachment Hub"
    assert payload["version"] == "0.3.0"


def test_liveness() -> None:
    with TestClient(app) as client:
        response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.3.0"}


def test_readiness_healthy(monkeypatch) -> None:
    async def healthy_checks(_settings):
        return [
            ProbeResult("postgres", True, "ok"),
            ProbeResult("redis", True, "ok"),
        ]

    monkeypatch.setattr("mailhub.main.run_readiness_checks", healthy_checks)
    with TestClient(app) as client:
        response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness_degraded(monkeypatch) -> None:
    async def degraded_checks(_settings):
        return [
            ProbeResult("postgres", True, "ok"),
            ProbeResult("redis", False, "TimeoutError"),
        ]

    monkeypatch.setattr("mailhub.main.run_readiness_checks", degraded_checks)
    with TestClient(app) as client:
        response = client.get("/health/ready")

    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "degraded"
    assert payload["checks"]["redis"]["status"] == "failed"
