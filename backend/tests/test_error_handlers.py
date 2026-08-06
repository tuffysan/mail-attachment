import logging

from fastapi import FastAPI
from fastapi.testclient import TestClient

from mailhub.core.errors import NotFoundError, install_exception_handlers
from mailhub.core.middleware import RequestContextMiddleware


def create_app() -> FastAPI:
    app = FastAPI()
    install_exception_handlers(app)
    app.add_middleware(RequestContextMiddleware)

    @app.get("/expected")
    async def expected() -> None:
        raise NotFoundError("Mailbox was not found", code="mailbox_not_found")

    @app.get("/unexpected")
    async def unexpected() -> None:
        raise RuntimeError("database password must never be exposed")

    @app.get("/items/{item_id}")
    async def item(item_id: int) -> dict[str, int]:
        return {"item_id": item_id}

    return app


def test_application_error_uses_problem_details() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/expected", headers={"X-Request-ID": "request-123"})

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json() == {
        "type": "about:blank",
        "title": "Resource not found",
        "status": 404,
        "detail": "Mailbox was not found",
        "instance": "/expected",
        "code": "mailbox_not_found",
        "request_id": "request-123",
    }


def test_validation_error_is_machine_readable() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/items/not-an-integer")

    payload = response.json()
    assert response.status_code == 422
    assert payload["code"] == "request_validation_error"
    assert payload["errors"][0]["location"] == ["path", "item_id"]
    assert payload["request_id"]


def test_unhandled_error_does_not_leak_internal_message(
    caplog,
) -> None:
    caplog.set_level(logging.ERROR)
    with TestClient(create_app(), raise_server_exceptions=False) as client:
        response = client.get("/unexpected")

    payload = response.json()
    assert response.status_code == 500
    assert payload["code"] == "internal_server_error"
    assert "database password" not in response.text
    assert payload["request_id"]
    assert "unhandled_request_error" in caplog.text


def test_unknown_route_uses_problem_details() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/missing")

    assert response.status_code == 404
    assert response.json()["code"] == "http_404"
