import threading
import time
from collections import defaultdict


class MetricsRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._request_count: dict[tuple[str, str, int], int] = defaultdict(int)
        self._request_duration_sum: dict[tuple[str, str], float] = defaultdict(float)
        self._request_duration_count: dict[tuple[str, str], int] = defaultdict(int)
        self._started_at = time.time()

    def observe_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_seconds: float,
    ) -> None:
        key = (method, path, status_code)
        duration_key = (method, path)
        with self._lock:
            self._request_count[key] += 1
            self._request_duration_sum[duration_key] += duration_seconds
            self._request_duration_count[duration_key] += 1

    @staticmethod
    def _label(value: str) -> str:
        return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")

    def render(self) -> str:
        lines = [
            "# HELP mailhub_process_uptime_seconds Process uptime in seconds.",
            "# TYPE mailhub_process_uptime_seconds gauge",
            f"mailhub_process_uptime_seconds {time.time() - self._started_at:.3f}",
            "# HELP mailhub_http_requests_total Total HTTP requests.",
            "# TYPE mailhub_http_requests_total counter",
        ]
        with self._lock:
            for (method, path, status), value in sorted(self._request_count.items()):
                lines.append(
                    'mailhub_http_requests_total'
                    f'{{method="{self._label(method)}",path="{self._label(path)}",status="{status}"}} {value}'
                )
            lines.extend(
                [
                    "# HELP mailhub_http_request_duration_seconds_sum "
                    "Accumulated HTTP request duration.",
                    "# TYPE mailhub_http_request_duration_seconds_sum counter",
                ]
            )
            for (method, path), value in sorted(self._request_duration_sum.items()):
                lines.append(
                    'mailhub_http_request_duration_seconds_sum'
                    f'{{method="{self._label(method)}",path="{self._label(path)}"}} {value:.6f}'
                )
            lines.extend(
                [
                    "# HELP mailhub_http_request_duration_seconds_count "
                    "Observed HTTP request count for duration metrics.",
                    "# TYPE mailhub_http_request_duration_seconds_count counter",
                ]
            )
            for (method, path), value in sorted(self._request_duration_count.items()):
                lines.append(
                    'mailhub_http_request_duration_seconds_count'
                    f'{{method="{self._label(method)}",path="{self._label(path)}"}} {value}'
                )
        return "\n".join(lines) + "\n"

    def reset(self) -> None:
        with self._lock:
            self._request_count.clear()
            self._request_duration_sum.clear()
            self._request_duration_count.clear()
            self._started_at = time.time()


metrics_registry = MetricsRegistry()
