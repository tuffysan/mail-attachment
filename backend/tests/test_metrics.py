from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.responses import PlainTextResponse

from mailhub.core.metrics import metrics_registry
from mailhub.core.middleware import RequestContextMiddleware


def test_request_metrics_are_prometheus_compatible() -> None:
    metrics_registry.reset()
    app = FastAPI()
    app.add_middleware(RequestContextMiddleware)

    @app.get("/hello")
    async def hello() -> dict[str, str]:
        return {"hello": "world"}

    @app.get("/metrics", response_class=PlainTextResponse)
    async def metrics() -> PlainTextResponse:
        return PlainTextResponse(metrics_registry.render())

    with TestClient(app) as client:
        assert client.get("/hello").status_code == 200
        response = client.get("/metrics")

    body = response.text
    assert "mailhub_process_uptime_seconds" in body
    assert 'mailhub_http_requests_total{method="GET",path="/hello",status="200"} 1' in body
    assert "mailhub_http_request_duration_seconds_sum" in body
    assert "mailhub_http_request_duration_seconds_count" in body
