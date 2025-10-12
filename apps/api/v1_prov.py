"""Provenance attestation endpoints."""
from __future__ import annotations

from fastapi import APIRouter

from apps.api.errors import capability_unavailable, runtime_error
from apps.api.schemas import (
    ProvenanceAttestRequest,
    ProvenanceAttestResponse,
    ProvenanceVerifyRequest,
    ProvenanceVerifyResponse,
)
from apps.runtime import local_handlers
from apps.runtime.exceptions import CapabilityUnavailable
from services.provenance.attestation import ProvenanceVerificationError

router = APIRouter(prefix="/v1/provenance", tags=["provenance"])


@router.post("/attest", response_model=ProvenanceAttestResponse)
def attest(request: ProvenanceAttestRequest) -> ProvenanceAttestResponse:
    try:
        return local_handlers.handle_provenance_attest(request)
    except CapabilityUnavailable as exc:
        raise capability_unavailable(exc)
    except Exception as exc:
        raise runtime_error(exc)


@router.post("/verify", response_model=ProvenanceVerifyResponse)
def verify(request: ProvenanceVerifyRequest) -> ProvenanceVerifyResponse:
    try:
        return local_handlers.handle_provenance_verify(request)
    except CapabilityUnavailable as exc:
        raise capability_unavailable(exc)
    except ProvenanceVerificationError as exc:
        raise runtime_error(exc)
    except Exception as exc:
        raise runtime_error(exc)


__all__ = ["router"]
