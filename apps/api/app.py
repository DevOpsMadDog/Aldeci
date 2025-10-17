"""FastAPI application exposing the FixOps capability surface."""
from __future__ import annotations

from fastapi import FastAPI

from apps.api import (
    v1_decision,
    v1_evidence,
    v1_gate,
    v1_graph,
    v1_ingest,
    v1_persona,
    v1_prov,
    v1_risk,
    v1_stage,
)


def create_app() -> FastAPI:
    app = FastAPI(title="AlDeci FixOps API", version="0.1.0")
    app.include_router(v1_stage.router)
    app.include_router(v1_ingest.router)
    app.include_router(v1_risk.router)
    app.include_router(v1_prov.router)
    app.include_router(v1_graph.router)
    app.include_router(v1_evidence.router)
    app.include_router(v1_gate.router)
    app.include_router(v1_persona.router)
    app.include_router(v1_decision.router)
    return app


app = create_app()

__all__ = ["app", "create_app"]
