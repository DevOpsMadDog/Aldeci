"""Persona explanation endpoint."""
from __future__ import annotations

from fastapi import APIRouter

from apps.api.errors import capability_unavailable, runtime_error
from apps.api.schemas import PersonaExplainRequest, PersonaExplainResponse
from apps.runtime import local_handlers
from apps.runtime.exceptions import CapabilityUnavailable

router = APIRouter(prefix="/v1/persona", tags=["persona"])


@router.post("/explain", response_model=PersonaExplainResponse)
def explain(request: PersonaExplainRequest) -> PersonaExplainResponse:
    try:
        return local_handlers.handle_persona_explain(request)
    except CapabilityUnavailable as exc:
        raise capability_unavailable(exc)
    except Exception as exc:
        raise runtime_error(exc)


__all__ = ["router"]
