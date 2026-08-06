"""Backward-compatible health probe imports."""

from mailhub.core.health import ProbeResult, run_readiness_checks

__all__ = ["ProbeResult", "run_readiness_checks"]
