from fastapi import FastAPI
from fastapi.testclient import TestClient

from mailhub.core.middleware import RequestContextMiddleware, SecurityHeadersMiddleware


def app_client() -> TestClient:
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware, enabled=True)
    app.add_middleware(RequestContextMiddleware)

    @app.get("/example")
    async def example() -> dict[str, bool]:
        return {"ok": True}

    return TestClient(app)


def test_request_context_headers_are_created() -> None:
    with app_client() as client:
        response = client.get("/example")
    assert response.status_code == 200
    assert response.headers["x-request-id"]
    assert response.headers["x-correlation-id"] == response.headers["x-request-id"]


def test_valid_incoming_context_is_preserved() -> None:
    with app_client() as client:
        response = client.get(
            "/example",
            headers={"X-Request-ID": "request-abc", "X-Correlation-ID": "trace-xyz"},
        )
    assert response.headers["x-request-id"] == "request-abc"
    assert response.headers["x-correlation-id"] == "trace-xyz"


def test_invalid_header_value_is_replaced() -> None:
    with app_client() as client:
        response = client.get("/example", headers={"X-Request-ID": "bad value with spaces"})
    assert response.headers["x-request-id"] != "bad value with spaces"


def test_security_headers_are_present() -> None:
    with app_client() as client:
        response = client.get("/example")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert "default-src 'self'" in response.headers["content-security-policy"]
