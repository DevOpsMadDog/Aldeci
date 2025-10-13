"""Shared Pydantic schemas for the /v1 FastAPI surface and CLI interoperability."""
from __future__ import annotations

from typing import Any, Dict, List, Mapping

from pydantic import BaseModel, Field


class StageRunRequest(BaseModel):
    stage: str = Field(..., description="Name of the SDLC stage to execute.")
    overlay: str = Field(..., description="Overlay to execute against (demo|enterprise).")
    parameters: Dict[str, Any] | None = Field(
        default=None,
        description="Optional stage parameters or overrides.",
    )


class StageRunResponse(BaseModel):
    message: str
    stage: str
    app_id: str
    run_id: str
    output_file: str
    outputs_dir: str
    signatures: List[str] = Field(default_factory=list)
    transparency_index: str | None = None
    bundle: str | None = None
    verified: bool | None = None


class SbomIngestRequest(BaseModel):
    content: str = Field(..., description="Raw SBOM document content.")
    sbom_type: str | None = Field(
        default="auto",
        description="Preferred SBOM format hint passed to lib4sbom.",
    )
    overlay: str = Field(..., description="Overlay requested by the caller.")


class SbomIngestResponse(BaseModel):
    normalized: Dict[str, Any]


class SarifIngestRequest(BaseModel):
    content: str = Field(..., description="SARIF log content to normalise.")
    overlay: str = Field(..., description="Overlay requested by the caller.")


class SarifIngestResponse(BaseModel):
    normalized: Dict[str, Any]


class RiskScoreRequest(BaseModel):
    normalized_sbom: Mapping[str, Any] = Field(
        ..., description="Pre-normalised SBOM used to derive risk metrics."
    )
    epss_csv: str = Field(..., description="EPSS CSV payload to load into memory.")
    kev_json: str = Field(..., description="KEV JSON payload to load into memory.")
    overlay: str = Field(..., description="Overlay requested by the caller.")


class RiskScoreResponse(BaseModel):
    report: Dict[str, Any]


class BinaryDocument(BaseModel):
    name: str
    content: str = Field(..., description="Base64 encoded bytes.")
    media_type: str | None = Field(
        default=None, description="Optional media type hint (for documentation)."
    )


class ProvenanceAttestRequest(BaseModel):
    artifact_name: str = Field(..., description="Display name for the artefact.")
    artifact_content: str = Field(..., description="Base64 encoded artefact bytes.")
    builder_id: str = Field(
        default="aldecI/builders/default",
        description="Builder identifier recorded in the attestation.",
    )
    source_uri: str = Field(
        default="https://example.com/repo",
        description="Source repository URI associated with the build.",
    )
    build_type: str = Field(
        default="https://fixops.dev/attestation/default",
        description="SLSA build type URI.",
    )
    materials: List[Mapping[str, Any]] | None = Field(
        default=None,
        description="Optional list of materials consumed during the build.",
    )
    metadata: Mapping[str, Any] | None = Field(
        default=None,
        description="Optional metadata block to merge into the attestation.",
    )
    overlay: str = Field(..., description="Overlay requested by the caller.")


class ProvenanceAttestResponse(BaseModel):
    attestation: Dict[str, Any]


class ProvenanceVerifyRequest(BaseModel):
    artifact_name: str
    artifact_content: str
    attestation: Mapping[str, Any]
    builder_id: str | None = None
    source_uri: str | None = None
    build_type: str | None = None
    overlay: str = Field(..., description="Overlay requested by the caller.")


class ProvenanceVerifyResponse(BaseModel):
    verified: bool


class GraphPayload(BaseModel):
    commits: List[Mapping[str, Any]] = Field(default_factory=list)
    attestations: List[Mapping[str, Any]] = Field(default_factory=list)
    normalized_sbom: Mapping[str, Any] | None = None
    risk_report: Mapping[str, Any] | None = None
    releases: Mapping[str, Any] | List[Mapping[str, Any]] | None = None
    overlay: str = Field(..., description="Overlay requested by the caller.")


class GraphLineageRequest(GraphPayload):
    artifact: str = Field(..., description="Artifact identifier or name to analyse.")


class GraphLineageResponse(BaseModel):
    artifact: str
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


class GraphKevRequest(GraphPayload):
    releases_window: int = Field(1, description="Number of releases to include.")


class GraphKevResponse(BaseModel):
    results: List[Dict[str, Any]]


class GraphAnomaliesRequest(GraphPayload):
    pass


class GraphAnomaliesResponse(BaseModel):
    anomalies: List[Dict[str, Any]]


class EvidenceBundleRequest(BaseModel):
    tag: str = Field(..., description="Release identifier used for bundle naming.")
    normalized_sbom: Mapping[str, Any]
    sbom_quality_json: Mapping[str, Any]
    sbom_quality_html: str | None = None
    risk_report: Mapping[str, Any]
    repro_attestation: Mapping[str, Any]
    provenance_files: List[BinaryDocument] = Field(default_factory=list)
    extra_files: List[BinaryDocument] = Field(default_factory=list)
    policy: Mapping[str, Any] | None = None
    sign_key: str | None = Field(
        default=None, description="Base64 encoded cosign private key (optional)."
    )
    overlay: str = Field(..., description="Overlay requested by the caller.")


class EvidenceBundleResponse(BaseModel):
    bundle_name: str
    bundle_content: str = Field(..., description="Base64 encoded ZIP archive bytes.")
    manifest: Dict[str, Any]


class GateCheckRequest(BaseModel):
    policy: Mapping[str, Any]
    metrics: Mapping[str, Any] | None = None
    overlay: str


class GateCheckResponse(BaseModel):
    overall: str
    checks: Dict[str, Any]
    metrics: Dict[str, Any]
    message: str


class PersonaExplainRequest(BaseModel):
    role: str
    risk_report: Mapping[str, Any]
    overlay: str


class PersonaExplainResponse(BaseModel):
    persona: str
    narrative: str
    highlights: List[str]
    contributions: Dict[str, float]
    context: Dict[str, Any]


__all__ = [
    "BinaryDocument",
    "EvidenceBundleRequest",
    "EvidenceBundleResponse",
    "GateCheckRequest",
    "GateCheckResponse",
    "GraphAnomaliesRequest",
    "GraphAnomaliesResponse",
    "GraphKevRequest",
    "GraphKevResponse",
    "GraphLineageRequest",
    "GraphLineageResponse",
    "PersonaExplainRequest",
    "PersonaExplainResponse",
    "ProvenanceAttestRequest",
    "ProvenanceAttestResponse",
    "ProvenanceVerifyRequest",
    "ProvenanceVerifyResponse",
    "RiskScoreRequest",
    "RiskScoreResponse",
    "SarifIngestRequest",
    "SarifIngestResponse",
    "SbomIngestRequest",
    "SbomIngestResponse",
    "StageRunRequest",
    "StageRunResponse",
]
