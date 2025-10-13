"""Unified AlDeci CLI capable of targeting local or HTTP backends."""
from __future__ import annotations

import base64
import json
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Iterable, List, Optional, cast

import typer
import yaml

from apps.api.schemas import (
    EvidenceBundleRequest,
    GateCheckRequest,
    GraphAnomaliesRequest,
    GraphKevRequest,
    GraphLineageRequest,
    PersonaExplainRequest,
    ProvenanceAttestRequest,
    ProvenanceVerifyRequest,
    RiskScoreRequest,
    SarifIngestRequest,
    SbomIngestRequest,
    StageRunRequest,
)
from apps.runtime.exceptions import CapabilityUnavailable
from apps.runtime import local_handlers
from sdk.python.fixops_client import FixopsAPIError, FixopsClient

app = typer.Typer(help="AlDeci control surface")
stage_app = typer.Typer(help="Stage orchestration commands")
ingest_app = typer.Typer(help="Ingestion helpers")
prov_app = typer.Typer(help="Provenance utilities")
graph_app = typer.Typer(help="Graph analytics")
risk_app = typer.Typer(help="Risk scoring")
evidence_app = typer.Typer(help="Evidence packaging")
persona_app = typer.Typer(help="Persona narratives")
app.add_typer(stage_app, name="stage")
app.add_typer(ingest_app, name="ingest")
app.add_typer(prov_app, name="prov")
app.add_typer(graph_app, name="graph")
app.add_typer(risk_app, name="risk")
app.add_typer(evidence_app, name="evidence")
app.add_typer(persona_app, name="persona")


class Backend(str, Enum):
    LOCAL = "local"
    HTTP = "http"


class Overlay(str, Enum):
    DEMO = "demo"
    ENTERPRISE = "enterprise"


class Stage(str, Enum):
    REQUIREMENTS = "requirements"
    DESIGN = "design"
    BUILD = "build"
    TEST = "test"
    DEPLOY = "deploy"
    OPERATE = "operate"
    DECISION = "decision"


@dataclass
class CLIContext:
    backend: Backend
    overlay: Overlay
    client: FixopsClient | None = None


def _base64_file(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("utf-8")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _collect_attestations(paths: Iterable[Path]) -> List[dict[str, Any]]:
    attestations: List[dict[str, Any]] = []
    for path in paths:
        if not path.exists():
            continue
        if path.is_dir():
            for candidate in sorted(path.glob("*.json")):
                attestations.append(_read_json(candidate))
        elif path.is_file():
            attestations.append(_read_json(path))
    return attestations


def _collect_commits(path: Optional[Path]) -> List[dict[str, Any]]:
    if not path:
        return []
    if not path.exists():
        return []
    from services.graph.graph import collect_git_history

    return collect_git_history(path)


def _collect_files(path: Optional[Path]) -> List[Path]:
    if not path or not path.exists():
        return []
    files: List[Path] = []
    for candidate in sorted(path.rglob("*")):
        if candidate.is_file():
            files.append(candidate)
    return files


def _echo_json(payload: Any) -> None:
    if hasattr(payload, 'model_dump'):
        payload = payload.model_dump()
    elif hasattr(payload, 'dict'):
        payload = payload.dict()
    typer.echo(json.dumps(payload, sort_keys=True))


def _print_unavailable(capability: str, reason: str | None) -> None:
    message = f"Unavailable: missing upstream capability ({reason})" if reason else (
        "Unavailable: missing upstream capability"
    )
    typer.secho(message, fg=typer.colors.YELLOW)


def _dispatch(
    cli_ctx: CLIContext,
    capability: str,
    request: Any,
    local_handler: Callable[[Any], Any],
    remote_handler: Callable[[FixopsClient, Any], Any],
) -> Any:
    if cli_ctx.backend == Backend.LOCAL:
        try:
            return local_handler(request)
        except CapabilityUnavailable as exc:
            _print_unavailable(capability, exc.reason)
            raise typer.Exit(code=12)
        except Exception as exc:  # pragma: no cover - surfaced as CLI failure
            typer.secho(str(exc), fg=typer.colors.RED)
            raise typer.Exit(code=1)
    client = cli_ctx.client
    assert client is not None, "HTTP backend requires a client"
    try:
        return remote_handler(client, request)
    except FixopsAPIError as exc:
        if exc.status_code == 501:
            detail = exc.detail
            reason = detail.get("reason") if isinstance(detail, dict) else str(detail)
            _print_unavailable(capability, reason)
            raise typer.Exit(code=12)
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1)


@app.callback()
def main(
    ctx: typer.Context,
    backend: Backend = typer.Option(Backend.LOCAL, help="Execution backend to target."),
    overlay: Overlay = typer.Option(Overlay.DEMO, help="Overlay configuration to apply."),
    api_base_url: str | None = typer.Option(
        None,
        help="Override the API base URL when using the HTTP backend.",
    ),
) -> None:
    client: FixopsClient | None = None
    if backend == Backend.HTTP:
        client = FixopsClient(base_url=api_base_url)
    ctx.obj = CLIContext(backend=backend, overlay=overlay, client=client)


@stage_app.command("run")
def stage_run(
    typer_ctx: typer.Context,
    stage: Stage = typer.Option(..., help="Stage to execute"),
    input_path: Path | None = typer.Option(
        None,
        "--input",
        help="Optional input artefact for the selected stage.",
    ),
    output_path: Path | None = typer.Option(
        None,
        "--output",
        help="Optional destination for the canonical stage output.",
    ),
    app_id: str | None = typer.Option(None, help="Override the application identifier."),
    app_name: str | None = typer.Option(None, help="Override the application display name."),
    sign: bool = typer.Option(False, help="Request manifest signing for this run."),
    verify: bool = typer.Option(
        False, help="Verify signatures when signing is requested."
    ),
    verbose: bool = typer.Option(False, help="Enable verbose stage runner output."),
) -> None:
    ctx = cast(CLIContext, typer_ctx.obj)
    parameters: dict[str, Any] = {}
    if input_path is not None:
        parameters["input"] = str(input_path)
    if output_path is not None:
        parameters["output"] = str(output_path)
    if app_id:
        parameters["app_id"] = app_id
    if app_name:
        parameters["app_name"] = app_name
    if sign:
        parameters["sign"] = True
    if verify:
        parameters["verify"] = True
    if verbose:
        parameters["verbose"] = True

    request = StageRunRequest(
        stage=stage.value,
        overlay=ctx.overlay.value,
        parameters=parameters or None,
    )
    response = _dispatch(
        ctx,
        "stage.run",
        request,
        local_handlers.handle_stage_run,
        lambda client, payload: client.stage_run(payload),
    )
    typer.echo(response.message)
    _echo_json(response)


@ingest_app.command("sbom")
def ingest_sbom(
    typer_ctx: typer.Context,
    in_path: Path = typer.Option(
        ..., "--in", help="Path to SBOM document", exists=True, dir_okay=False
    ),
    out_path: Path = typer.Option(
        Path("artifacts/sbom/normalized.json"),
        "--out",
        help="Destination for normalized SBOM",
    ),
    sbom_type: str = typer.Option("auto", help="SBOM type hint"),
) -> None:
    ctx = cast(CLIContext, typer_ctx.obj)
    content = in_path.read_text(encoding="utf-8")
    request = SbomIngestRequest(content=content, sbom_type=sbom_type, overlay=ctx.overlay.value)
    response = _dispatch(
        ctx,
        "ingest.sbom",
        request,
        local_handlers.handle_ingest_sbom,
        lambda client, payload: client.ingest_sbom(payload),
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(response.normalized, indent=2), encoding="utf-8")
    typer.echo(f"Normalized SBOM written to {out_path}")


@ingest_app.command("sarif")
def ingest_sarif(
    typer_ctx: typer.Context,
    in_path: Path = typer.Option(
        ..., "--in", help="Path to SARIF log", exists=True, dir_okay=False
    ),
    out_path: Path = typer.Option(
        Path("artifacts/sarif/normalized.json"),
        "--out",
        help="Destination for normalized SARIF",
    ),
) -> None:
    ctx = cast(CLIContext, typer_ctx.obj)
    content = in_path.read_text(encoding="utf-8")
    request = SarifIngestRequest(content=content, overlay=ctx.overlay.value)
    response = _dispatch(
        ctx,
        "ingest.sarif",
        request,
        local_handlers.handle_ingest_sarif,
        lambda client, payload: client.ingest_sarif(payload),
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(response.normalized, indent=2), encoding="utf-8")
    typer.echo(f"Normalized SARIF written to {out_path}")


@risk_app.command("score")
def risk_score(
    typer_ctx: typer.Context,
    sbom_path: Path = typer.Option(
        ..., "--sbom", help="Normalized SBOM JSON", exists=True, dir_okay=False
    ),
    epss_path: Path = typer.Option(
        ..., "--epss", help="EPSS CSV feed", exists=True, dir_okay=False
    ),
    kev_path: Path = typer.Option(
        ..., "--kev", help="KEV JSON feed", exists=True, dir_okay=False
    ),
    out_path: Path = typer.Option(
        Path("artifacts/risk.json"), "--out", help="Destination for risk report"
    ),
) -> None:
    ctx = cast(CLIContext, typer_ctx.obj)
    request = RiskScoreRequest(
        normalized_sbom=_read_json(sbom_path),
        epss_csv=epss_path.read_text(encoding="utf-8"),
        kev_json=kev_path.read_text(encoding="utf-8"),
        overlay=ctx.overlay.value,
    )
    response = _dispatch(
        ctx,
        "risk.score",
        request,
        local_handlers.handle_risk_score,
        lambda client, payload: client.risk_score(payload),
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(response.report, indent=2), encoding="utf-8")
    typer.echo(f"Risk report written to {out_path}")


@prov_app.command("attest")
def provenance_attest(
    typer_ctx: typer.Context,
    artifact: Path = typer.Option(..., help="Artefact to attest", exists=True, dir_okay=False),
    out_path: Path = typer.Option(
        Path("artifacts/attestations/attestation.json"),
        "--out",
        help="Destination for generated attestation",
    ),
    builder: str = typer.Option("aldecI/builders/default", help="Builder identifier"),
    source: str = typer.Option("https://example.com/repo", help="Source URI"),
    build_type: str = typer.Option("https://fixops.dev/attestation/default", help="Build type URI"),
) -> None:
    ctx = cast(CLIContext, typer_ctx.obj)
    request = ProvenanceAttestRequest(
        artifact_name=artifact.name,
        artifact_content=_base64_file(artifact),
        builder_id=builder,
        source_uri=source,
        build_type=build_type,
        overlay=ctx.overlay.value,
    )
    response = _dispatch(
        ctx,
        "provenance.attest",
        request,
        local_handlers.handle_provenance_attest,
        lambda client, payload: client.provenance_attest(payload),
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(response.attestation, indent=2), encoding="utf-8")
    typer.echo(f"Attestation written to {out_path}")


@prov_app.command("verify")
def provenance_verify(
    typer_ctx: typer.Context,
    artifact: Path = typer.Option(
        ..., "--artifact", help="Artefact to verify", exists=True, dir_okay=False
    ),
    attestation: Path = typer.Option(
        ..., "--attestation", help="Attestation JSON", exists=True, dir_okay=False
    ),
    builder: Optional[str] = typer.Option(None, help="Expected builder ID"),
    source: Optional[str] = typer.Option(None, help="Expected source URI"),
    build_type: Optional[str] = typer.Option(None, help="Expected build type"),
) -> None:
    ctx = cast(CLIContext, typer_ctx.obj)
    request = ProvenanceVerifyRequest(
        artifact_name=artifact.name,
        artifact_content=_base64_file(artifact),
        attestation=_read_json(attestation),
        builder_id=builder,
        source_uri=source,
        build_type=build_type,
        overlay=ctx.overlay.value,
    )
    _dispatch(
        ctx,
        "provenance.verify",
        request,
        local_handlers.handle_provenance_verify,
        lambda client, payload: client.provenance_verify(payload),
    )
    typer.echo("Attestation verified successfully")


def _graph_request_base(
    ctx: CLIContext,
    artifact: str | None,
    commits: Optional[Path],
    commits_json: Optional[Path],
    attestations_dir: Optional[Path],
    attestations_json: Optional[Path],
    normalized_sbom: Optional[Path],
    risk_report: Optional[Path],
    releases: Optional[Path],
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "overlay": ctx.overlay.value,
        "commits": [],
        "attestations": [],
    }
    if artifact is not None:
        payload["artifact"] = artifact
    if commits_json:
        payload["commits"] = list(_read_json(commits_json) or [])
    elif commits:
        payload["commits"] = _collect_commits(commits)
    if attestations_json:
        payload["attestations"] = list(_read_json(attestations_json) or [])
    elif attestations_dir:
        payload["attestations"] = _collect_attestations([attestations_dir])
    if normalized_sbom:
        payload["normalized_sbom"] = _read_json(normalized_sbom)
    if risk_report:
        payload["risk_report"] = _read_json(risk_report)
    if releases:
        payload["releases"] = _read_json(releases)
    return payload


def _build_gate_metrics(
    metrics_path: Path | None,
    risk_report: Path | None,
    provenance_dir: Path | None,
    repro_attestation: Path | None,
) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    if metrics_path is not None and metrics_path.exists():
        loaded = _read_json(metrics_path)
        if isinstance(loaded, dict):
            metrics.update(loaded)
    if risk_report is not None and risk_report.exists():
        risk_payload = _read_json(risk_report) or {}
        summary = risk_payload.get("summary") if isinstance(risk_payload, dict) else {}
        if isinstance(summary, dict):
            risk_metrics: dict[str, Any] = {}
            for key in ("component_count", "cve_count", "max_risk_score"):
                value = summary.get(key)
                if isinstance(value, (int, float)):
                    risk_metrics[key] = float(value)
            if risk_metrics:
                metrics.setdefault("risk", {}).update(risk_metrics)
    if provenance_dir is not None and provenance_dir.exists():
        provenance_files = _collect_files(provenance_dir)
        metrics.setdefault("provenance", {})["count"] = len(provenance_files)
    if repro_attestation is not None and repro_attestation.exists():
        repro_payload = _read_json(repro_attestation)
        if isinstance(repro_payload, dict):
            match = repro_payload.get("match")
            if isinstance(match, bool):
                metrics.setdefault("repro", {})["match"] = match
    return metrics


@graph_app.command("lineage")
def graph_lineage(
    typer_ctx: typer.Context,
    artifact: str = typer.Option(..., help="Artifact identifier"),
    commits: Optional[Path] = typer.Option(
        None, help="Git repository path", exists=True, file_okay=False
    ),
    commits_json: Optional[Path] = typer.Option(
        None, help="Pre-collected commit JSON", exists=True, dir_okay=False
    ),
    attestations_dir: Optional[Path] = typer.Option(
        None, help="Directory of attestation JSON files", exists=True, file_okay=False
    ),
    attestations_json: Optional[Path] = typer.Option(
        None, help="Attestation list JSON", exists=True, dir_okay=False
    ),
    normalized_sbom: Optional[Path] = typer.Option(
        None, help="Normalized SBOM JSON", exists=True, dir_okay=False
    ),
    risk_report: Optional[Path] = typer.Option(
        None, help="Risk report JSON", exists=True, dir_okay=False
    ),
    releases: Optional[Path] = typer.Option(
        None, help="Releases JSON", exists=True, dir_okay=False
    ),
) -> None:
    ctx = cast(CLIContext, typer_ctx.obj)
    payload = _graph_request_base(
        ctx,
        artifact,
        commits,
        commits_json,
        attestations_dir,
        attestations_json,
        normalized_sbom,
        risk_report,
        releases,
    )
    request = GraphLineageRequest(**payload)
    response = _dispatch(
        ctx,
        "graph.lineage",
        request,
        local_handlers.handle_graph_lineage,
        lambda client, req: client.graph_lineage(req),
    )
    _echo_json(response)


@graph_app.command("kev-in-last")
def graph_kev_in_last(
    typer_ctx: typer.Context,
    releases_window: int = typer.Option(1, help="Number of releases to inspect"),
    commits: Optional[Path] = typer.Option(
        None, help="Git repository path", exists=True, file_okay=False
    ),
    commits_json: Optional[Path] = typer.Option(
        None, help="Pre-collected commit JSON", exists=True, dir_okay=False
    ),
    attestations_dir: Optional[Path] = typer.Option(
        None, help="Directory of attestation JSON files", exists=True, file_okay=False
    ),
    attestations_json: Optional[Path] = typer.Option(
        None, help="Attestation list JSON", exists=True, dir_okay=False
    ),
    normalized_sbom: Optional[Path] = typer.Option(
        None, help="Normalized SBOM JSON", exists=True, dir_okay=False
    ),
    risk_report: Optional[Path] = typer.Option(
        None, help="Risk report JSON", exists=True, dir_okay=False
    ),
    releases: Optional[Path] = typer.Option(
        None, help="Releases JSON", exists=True, dir_okay=False
    ),
) -> None:
    ctx = cast(CLIContext, typer_ctx.obj)
    payload = _graph_request_base(
        ctx,
        None,
        commits,
        commits_json,
        attestations_dir,
        attestations_json,
        normalized_sbom,
        risk_report,
        releases,
    )
    payload["releases_window"] = releases_window
    request = GraphKevRequest(**payload)
    response = _dispatch(
        ctx,
        "graph.kev_in_last",
        request,
        local_handlers.handle_graph_kev,
        lambda client, req: client.graph_kev(req),
    )
    _echo_json(response)


@graph_app.command("anomalies")
def graph_anomalies(
    typer_ctx: typer.Context,
    commits: Optional[Path] = typer.Option(
        None, help="Git repository path", exists=True, file_okay=False
    ),
    commits_json: Optional[Path] = typer.Option(
        None, help="Pre-collected commit JSON", exists=True, dir_okay=False
    ),
    attestations_dir: Optional[Path] = typer.Option(
        None, help="Directory of attestation JSON files", exists=True, file_okay=False
    ),
    attestations_json: Optional[Path] = typer.Option(
        None, help="Attestation list JSON", exists=True, dir_okay=False
    ),
    normalized_sbom: Optional[Path] = typer.Option(
        None, help="Normalized SBOM JSON", exists=True, dir_okay=False
    ),
    risk_report: Optional[Path] = typer.Option(
        None, help="Risk report JSON", exists=True, dir_okay=False
    ),
    releases: Optional[Path] = typer.Option(
        None, help="Releases JSON", exists=True, dir_okay=False
    ),
) -> None:
    ctx = cast(CLIContext, typer_ctx.obj)
    payload = _graph_request_base(
        ctx,
        None,
        commits,
        commits_json,
        attestations_dir,
        attestations_json,
        normalized_sbom,
        risk_report,
        releases,
    )
    request = GraphAnomaliesRequest(**payload)
    response = _dispatch(
        ctx,
        "graph.anomalies",
        request,
        local_handlers.handle_graph_anomalies,
        lambda client, req: client.graph_anomalies(req),
    )
    _echo_json(response)


@evidence_app.command("bundle")
def evidence_bundle(
    typer_ctx: typer.Context,
    release: str = typer.Option(..., help="Release identifier"),
    normalized_sbom: Path = typer.Option(
        ..., help="Normalized SBOM JSON", exists=True, dir_okay=False
    ),
    sbom_quality_json: Path = typer.Option(
        ..., help="SBOM quality JSON", exists=True, dir_okay=False
    ),
    sbom_quality_html: Optional[Path] = typer.Option(
        None, help="SBOM quality HTML", exists=True, dir_okay=False
    ),
    risk_report: Path = typer.Option(
        ..., help="Risk report JSON", exists=True, dir_okay=False
    ),
    repro_attestation: Path = typer.Option(
        ..., help="Repro attestation JSON", exists=True, dir_okay=False
    ),
    provenance_dir: Path = typer.Option(
        ..., help="Directory with provenance files", exists=True, file_okay=False
    ),
    extra_dir: Optional[Path] = typer.Option(
        None, help="Directory with extra evidence", exists=True, file_okay=False
    ),
    policy: Optional[Path] = typer.Option(
        None, help="Policy override (YAML/JSON)", exists=True, dir_okay=False
    ),
    sign_key: Optional[Path] = typer.Option(
        None, help="Cosign private key", exists=True, dir_okay=False
    ),
    out_path: Path = typer.Option(
        Path("artifacts/evidence/bundle.zip"),
        "--out",
        help="Destination for bundled evidence ZIP",
    ),
) -> None:
    ctx = cast(CLIContext, typer_ctx.obj)
    provenance_files = [
        {
            "name": path.name,
            "content": _base64_file(path),
        }
        for path in _collect_files(provenance_dir)
    ]
    extra_files = [
        {
            "name": path.name,
            "content": _base64_file(path),
        }
        for path in _collect_files(extra_dir)
    ]
    policy_payload: dict[str, Any] | None = None
    if policy:
        try:
            policy_payload = _read_json(policy)
        except json.JSONDecodeError:
            policy_payload = yaml.safe_load(policy.read_text(encoding="utf-8"))
    sign_key_payload: str | None = _base64_file(sign_key) if sign_key else None
    request = EvidenceBundleRequest(
        tag=release,
        normalized_sbom=_read_json(normalized_sbom),
        sbom_quality_json=_read_json(sbom_quality_json),
        sbom_quality_html=sbom_quality_html.read_text(encoding="utf-8") if sbom_quality_html else None,
        risk_report=_read_json(risk_report),
        repro_attestation=_read_json(repro_attestation),
        provenance_files=provenance_files,
        extra_files=extra_files,
        policy=policy_payload,
        sign_key=sign_key_payload,
        overlay=ctx.overlay.value,
    )
    response = _dispatch(
        ctx,
        "evidence.bundle",
        request,
        local_handlers.handle_evidence_bundle,
        lambda client, req: client.evidence_bundle(req),
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(base64.b64decode(response.bundle_content.encode("utf-8")))
    manifest_path = out_path.with_suffix(".manifest.json")
    manifest_path.write_text(json.dumps(response.manifest, indent=2), encoding="utf-8")
    typer.echo(f"Evidence bundle written to {out_path} and {manifest_path}")


@app.command("gate")
def gate_check(
    typer_ctx: typer.Context,
    policy: Path = typer.Option(
        ..., help="Policy configuration", exists=True, dir_okay=False
    ),
    metrics_path: Path | None = typer.Option(
        None,
        "--metrics",
        help="Optional JSON document containing pre-computed gate metrics.",
        dir_okay=False,
        exists=True,
    ),
    risk_report: Path | None = typer.Option(
        None,
        "--risk-report",
        help="Optional risk report JSON used to derive policy metrics.",
        dir_okay=False,
        exists=True,
    ),
    provenance_dir: Path | None = typer.Option(
        None,
        "--provenance-dir",
        help="Directory of provenance artefacts to count for gate metrics.",
        file_okay=False,
        exists=True,
    ),
    repro_attestation: Path | None = typer.Option(
        None,
        "--repro-attestation",
        help="Reproducibility attestation JSON used to derive metrics.",
        dir_okay=False,
        exists=True,
    ),
) -> None:
    ctx = cast(CLIContext, typer_ctx.obj)
    policy_payload = _read_json(policy)
    metrics = _build_gate_metrics(metrics_path, risk_report, provenance_dir, repro_attestation)
    request = GateCheckRequest(
        policy=policy_payload,
        metrics=metrics or None,
        overlay=ctx.overlay.value,
    )
    response = _dispatch(
        ctx,
        "gate.check",
        request,
        local_handlers.handle_gate_check,
        lambda client, req: client.gate_check(req),
    )
    typer.echo(response.message)
    _echo_json(response)


@persona_app.command("explain")
def persona_explain(
    typer_ctx: typer.Context,
    role: str = typer.Option(..., help="Persona role"),
    risk: Path = typer.Option(..., help="Risk report JSON", exists=True, dir_okay=False),
) -> None:
    ctx = cast(CLIContext, typer_ctx.obj)
    request = PersonaExplainRequest(
        role=role,
        risk_report=_read_json(risk),
        overlay=ctx.overlay.value,
    )
    response = _dispatch(
        ctx,
        "persona.explain",
        request,
        local_handlers.handle_persona_explain,
        lambda client, req: client.persona_explain(req),
    )
    typer.echo(f"[{response.persona}] {response.narrative}")
    if response.highlights:
        for item in response.highlights:
            typer.echo(f"- {item}")
    _echo_json(
        {
            "contributions": response.contributions,
            "context": response.context,
        }
    )


def run_cli(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    try:
        app(args)
        return 0
    except SystemExit as exc:  # Typer exits via SystemExit
        return int(exc.code or 0)


if __name__ == "__main__":
    sys.exit(run_cli())
