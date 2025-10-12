"""Policy gate endpoint."""
from __future__ import annotations

from fastapi import APIRouter

from apps.api.errors import capability_unavailable, runtime_error
from apps.api.schemas import GateCheckRequest, GateCheckResponse
from apps.runtime import local_handlers
from apps.runtime.exceptions import CapabilityUnavailable

router = APIRouter(prefix="/v1/gate", tags=["gate"])


@router.post("/check", response_model=GateCheckResponse)
def check(request: GateCheckRequest) -> GateCheckResponse:
    try:
        return local_handlers.handle_gate_check(request)
    except CapabilityUnavailable as exc:
        raise capability_unavailable(exc)
    except Exception as exc:
        raise runtime_error(exc)


__all__ = ["router"]
