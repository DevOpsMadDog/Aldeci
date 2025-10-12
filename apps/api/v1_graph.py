"""Graph analysis endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Body

from apps.api.errors import capability_unavailable, runtime_error
from apps.api.schemas import (
    GraphAnomaliesRequest,
    GraphAnomaliesResponse,
    GraphKevRequest,
    GraphKevResponse,
    GraphLineageRequest,
    GraphLineageResponse,
)
from apps.runtime import local_handlers
from apps.runtime.exceptions import CapabilityUnavailable

router = APIRouter(prefix="/v1/graph", tags=["graph"])


@router.get("/lineage", response_model=GraphLineageResponse)
def lineage(request: GraphLineageRequest = Body(...)) -> GraphLineageResponse:
    try:
        return local_handlers.handle_graph_lineage(request)
    except CapabilityUnavailable as exc:
        raise capability_unavailable(exc)
    except Exception as exc:
        raise runtime_error(exc)


@router.get("/kev-in-last", response_model=GraphKevResponse)
def kev_in_last(request: GraphKevRequest = Body(...)) -> GraphKevResponse:
    try:
        return local_handlers.handle_graph_kev(request)
    except CapabilityUnavailable as exc:
        raise capability_unavailable(exc)
    except Exception as exc:
        raise runtime_error(exc)


@router.get("/anomalies", response_model=GraphAnomaliesResponse)
def anomalies(request: GraphAnomaliesRequest = Body(...)) -> GraphAnomaliesResponse:
    try:
        return local_handlers.handle_graph_anomalies(request)
    except CapabilityUnavailable as exc:
        raise capability_unavailable(exc)
    except Exception as exc:
        raise runtime_error(exc)


__all__ = ["router"]
