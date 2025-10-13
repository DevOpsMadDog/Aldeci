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


def _cli_syntax(meta: Dict[str, Any]) -> str:
    cli_spec = meta.get("cli", {})
    syntax = cli_spec.get("syntax") if isinstance(cli_spec, dict) else None
    if syntax:
        return syntax
    command = cli_spec.get("command") if isinstance(cli_spec, dict) else None
    if command:
        return f"aldecI {command}"
    return "—"


def _sample_cli(meta: Dict[str, Any]) -> str:
    syntax = _cli_syntax(meta)
    if syntax == "—":
        return "—"
    overlays = meta.get("overlays", []) or []
    overlay = overlays[0] if overlays else "demo"
    return f"{syntax} --backend local --overlay {overlay}"


def _sample_curl(meta: Dict[str, Any], method: str, route: str) -> str:
    if not method or not route:
        return "—"
    method = method.upper()
    payload_hint = meta.get("api_payload", "@payload.json")
    return (
        "curl -sS -X "
        + method
        + f" http://127.0.0.1:8000{route} -H 'Content-Type: application/json' -d {payload_hint}"
    )


def generate_api_cli_map() -> str:
    lines: List[str] = []
    lines.append("# API to CLI Mapping")
    lines.append("")
    lines.append(f"> {ANCHOR_NOTE}")
    lines.append(f"> {ANCHOR_DETAIL}")
    lines.append("")
    lines.append(
        "| Capability | Availability | CLI Syntax | API Route | FastAPI Handler | Service Calls | Overlays | Outputs | Sample CLI | Sample cURL |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")

    for capability in sorted(EXECUTION_REGISTRY):
        meta = EXECUTION_REGISTRY[capability]
        cli_usage = _cli_syntax(meta)
        api_spec = meta.get("api", {})
        method = api_spec.get("method", "").upper()
        route = api_spec.get("route", "")
        route_info = ROUTE_INDEX.get((method, route), {})
        handler = route_info.get("endpoint", "—")
        services = _format_list(meta.get("services", []))
        overlays = _format_list(meta.get("overlays", []))
        outputs = _format_list(meta.get("outputs", []))
        sample_cli = _sample_cli(meta)
        sample_curl = _sample_curl(meta, method, route)
        lines.append(
            "| {capability} | {availability} | `{cli_usage}` | {method} {route} | {handler} | {services} | {overlays} | {outputs} | `{sample_cli}` | `{sample_curl}` |".format(
                capability=capability,
                availability=_availability_badge(meta),
                cli_usage=cli_usage,
                method=method,
                route=route,
                handler=handler,
                services=services,
                overlays=overlays,
                outputs=outputs,
                sample_cli=sample_cli,
                sample_curl=sample_curl,
            )
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
        lines.append(f"**Availability:** {_availability_badge(meta)}")
        lines.append("")
        lines.append(f"**What it does:** {description}")
        lines.append("")
        overlays = ", ".join(meta.get("overlays", []) or []) or "—"
        outputs = ", ".join(meta.get("outputs", []) or []) or "—"
        lines.append(f"**Overlays:** {overlays}")
        lines.append(f"**Outputs:** {outputs}")
        sample_cli = _sample_cli(meta)
        if sample_cli != "—":
            lines.append(f"**CLI Sample:** `{sample_cli}`")
        api_spec = meta.get("api", {})
        method = api_spec.get("method", "").upper()
        route = api_spec.get("route", "")
        if method and route:
            sample_curl = _sample_curl(meta, method, route)
            if sample_curl != "—":
                lines.append(f"**HTTP Sample:** `{sample_curl}`")
        lines.append("")
        if not meta.get("available"):
            reason = meta.get("reason") or "Capability unavailable upstream."
            lines.append(f"**GAP:** {reason}")
            lines.append("")
            continue
        route_info = ROUTE_INDEX.get((method, route), {})
        chain = [
            f"CLI `{_cli_syntax(meta)}`",
            f"Local backend `{_local_handler_name(capability)}`",
            f"SDK `{_client_method_name(capability)}`",
            f"FastAPI `{route_info.get('endpoint', '—')}`",
        ]
        services = meta.get("services", []) or []
        if services:
            chain.extend(f"Service `{service}`" for service in services)
        infra = meta.get("infra", []) or []
        if infra:
            chain.extend(f"Infra `{item}`" for item in infra)
        lines.append("**Function call chain:**")
        lines.append("")
        lines.append(" -> ".join(chain))
        lines.append("")

    return "\n".join(lines)


def _sanitize_participant(name: str, prefix: str) -> str:
    safe = name.replace(".", "_").replace("/", "_").replace("-", "_")
    safe = safe.replace("<", "_").replace(">", "_")
    return f"{prefix}{abs(hash(name)) % (10 ** 6)}"


def _write_sequence_diagram(capability: str, meta: Dict[str, Any], _route_info: Dict[str, Any]) -> None:
    lines: List[str] = [
        "sequenceDiagram",
        "    participant CLI",
        "    participant Local",
        "    participant SDK",
        "    participant API",
    ]
    api_spec = meta.get("api", {})
    method = api_spec.get("method", "").upper()
    route = api_spec.get("route", "")
    cli_label = _cli_syntax(meta)
    local_handler = _local_handler_name(capability)
    client_method = _client_method_name(capability)
    participants: List[Tuple[str, str]] = []
    if local_handler != "—":
        participants.append((_sanitize_participant(local_handler, "L"), local_handler))
    services = meta.get("services", []) or []
    service_aliases = [
        (_sanitize_participant(service, "S"), service) for service in services
    ]
    participants.extend(service_aliases)
    infra = meta.get("infra", []) or []
    infra_aliases = [(_sanitize_participant(item, "I"), item) for item in infra]
    participants.extend(infra_aliases)
    for alias, name in participants:
        lines.append(f"    participant {alias} as {name}")

    if not meta.get("available"):
        reason = meta.get("reason") or "Unavailable"
        lines.append(f"    CLI->>Local: {cli_label}")
        lines.append("    Local-->>CLI: exit 12")
        if method and route:
            lines.append(f"    CLI->>SDK: {client_method}")
            lines.append(f"    SDK->>API: {method} {route}")
            lines.append("    API-->>SDK: 501 GAP")
            lines.append("    SDK-->>CLI: propagate GAP")
        lines.append(f"    Note over CLI,API: {reason}")
    else:
        lines.append(f"    CLI->>Local: {cli_label}")
        if local_handler != "—":
            local_alias = _sanitize_participant(local_handler, "L")
            lines.append(f"    Local->>{local_alias}: execute")
            lines.append(f"    {local_alias}-->>Local: results")
        for alias, _ in service_aliases:
            lines.append(f"    Local->>{alias}: call")
            lines.append(f"    {alias}-->>Local: result")
        for alias, _ in infra_aliases:
            lines.append(f"    Local->>{alias}: invoke")
            lines.append(f"    {alias}-->>Local: ack")
        lines.append("    Local-->>CLI: outputs")
        if method and route:
            lines.append(f"    CLI->>SDK: {client_method}")
            lines.append(f"    SDK->>API: {method} {route}")
            for alias, _ in service_aliases:
                lines.append(f"    API->>{alias}: call")
                lines.append(f"    {alias}-->>API: result")
            for alias, _ in infra_aliases:
                lines.append(f"    API->>{alias}: invoke")
                lines.append(f"    {alias}-->>API: ack")
            lines.append("    API-->>SDK: response")
            lines.append("    SDK-->>CLI: parsed response")

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
