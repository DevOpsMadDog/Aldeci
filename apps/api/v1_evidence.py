"""Evidence bundling endpoint."""
from __future__ import annotations

from fastapi import APIRouter

from apps.api.errors import capability_unavailable, runtime_error
from apps.api.schemas import EvidenceBundleRequest, EvidenceBundleResponse
from apps.runtime import local_handlers
from apps.runtime.exceptions import CapabilityUnavailable

router = APIRouter(prefix="/v1/evidence", tags=["evidence"])


@router.post("/bundle", response_model=EvidenceBundleResponse)
def bundle(request: EvidenceBundleRequest) -> EvidenceBundleResponse:
    try:
        return local_handlers.handle_evidence_bundle(request)
    except CapabilityUnavailable as exc:
        raise capability_unavailable(exc)
    except Exception as exc:
        raise runtime_error(exc)


__all__ = ["router"]
