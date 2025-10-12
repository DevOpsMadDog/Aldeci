"""Custom runtime exceptions reused by CLI and API integrations."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class CapabilityUnavailable(Exception):
    """Raised when a capability is marked as unavailable in the execution map."""

    capability: str
    reason: str | None = None

    def __str__(self) -> str:  # pragma: no cover - human readable helper
        base = f"Capability '{self.capability}' is unavailable"
        if self.reason:
            return f"{base}: {self.reason}"
        return base


__all__ = ["CapabilityUnavailable"]
