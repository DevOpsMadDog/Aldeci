"""Ingestion endpoints for SBOM and SARIF content."""
from __future__ import annotations

from fastapi import APIRouter

from apps.api.errors import capability_unavailable, runtime_error
from apps.api.schemas import (
    SarifIngestRequest,
    SarifIngestResponse,
    SbomIngestRequest,
    SbomIngestResponse,
)
from apps.runtime import local_handlers
from apps.runtime.exceptions import CapabilityUnavailable

router = APIRouter(prefix="/v1/ingest", tags=["ingest"])


@router.post("/sbom", response_model=SbomIngestResponse)
def ingest_sbom(request: SbomIngestRequest) -> SbomIngestResponse:
    try:
        return local_handlers.handle_ingest_sbom(request)
    except CapabilityUnavailable as exc:
        raise capability_unavailable(exc)
    except Exception as exc:
        raise runtime_error(exc)


@router.post("/sarif", response_model=SarifIngestResponse)
def ingest_sarif(request: SarifIngestRequest) -> SarifIngestResponse:
    try:
        return local_handlers.handle_ingest_sarif(request)
    except CapabilityUnavailable as exc:
        raise capability_unavailable(exc)
    except Exception as exc:
        raise runtime_error(exc)


__all__ = ["router"]
