"""Risk scoring endpoint."""
from __future__ import annotations

from fastapi import APIRouter

from apps.api.errors import capability_unavailable, runtime_error
from apps.api.schemas import RiskScoreRequest, RiskScoreResponse
from apps.runtime import local_handlers
from apps.runtime.exceptions import CapabilityUnavailable

router = APIRouter(prefix="/v1/risk", tags=["risk"])


@router.post("/score", response_model=RiskScoreResponse)
def score(request: RiskScoreRequest) -> RiskScoreResponse:
    try:
        return local_handlers.handle_risk_score(request)
    except CapabilityUnavailable as exc:
        raise capability_unavailable(exc)
    except Exception as exc:
        raise runtime_error(exc)


__all__ = ["router"]
