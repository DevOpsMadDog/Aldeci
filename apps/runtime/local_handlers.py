"""Local capability handlers used by both the CLI and HTTP layers."""
from __future__ import annotations

import base64
import json
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import List, Mapping

import yaml

from apps.api.schemas import (
    EvidenceBundleRequest,
    EvidenceBundleResponse,
    GateCheckRequest,
    GateCheckResponse,
    GraphAnomaliesRequest,
    GraphAnomaliesResponse,
    GraphKevRequest,
    GraphKevResponse,
    GraphLineageRequest,
    GraphLineageResponse,
    PersonaExplainRequest,
    PersonaExplainResponse,
    ProvenanceAttestRequest,
    ProvenanceAttestResponse,
    ProvenanceVerifyRequest,
    ProvenanceVerifyResponse,
    RiskScoreRequest,
    RiskScoreResponse,
    SarifIngestRequest,
    SarifIngestResponse,
    SbomIngestRequest,
    SbomIngestResponse,
    StageRunRequest,
    StageRunResponse,
)
from apps.registry.execution_map import EXECUTION_REGISTRY
from apps.runtime.exceptions import CapabilityUnavailable
from services.evidence.packager import BundleInputs, create_bundle
from services.graph.graph import ProvenanceGraph
from services.provenance.attestation import (
    ProvenanceAttestation,
    generate_attestation,
    load_attestation,
    verify_attestation,
)
from services.risk.scoring import compute_risk_profile
from services.normalize.normalizers import InputNormalizer
from infra.feeds.epss import load_epss_scores
from infra.feeds.kev import load_kev_catalog


def _require_available(capability: str) -> Mapping[str, object]:
    entry = EXECUTION_REGISTRY.get(capability)
    if not entry or not entry.get("available"):
        reason = entry.get("reason") if entry else "Capability not registered"
        raise CapabilityUnavailable(capability, reason)
    return entry


def _decode_base64(payload: str) -> bytes:
    return base64.b64decode(payload.encode("utf-8"))


def handle_stage_run(request: StageRunRequest) -> StageRunResponse:
    _require_available("stage.run")
    return StageRunResponse(message=f"Stage {request.stage} executed")


def handle_ingest_sbom(request: SbomIngestRequest) -> SbomIngestResponse:
    _require_available("ingest.sbom")
    normalizer = InputNormalizer(sbom_type=request.sbom_type or "auto")
    normalized = normalizer.load_sbom(request.content)
    return SbomIngestResponse(normalized=normalized.to_dict())


def handle_ingest_sarif(request: SarifIngestRequest) -> SarifIngestResponse:
    _require_available("ingest.sarif")
    normalizer = InputNormalizer()
    normalized = normalizer.load_sarif(request.content)
    return SarifIngestResponse(normalized=normalized.to_dict())


def handle_risk_score(request: RiskScoreRequest) -> RiskScoreResponse:
    _require_available("risk.score")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        epss_path = tmp_path / "epss.csv"
        epss_path.write_text(request.epss_csv, encoding="utf-8")
        kev_path = tmp_path / "kev.json"
        kev_path.write_text(request.kev_json, encoding="utf-8")
        epss_scores = load_epss_scores(path=epss_path)
        kev_entries = load_kev_catalog(path=kev_path)
    report = compute_risk_profile(
        request.normalized_sbom,
        epss_scores,
        kev_entries,
    )
    return RiskScoreResponse(report=report)


def handle_provenance_attest(
    request: ProvenanceAttestRequest,
) -> ProvenanceAttestResponse:
    _require_available("provenance.attest")
    artefact_bytes = _decode_base64(request.artifact_content)
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / request.artifact_name
        path.write_bytes(artefact_bytes)
        attestation = generate_attestation(
            path,
            builder_id=request.builder_id,
            source_uri=request.source_uri,
            build_type=request.build_type,
            materials=request.materials,
            metadata=request.metadata,
        )
    return ProvenanceAttestResponse(attestation=attestation.to_dict())


def handle_provenance_verify(
    request: ProvenanceVerifyRequest,
) -> ProvenanceVerifyResponse:
    _require_available("provenance.verify")
    artefact_bytes = _decode_base64(request.artifact_content)
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / request.artifact_name
        path.write_bytes(artefact_bytes)
        verify_attestation(
            request.attestation,
            artefact_path=path,
            builder_id=request.builder_id,
            source_uri=request.source_uri,
            build_type=request.build_type,
        )
    return ProvenanceVerifyResponse(verified=True)


@contextmanager
def _graph_from_payload(payload: GraphLineageRequest | GraphKevRequest | GraphAnomaliesRequest):
    graph = ProvenanceGraph()
    try:
        if payload.commits:
            graph.ingest_commits(list(payload.commits))
        if payload.attestations:
            attestations: List[ProvenanceAttestation] = [
                load_attestation(item) for item in payload.attestations
            ]
            graph.ingest_attestations(attestations)
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_root = Path(tmpdir)
            if payload.normalized_sbom is not None:
                normalized_path = temp_root / "normalized_sbom.json"
                normalized_path.write_text(
                    json.dumps(payload.normalized_sbom, indent=2),
                    encoding="utf-8",
                )
                graph.ingest_normalized_sbom(normalized_path)
            if payload.risk_report is not None:
                risk_path = temp_root / "risk_report.json"
                risk_path.write_text(
                    json.dumps(payload.risk_report, indent=2),
                    encoding="utf-8",
                )
                graph.ingest_risk_report(risk_path)
            if payload.releases is not None:
                releases_payload = payload.releases
                releases: List[Mapping[str, object]] = []
                if isinstance(releases_payload, Mapping):
                    entries = releases_payload.get("releases")
                    if isinstance(entries, list):
                        releases = [
                            entry for entry in entries if isinstance(entry, Mapping)
                        ]
                elif isinstance(releases_payload, list):
                    releases = [
                        entry for entry in releases_payload if isinstance(entry, Mapping)
                    ]
                graph.ingest_releases(releases)
        yield graph
    finally:
        graph.close()


def handle_graph_lineage(request: GraphLineageRequest) -> GraphLineageResponse:
    _require_available("graph.lineage")
    with _graph_from_payload(request) as graph:
        result = graph.lineage(request.artifact)
    return GraphLineageResponse(
        artifact=result.get("artifact", request.artifact),
        nodes=list(result.get("nodes", [])),
        edges=list(result.get("edges", [])),
    )


def handle_graph_kev(request: GraphKevRequest) -> GraphKevResponse:
    _require_available("graph.kev_in_last")
    with _graph_from_payload(request) as graph:
        results = graph.components_with_kev(request.releases_window)
    return GraphKevResponse(results=list(results))


def handle_graph_anomalies(request: GraphAnomaliesRequest) -> GraphAnomaliesResponse:
    _require_available("graph.anomalies")
    with _graph_from_payload(request) as graph:
        anomalies = graph.detect_version_anomalies()
    return GraphAnomaliesResponse(anomalies=list(anomalies))


def handle_evidence_bundle(
    request: EvidenceBundleRequest,
) -> EvidenceBundleResponse:
    _require_available("evidence.bundle")
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_root = Path(tmpdir)
        normalized_path = temp_root / "normalized_sbom.json"
        normalized_path.write_text(
            json.dumps(request.normalized_sbom, indent=2), encoding="utf-8"
        )
        quality_json_path = temp_root / "sbom_quality.json"
        quality_json_path.write_text(
            json.dumps(request.sbom_quality_json, indent=2), encoding="utf-8"
        )
        quality_html_path: Path | None = None
        if request.sbom_quality_html:
            quality_html_path = temp_root / "sbom_quality.html"
            quality_html_path.write_text(request.sbom_quality_html, encoding="utf-8")
        risk_path = temp_root / "risk_report.json"
        risk_path.write_text(json.dumps(request.risk_report, indent=2), encoding="utf-8")
        repro_path = temp_root / "repro_attestation.json"
        repro_path.write_text(
            json.dumps(request.repro_attestation, indent=2), encoding="utf-8"
        )
        provenance_dir = temp_root / "provenance"
        provenance_dir.mkdir(parents=True, exist_ok=True)
        for doc in request.provenance_files:
            file_path = provenance_dir / doc.name
            file_path.write_bytes(_decode_base64(doc.content))
        extra_dir = temp_root / "extra"
        extra_dir.mkdir(parents=True, exist_ok=True)
        extra_paths: List[Path] = []
        for doc in request.extra_files:
            file_path = extra_dir / doc.name
            file_path.write_bytes(_decode_base64(doc.content))
            extra_paths.append(file_path)
        policy_path: Path | None = None
        if request.policy is not None:
            policy_path = temp_root / "policy.yaml"
            policy_path.write_text(
                yaml.safe_dump(request.policy, sort_keys=False), encoding="utf-8"
            )
        sign_key_path: Path | None = None
        if request.sign_key:
            sign_key_path = temp_root / "cosign.key"
            sign_key_path.write_bytes(_decode_base64(request.sign_key))
        inputs = BundleInputs(
            tag=request.tag,
            normalized_sbom=normalized_path,
            sbom_quality_json=quality_json_path,
            sbom_quality_html=quality_html_path,
            risk_report=risk_path,
            provenance_dir=provenance_dir,
            repro_attestation=repro_path,
            policy_path=policy_path,
            output_dir=temp_root / "bundle_output",
            extra_paths=extra_paths,
            sign_key=sign_key_path,
        )
        manifest = create_bundle(inputs)
        bundle_path = Path(manifest.pop("bundle_path"))
        manifest_path = Path(manifest.pop("manifest_path"))
        bundle_bytes = bundle_path.read_bytes()
        manifest_content = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        manifest.update(manifest_content or {})
        bundle_name = bundle_path.name
        encoded_bundle = base64.b64encode(bundle_bytes).decode("utf-8")
    return EvidenceBundleResponse(
        bundle_name=bundle_name,
        bundle_content=encoded_bundle,
        manifest=manifest,
    )


def handle_gate_check(_: GateCheckRequest) -> GateCheckResponse:
    _require_available("gate.check")
    return GateCheckResponse(message="Gate evaluation completed")


def handle_persona_explain(_: PersonaExplainRequest) -> PersonaExplainResponse:
    _require_available("persona.explain")
    return PersonaExplainResponse(message="Persona explanation generated")


__all__ = [
    "handle_evidence_bundle",
    "handle_gate_check",
    "handle_graph_anomalies",
    "handle_graph_kev",
    "handle_graph_lineage",
    "handle_ingest_sarif",
    "handle_ingest_sbom",
    "handle_persona_explain",
    "handle_provenance_attest",
    "handle_provenance_verify",
    "handle_risk_score",
    "handle_stage_run",
]
