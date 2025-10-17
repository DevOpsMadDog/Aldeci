from __future__ import annotations

from fastapi import APIRouter

from apps.api.errors import capability_unavailable, runtime_error
from apps.api.schemas import (
    DecisionFuseRequest,
    DecisionFuseResponse,
    DecisionPropagateRequest,
    DecisionPropagateResponse,
)
from apps.runtime import local_handlers
from apps.runtime.exceptions import CapabilityUnavailable

router = APIRouter(prefix="/v1/decision", tags=["decision"])


@router.post("/fuse", response_model=DecisionFuseResponse)
def fuse(request: DecisionFuseRequest) -> DecisionFuseResponse:
    try:
        return local_handlers.handle_decision_fuse(request)
    except CapabilityUnavailable as exc:
        raise capability_unavailable(exc)
    except Exception as exc:
        raise runtime_error(exc)


@router.post("/propagate", response_model=DecisionPropagateResponse)
def propagate(request: DecisionPropagateRequest) -> DecisionPropagateResponse:
    try:
        return local_handlers.handle_decision_propagate(request)
    except CapabilityUnavailable as exc:
        raise capability_unavailable(exc)
    except Exception as exc:
        raise runtime_error(exc)


__all__ = ["router"]
