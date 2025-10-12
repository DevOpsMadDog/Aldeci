"""Generate documentation for API/CLI interactions directly from runtime objects."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import click
from fastapi import FastAPI
from fastapi.routing import APIRoute
from typer.main import get_command

ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = ROOT / "docs"
DIAGRAM_DIR = DOCS_DIR / "diagrams"
ANCHOR_NOTE = "These docs are generated from apps/registry/execution_map.py."
ANCHOR_DETAIL = "Additional inputs: cli/aldecI.py and apps/api/app.py."

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app import create_app  # noqa: E402
from apps.registry.execution_map import EXECUTION_REGISTRY  # noqa: E402
from cli import aldecI as cli_app  # noqa: E402
from sdk.python.fixops_client import FixopsClient  # noqa: E402
from apps.runtime import local_handlers  # noqa: E402

CLICK_APP = get_command(cli_app.app)
FASTAPI_APP: FastAPI = create_app()

LOCAL_HANDLER_MAP: Dict[str, str] = {
    "stage.run": "handle_stage_run",
    "ingest.sbom": "handle_ingest_sbom",
    "ingest.sarif": "handle_ingest_sarif",
    "risk.score": "handle_risk_score",
    "provenance.attest": "handle_provenance_attest",
    "provenance.verify": "handle_provenance_verify",
    "graph.lineage": "handle_graph_lineage",
    "graph.kev_in_last": "handle_graph_kev",
    "graph.anomalies": "handle_graph_anomalies",
    "evidence.bundle": "handle_evidence_bundle",
    "gate.check": "handle_gate_check",
    "persona.explain": "handle_persona_explain",
}

CLIENT_METHOD_MAP: Dict[str, str] = {
    "stage.run": "stage_run",
    "ingest.sbom": "ingest_sbom",
    "ingest.sarif": "ingest_sarif",
    "risk.score": "risk_score",
    "provenance.attest": "provenance_attest",
    "provenance.verify": "provenance_verify",
    "graph.lineage": "graph_lineage",
    "graph.kev_in_last": "graph_kev",
    "graph.anomalies": "graph_anomalies",
    "evidence.bundle": "evidence_bundle",
    "gate.check": "gate_check",
    "persona.explain": "persona_explain",
}


def _resolve_click_command(path: str) -> Tuple[click.Command | None, click.Context | None]:
    command: click.Command = CLICK_APP
    ctx = click.Context(command)
    for part in path.split():
        next_command = command.get_command(ctx, part)
        if next_command is None:
            return None, None
        ctx = click.Context(next_command, info_name=part, parent=ctx)
        command = next_command
    return command, ctx


def _describe_cli(path: str) -> Dict[str, Any]:
    command, ctx = _resolve_click_command(path)
    if not command or not ctx:
        return {"usage": f"aldecI {path}", "options": []}
    options: List[str] = []
    for param in command.params:
        if isinstance(param, click.Option):
            opts = "/".join(param.opts)
            metavar = param.metavar or ""
            segment = f"{opts} {metavar}".strip()
            if param.default is not None and param.show_default:
                segment = f"{segment} (default: {param.default})"
            options.append(segment)
    usage = command.get_usage(ctx).strip()
    return {"usage": usage, "options": options}


def _build_route_index(app: FastAPI) -> Dict[Tuple[str, str], Dict[str, Any]]:
    index: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        methods = {method.upper() for method in route.methods or set()}
        methods.discard("HEAD")
        methods.discard("OPTIONS")
        for method in methods or {"GET"}:
            request_model = None
            if route.body_field is not None:
                request_model = getattr(route.body_field.type_, "__name__", str(route.body_field.type_))
            response_model = None
            if route.response_model is not None:
                response_model = getattr(route.response_model, "__name__", str(route.response_model))
            index[(method, route.path)] = {
                "endpoint": f"{route.endpoint.__module__}.{route.endpoint.__name__}",
                "request_model": request_model,
                "response_model": response_model,
            }
    return index


ROUTE_INDEX = _build_route_index(FASTAPI_APP)


def _availability_badge(meta: Dict[str, Any]) -> str:
    if meta.get("available"):
        return "✅ Available"
    reason = meta.get("reason") or "Unavailable"
    return f"❌ GAP: {reason}"


def _format_list(values: Iterable[str]) -> str:
    items = [value for value in values if value]
    return "<br>".join(items) if items else "—"


def generate_api_cli_map() -> str:
    lines: List[str] = []
    lines.append("# API to CLI Mapping")
    lines.append("")
    lines.append(f"> {ANCHOR_NOTE}")
    lines.append(f"> {ANCHOR_DETAIL}")
    lines.append("")
    lines.append(
        "| Capability | Availability | CLI Command | CLI Options | API Route | Handler | Outputs |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")

    for capability in sorted(EXECUTION_REGISTRY):
        meta = EXECUTION_REGISTRY[capability]
        cli_spec = meta.get("cli", {})
        cli_command = cli_spec.get("command", "")
        cli_details = _describe_cli(cli_command)
        cli_usage = cli_details.get("usage") or f"aldecI {cli_command}" if cli_command else "—"
        cli_options = _format_list(cli_details.get("options", []))
        api_spec = meta.get("api", {})
        method = api_spec.get("method", "").upper()
        route = api_spec.get("route", "")
        handler = "—"
        if method and route:
            handler = ROUTE_INDEX.get((method, route), {}).get("endpoint", "—")
        outputs = _format_list(meta.get("outputs", []))
        lines.append(
            f"| {capability} | {_availability_badge(meta)} | `{cli_usage}` | {cli_options} | {method} {route} | {handler} | {outputs} |"
        )

    return "\n".join(lines) + "\n"


def _local_handler_name(capability: str) -> str:
    handler = LOCAL_HANDLER_MAP.get(capability)
    if not handler:
        return "—"
    func = getattr(local_handlers, handler, None)
    if not func:
        return handler
    return f"{func.__module__}.{func.__name__}"


def _client_method_name(capability: str) -> str:
    method = CLIENT_METHOD_MAP.get(capability)
    if not method:
        return "—"
    func = getattr(FixopsClient, method, None)
    if not func:
        return method
    return f"{FixopsClient.__module__}.FixopsClient.{func.__name__}"


def generate_interactions() -> str:
    lines: List[str] = []
    lines.append("# System Interactions")
    lines.append("")
    lines.append(f"> {ANCHOR_NOTE}")
    lines.append(f"> {ANCHOR_DETAIL}")
    lines.append("")

    for capability in sorted(EXECUTION_REGISTRY):
        meta = EXECUTION_REGISTRY[capability]
        description = meta.get("description") or "Description not provided."
        lines.append(f"## {capability}")
        lines.append("")
        lines.append(f"**What it does:** {description}")
        lines.append("")
        if not meta.get("available"):
            reason = meta.get("reason") or "Capability unavailable upstream."
            lines.append(f"> GAP: {reason}")
            lines.append("")
            continue
        cli_path = meta.get("cli", {}).get("command", "—")
        api_spec = meta.get("api", {})
        method = api_spec.get("method", "").upper()
        route = api_spec.get("route", "")
        route_info = ROUTE_INDEX.get((method, route), {})
        segments = [
            f"CLI `aldecI {cli_path}`",
            f"Local backend `{_local_handler_name(capability)}`",
            f"HTTP client `{_client_method_name(capability)}`",
            f"API `{route_info.get('endpoint', '—')}`",
        ]
        services = meta.get("services", []) or []
        if services:
            segments.extend(f"Service `{service}`" for service in services)
        infra = meta.get("infra", []) or []
        if infra:
            segments.extend(f"Infra `{item}`" for item in infra)
        lines.append("**Function call chain:**")
        lines.append("")
        lines.append(" -> ".join(segments))
        lines.append("")

    return "\n".join(lines)


def _sanitize_participant(name: str, prefix: str) -> str:
    safe = name.replace(".", "_").replace("/", "_").replace("-", "_")
    safe = safe.replace("<", "_").replace(">", "_")
    return f"{prefix}{abs(hash(name)) % (10 ** 6)}"


def _write_sequence_diagram(capability: str, meta: Dict[str, Any], route_info: Dict[str, Any]) -> None:
    lines: List[str] = ["sequenceDiagram", "    participant CLI", "    participant Local", "    participant API"]
    cli_path = meta.get("cli", {}).get("command", "")
    api_spec = meta.get("api", {})
    method = api_spec.get("method", "").upper()
    route = api_spec.get("route", "")
    if not meta.get("available"):
        reason = meta.get("reason") or "Unavailable"
        lines.append(f"    CLI->>Local: aldecI {cli_path}")
        lines.append("    Local-->>CLI: exit 12")
        if method and route:
            lines.append(f"    CLI->>API: {method} {route}")
            lines.append("    API-->>CLI: 501 GAP")
        lines.append(f"    Note over CLI,API: {reason}")
    else:
        lines.append(f"    CLI->>Local: aldecI {cli_path}")
        lines.append(f"    Local->>API: {method} {route}")
        services = meta.get("services", []) or []
        infra = meta.get("infra", []) or []
        counter = 1
        for service in services:
            alias = _sanitize_participant(service, "S")
            lines.append(f"    participant {alias} as {service}")
            lines.append(f"    API->>{alias}: call")
            lines.append(f"    {alias}-->>API: result")
            counter += 1
        for item in infra:
            alias = _sanitize_participant(item, "I")
            lines.append(f"    participant {alias} as {item}")
            lines.append(f"    API->>{alias}: invoke")
            lines.append(f"    {alias}-->>API: ack")
        lines.append("    API-->>Local: response")
        lines.append("    Local-->>CLI: materialise outputs")
    diagram_path = DIAGRAM_DIR / f"seq_{capability.replace('.', '_')}.mmd"
    diagram_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    DIAGRAM_DIR.mkdir(parents=True, exist_ok=True)
    api_cli_map = generate_api_cli_map()
    interactions = generate_interactions()
    (DOCS_DIR / "API_CLI_MAP.md").write_text(api_cli_map, encoding="utf-8")
    (DOCS_DIR / "INTERACTIONS.md").write_text(interactions, encoding="utf-8")
    for capability in EXECUTION_REGISTRY:
        meta = EXECUTION_REGISTRY[capability]
        api_spec = meta.get("api", {})
        method = api_spec.get("method", "").upper()
        route = api_spec.get("route", "")
        route_info = ROUTE_INDEX.get((method, route), {})
        _write_sequence_diagram(capability, meta, route_info)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
