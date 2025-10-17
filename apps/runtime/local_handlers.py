"""Local capability handlers used by both the CLI and HTTP layers."""
from __future__ import annotations

import base64
import json
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

import yaml

from apps.api.schemas import (
    DecisionFuseRequest,
    DecisionFuseResponse,
    DecisionPropagateRequest,
    DecisionPropagateResponse,
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
    PersonaExplainExtRequest,
    PersonaExplainExtResponse,
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
from core.configuration import load_overlay
from core.stage_runner import StageRunner
from services.evidence.packager import BundleInputs, create_bundle, evaluate_policy
from services.explainability import ExplainabilityService
from services.graph.graph import ProvenanceGraph
from services.id_allocator import ensure_ids
from services.provenance.attestation import (
    ProvenanceAttestation,
    generate_attestation,
    load_attestation,
    verify_attestation,
)
from services.risk.scoring import compute_risk_profile
from services.run_registry import RunRegistry
from services.signing import sign_manifest, verify_manifest
from apps.api.normalizers import InputNormalizer
from infra.feeds.epss import load_epss_scores
from infra.feeds.kev import load_kev_catalog
from services.score_ext import compute_bayesian_extension, propagate_risk_markov
from infra.llm_router_ext import explain_risk_ext


def _require_available(capability: str) -> Mapping[str, object]:
    entry = EXECUTION_REGISTRY.get(capability)
    if not entry or not entry.get("available"):
        reason = entry.get("reason") if entry else "Capability not registered"
        raise CapabilityUnavailable(capability, reason)
    return entry


def _decode_base64(payload: str) -> bytes:
    return base64.b64decode(payload.encode("utf-8"))


@dataclass(frozen=True)
class _StageRuntime:
    mode: str
    runner: StageRunner


class _AllocatorAdapter:
    def ensure_ids(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        return ensure_ids(payload)


class _SignerAdapter:
    def sign_manifest(self, manifest: Mapping[str, Any]) -> Mapping[str, Any]:
        return sign_manifest(manifest)

    def verify_manifest(
        self, manifest: Mapping[str, Any], envelope: Mapping[str, Any] | str | None
    ) -> bool:
        return verify_manifest(manifest, envelope)


@lru_cache(maxsize=8)
def _stage_runtime(overlay: str) -> _StageRuntime:
    overlay_file = Path("config") / f"overlay.{overlay}.yml"
    if not overlay_file.is_file():
        raise CapabilityUnavailable("stage.run", f"Overlay '{overlay}' not found")
    try:
        overlay_config = load_overlay(overlay_file, mode_override=overlay)
    except Exception as exc:  # pragma: no cover - validation guard
        raise CapabilityUnavailable("stage.run", f"Overlay load failed: {exc}") from exc

    storage_root = Path("artifacts") / "stage" / overlay
    storage_root.mkdir(parents=True, exist_ok=True)
    registry = RunRegistry(root=storage_root)
    runner = StageRunner(
        registry,
        _AllocatorAdapter(),
        _SignerAdapter(),
        normalizer=InputNormalizer(),
    )
    return _StageRuntime(mode=overlay_config.mode, runner=runner)


def _resolve_optional_path(value: Any) -> Path | None:
    if value is None:
        return None
    candidate = Path(str(value)).expanduser()
    return candidate


def _normalise_mapping(payload: Mapping[str, Any] | None) -> Dict[str, Any]:
    if not isinstance(payload, Mapping):
        return {}
    normalised: Dict[str, Any] = {}
    for key, value in payload.items():
        key_str = str(key)
        if isinstance(value, Mapping):
            normalised[key_str] = _normalise_mapping(value)
        elif isinstance(value, list):
            normalised[key_str] = [
                _normalise_mapping(item) if isinstance(item, Mapping) else item
                for item in value
            ]
        else:
            normalised[key_str] = value
    return normalised


def handle_stage_run(request: StageRunRequest) -> StageRunResponse:
    _require_available("stage.run")
    runtime = _stage_runtime(request.overlay)
    parameters = request.parameters or {}
    input_path = _resolve_optional_path(parameters.get("input"))
    if input_path is not None and not input_path.exists():
        raise CapabilityUnavailable(
            "stage.run", f"Input path '{input_path}' does not exist"
        )
    output_path = _resolve_optional_path(parameters.get("output"))
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)

    summary = runtime.runner.run_stage(
        request.stage,
        input_path,
        app_name=parameters.get("app_name"),
        app_id=parameters.get("app_id"),
        output_path=output_path,
        mode=runtime.mode,
        sign=bool(parameters.get("sign")),
        verify=bool(parameters.get("verify")),
        verbose=bool(parameters.get("verbose")),
    )

    response = StageRunResponse(
        message=f"Stage '{summary.stage}' completed for {summary.app_id}/{summary.run_id}",
        stage=summary.stage,
        app_id=summary.app_id,
        run_id=summary.run_id,
        output_file=str(summary.output_file),
        outputs_dir=str(summary.outputs_dir),
        signatures=[str(path) for path in summary.signatures],
        transparency_index=str(summary.transparency_index)
        if summary.transparency_index
        else None,
        bundle=str(summary.bundle) if summary.bundle else None,
        verified=summary.verified,
    )
    return response


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


def handle_decision_fuse(request: DecisionFuseRequest) -> DecisionFuseResponse:
    _require_available("decision.fuse")
    result = compute_bayesian_extension(request.normalized_sbom, request.risk_report)
    risk_ext = result.get("risk_ext") if isinstance(result, Mapping) else result
    return DecisionFuseResponse(risk_ext=risk_ext or {})


def handle_decision_propagate(
    request: DecisionPropagateRequest,
) -> DecisionPropagateResponse:
    _require_available("decision.propagate")
    result = propagate_risk_markov(
        request.graph,
        request.risk_ext,
        entry_nodes=request.entry_nodes or (),
        top_k_paths=request.top_k_paths,
    )
    risk_markov = result.get("risk_markov") if isinstance(result, Mapping) else result
    return DecisionPropagateResponse(risk_markov=risk_markov or {})


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


def handle_gate_check(request: GateCheckRequest) -> GateCheckResponse:
    _require_available("gate.check")
    policy = _normalise_mapping(request.policy)
    metrics = _normalise_mapping(request.metrics)
    evaluations = evaluate_policy(policy, metrics=metrics)
    checks = _normalise_mapping(evaluations.get("checks"))
    overall = str(evaluations.get("overall") or "unknown")
    message = f"Gate evaluation {overall}" if overall else "Gate evaluation completed"
    return GateCheckResponse(
        overall=overall,
        checks=checks,
        metrics=metrics,
        message=message,
    )


def _prime_explainability(service: ExplainabilityService, risk_report: Mapping[str, Any]) -> None:
    components = risk_report.get("components")
    if not isinstance(components, Iterable):
        return
    training_examples: list[Dict[str, float]] = []
    for component in components:
        if not isinstance(component, Mapping):
            continue
        entry: Dict[str, float] = {}
        risk_value = component.get("component_risk")
        if isinstance(risk_value, (int, float)):
            entry["component_risk"] = float(risk_value)
        vulnerabilities = component.get("vulnerabilities")
        if isinstance(vulnerabilities, Iterable):
            entry["vulnerability_count"] = float(len(list(vulnerabilities)))
        if entry:
            training_examples.append(entry)
    if training_examples:
        service.prime_baseline(training_examples)


def _persona_feature_vector(risk_report: Mapping[str, Any]) -> Dict[str, float]:
    summary = risk_report.get("summary") if isinstance(risk_report, Mapping) else {}
    if not isinstance(summary, Mapping):
        summary = {}
    feature_vector: Dict[str, float] = {}
    component_count = summary.get("component_count")
    cve_count = summary.get("cve_count")
    max_risk = summary.get("max_risk_score")
    if isinstance(component_count, (int, float)):
        feature_vector["component_count"] = float(component_count)
    if isinstance(cve_count, (int, float)):
        feature_vector["cve_count"] = float(cve_count)
    if isinstance(max_risk, (int, float)):
        feature_vector["max_risk_score"] = float(max_risk)
    return feature_vector


def _persona_highlights(
    role: str, contributions: Mapping[str, float], feature_vector: Mapping[str, float]
) -> List[str]:
    persona = role.lower()
    ordered = sorted(
        contributions.items(), key=lambda item: abs(item[1]), reverse=True
    )
    insights: List[str] = []
    if persona in {"ciso", "executive"}:
        count = int(feature_vector.get("component_count", 0))
        insights.append(f"Portfolio covers {count} components under active monitoring.")
    elif persona in {"developer", "engineer"}:
        insights.append(
            "Prioritise fixes for the components contributing the highest risk deltas."
        )
    else:
        cves = int(feature_vector.get("cve_count", 0))
        insights.append(f"Tracking {cves} CVEs across the service portfolio.")

    for feature, delta in ordered[:3]:
        direction = "increases" if delta > 0 else "reduces"
        insights.append(
            f"{feature.replace('_', ' ').title()} {direction} relative risk by {abs(delta):.2f}."
        )
    return insights[:3]


def handle_persona_explain(request: PersonaExplainRequest) -> PersonaExplainResponse:
    _require_available("persona.explain")
    risk_report = _normalise_mapping(request.risk_report)
    advisor = ExplainabilityService()
    _prime_explainability(advisor, risk_report)
    feature_vector = _persona_feature_vector(risk_report)
    contributions = advisor.explain(feature_vector)
    narrative = advisor.generate_narrative(feature_vector, contributions)
    highlights = _persona_highlights(request.role, contributions, feature_vector)
    context = {
        "summary": risk_report.get("summary", {}),
        "highest_risk_component": risk_report.get("summary", {}).get(
            "highest_risk_component"
        ),
    }
    return PersonaExplainResponse(
        persona=request.role.lower(),
        narrative=narrative,
        highlights=highlights,
        contributions=contributions,
        context=_normalise_mapping(context),
    )


def handle_persona_explain_ext(
    request: PersonaExplainExtRequest,
) -> PersonaExplainExtResponse:
    _require_available("persona.explain_ext")
    explanation = explain_risk_ext(request.risk_ext, request.role)
    return PersonaExplainExtResponse(
        persona=str(explanation.get("persona", request.role)).lower(),
        narrative=str(explanation.get("narrative", "")),
        rationale=list(explanation.get("rationale", [])),
        actions=list(explanation.get("actions", [])),
        highlights=list(explanation.get("highlights", [])),
        meta=_normalise_mapping(explanation.get("meta")),
        generated_at=str(explanation.get("generated_at")),
    )


__all__ = [
    "handle_evidence_bundle",
    "handle_gate_check",
    "handle_graph_anomalies",
    "handle_graph_kev",
    "handle_graph_lineage",
    "handle_ingest_sarif",
    "handle_ingest_sbom",
    "handle_decision_fuse",
    "handle_decision_propagate",
    "handle_persona_explain",
    "handle_persona_explain_ext",
    "handle_provenance_attest",
    "handle_provenance_verify",
    "handle_risk_score",
    "handle_stage_run",
]
