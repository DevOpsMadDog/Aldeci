"""Stage related API handlers."""
from __future__ import annotations

from fastapi import APIRouter

from apps.api.errors import capability_unavailable
from apps.api.schemas import StageRunRequest, StageRunResponse
from apps.runtime.exceptions import CapabilityUnavailable
from apps.runtime import local_handlers

router = APIRouter(prefix="/v1/stage", tags=["stage"])


@router.post("/run", response_model=StageRunResponse)
def run_stage(request: StageRunRequest) -> StageRunResponse:
    try:
        return local_handlers.handle_stage_run(request)
    except CapabilityUnavailable as exc:
        raise capability_unavailable(exc)


__all__ = ["router"]
