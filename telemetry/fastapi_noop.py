# ----------------------------------------
# Sourced from FixOps (4ffd8dd1f6186ca5fb082e4d674e5e7f01f5db78)
# ----------------------------------------
"""No-op FastAPI instrumentor for environments without OpenTelemetry packages."""

from __future__ import annotations


class FastAPIInstrumentor:  # pragma: no cover - simple shim
    @staticmethod
    def instrument_app(*_args, **_kwargs) -> None:
        return None
