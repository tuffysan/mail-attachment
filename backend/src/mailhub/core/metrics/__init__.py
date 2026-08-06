"""Minimal Prometheus-compatible application metrics."""

from mailhub.core.metrics.registry import metrics_registry

__all__ = ["metrics_registry"]
