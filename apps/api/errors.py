"""Common error helpers for FastAPI handlers."""
from __future__ import annotations

from fastapi import HTTPException, status

from apps.runtime.exceptions import CapabilityUnavailable


def capability_unavailable(exc: CapabilityUnavailable) -> HTTPException:
    """Translate a capability gap into an HTTP 501 response."""

    return HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={"capability": exc.capability, "reason": exc.reason},
    )


def runtime_error(exc: Exception) -> HTTPException:
    """Wrap unexpected runtime failures in a 400 response."""

    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


__all__ = ["capability_unavailable", "runtime_error"]
