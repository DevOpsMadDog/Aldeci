"""HTTP client for interacting with the AlDeci FixOps API."""
from __future__ import annotations

import os
from typing import Any, Dict, Type, TypeVar

import httpx
from pydantic import BaseModel

from apps.api import schemas

T = TypeVar("T", bound=BaseModel)


class FixopsAPIError(Exception):
    """Raised when the API responds with an error payload."""

    def __init__(self, status_code: int, detail: Any) -> None:
        self.status_code = status_code
        self.detail = detail
        message = f"HTTP {status_code}: {detail}" if status_code else str(detail)
        super().__init__(message)


class FixopsClient:
    """Small httpx-based client with retry support."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float = 30.0,
        retries: int = 3,
    ) -> None:
        self.base_url = base_url or os.environ.get("FIXOPS_BASE_URL", "http://127.0.0.1:8000")
        self.api_key = api_key or os.environ.get("FIXOPS_API_KEY")
        self.timeout = timeout
        self.retries = max(1, retries)
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout,
            headers=self._default_headers(),
        )

    def _default_headers(self) -> Dict[str, str]:
        headers = {"User-Agent": "aldecI-sdk/0.1"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "FixopsClient":  # pragma: no cover - convenience helper
        return self

    def __exit__(self, *_: object) -> None:  # pragma: no cover - convenience helper
        self.close()

    def _request(
        self,
        method: str,
        path: str,
        *,
        json_payload: Dict[str, Any] | None = None,
    ) -> httpx.Response:
        last_exc: Exception | None = None
        for attempt in range(self.retries):
            try:
                response = self._client.request(method, path, json=json_payload)
                if response.status_code >= 400:
                    detail: Any
                    try:
                        detail = response.json()
                    except ValueError:
                        detail = response.text
                    raise FixopsAPIError(response.status_code, detail)
                return response
            except httpx.HTTPError as exc:
                last_exc = exc
        raise FixopsAPIError(0, last_exc or "HTTP request failed")

    @staticmethod
    def _dump(payload: BaseModel | Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(payload, BaseModel):
            return payload.model_dump()
        return dict(payload)

    @staticmethod
    def _load(model: Type[T], response: httpx.Response) -> T:
        return model.model_validate(response.json())

    # ------------------------------------------------------------------
    # Capability specific methods
    def stage_run(self, request: schemas.StageRunRequest) -> schemas.StageRunResponse:
        response = self._request("POST", "/v1/stage/run", json_payload=self._dump(request))
        return self._load(schemas.StageRunResponse, response)

    def ingest_sbom(self, request: schemas.SbomIngestRequest) -> schemas.SbomIngestResponse:
        response = self._request("POST", "/v1/ingest/sbom", json_payload=self._dump(request))
        return self._load(schemas.SbomIngestResponse, response)

    def ingest_sarif(self, request: schemas.SarifIngestRequest) -> schemas.SarifIngestResponse:
        response = self._request("POST", "/v1/ingest/sarif", json_payload=self._dump(request))
        return self._load(schemas.SarifIngestResponse, response)

    def risk_score(self, request: schemas.RiskScoreRequest) -> schemas.RiskScoreResponse:
        response = self._request("POST", "/v1/risk/score", json_payload=self._dump(request))
        return self._load(schemas.RiskScoreResponse, response)

    def provenance_attest(
        self, request: schemas.ProvenanceAttestRequest
    ) -> schemas.ProvenanceAttestResponse:
        response = self._request("POST", "/v1/provenance/attest", json_payload=self._dump(request))
        return self._load(schemas.ProvenanceAttestResponse, response)

    def provenance_verify(
        self, request: schemas.ProvenanceVerifyRequest
    ) -> schemas.ProvenanceVerifyResponse:
        response = self._request("POST", "/v1/provenance/verify", json_payload=self._dump(request))
        return self._load(schemas.ProvenanceVerifyResponse, response)

    def graph_lineage(
        self, request: schemas.GraphLineageRequest
    ) -> schemas.GraphLineageResponse:
        response = self._request(
            "POST", "/v1/graph/lineage", json_payload=self._dump(request)
        )
        return self._load(schemas.GraphLineageResponse, response)

    def graph_kev(self, request: schemas.GraphKevRequest) -> schemas.GraphKevResponse:
        response = self._request(
            "POST", "/v1/graph/kev-in-last", json_payload=self._dump(request)
        )
        return self._load(schemas.GraphKevResponse, response)

    def graph_anomalies(
        self, request: schemas.GraphAnomaliesRequest
    ) -> schemas.GraphAnomaliesResponse:
        response = self._request(
            "POST", "/v1/graph/anomalies", json_payload=self._dump(request)
        )
        return self._load(schemas.GraphAnomaliesResponse, response)

    def evidence_bundle(
        self, request: schemas.EvidenceBundleRequest
    ) -> schemas.EvidenceBundleResponse:
        response = self._request("POST", "/v1/evidence/bundle", json_payload=self._dump(request))
        return self._load(schemas.EvidenceBundleResponse, response)

    def gate_check(self, request: schemas.GateCheckRequest) -> schemas.GateCheckResponse:
        response = self._request("POST", "/v1/gate/check", json_payload=self._dump(request))
        return self._load(schemas.GateCheckResponse, response)

    def persona_explain(
        self, request: schemas.PersonaExplainRequest
    ) -> schemas.PersonaExplainResponse:
        response = self._request("POST", "/v1/persona/explain", json_payload=self._dump(request))
        return self._load(schemas.PersonaExplainResponse, response)


__all__ = ["FixopsClient", "FixopsAPIError"]
