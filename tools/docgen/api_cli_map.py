"""Generate documentation for API/CLI interactions directly from the execution registry."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable, List

ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = ROOT / "docs"
ANCHOR_NOTE = "These docs are generated from apps/registry/execution_map.py."

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.registry.execution_map import EXECUTION_REGISTRY  # noqa: E402


def _format_list(values: Iterable[str]) -> str:
    items = [value for value in values if value]
    return "<br>".join(items) if items else "—"


def _capability_title(capability: str, alias_of: str | None) -> str:
    if alias_of:
        return f"{capability} (alias of {alias_of})"
    return capability


def generate_api_cli_map() -> str:
    lines: List[str] = []
    lines.append("# API to CLI Mapping")
    lines.append("")
    lines.append(f"> {ANCHOR_NOTE}")
    lines.append("")
    lines.append("| Capability | CLI Syntax | API Route | Services | Overlays | Outputs |")
    lines.append("| --- | --- | --- | --- | --- | --- |")

    for capability in sorted(EXECUTION_REGISTRY):
        data = EXECUTION_REGISTRY[capability]
        title = _capability_title(capability, data.get("alias_of"))
        cli_syntax = data.get("cli", {}).get("syntax", "—")
        api = data.get("api", {})
        api_route = "—"
        if api:
            method = api.get("method", "").upper()
            route = api.get("route", "")
            api_route = f"{method} {route}".strip()
        if not data.get("available", False):
            services = f"GAP: {data.get('reason') or 'unavailable'}"
        else:
            services = _format_list(data.get("services", []))
        overlays = _format_list(data.get("overlays", []))
        outputs = _format_list(data.get("outputs", []))
        lines.append(
            f"| {title} | {cli_syntax} | {api_route} | {services} | {overlays} | {outputs} |"
        )

    return "\n".join(lines) + "\n"


def _flow_segments(data: dict) -> List[str]:
    segments: List[str] = []
    cli = data.get("cli", {})
    if cli:
        segments.append(f"CLI `{cli.get('syntax', 'aldecI …')}`")
    api = data.get("api", {})
    if api:
        method = api.get("method", "").upper()
        route = api.get("route", "")
        segments.append(f"API `{method} {route}`".strip())
    for scope, key in (("domain", "domain"), ("services", "services"), ("infra", "infra")):
        for item in data.get(key, []) or []:
            label = "Infra" if scope == "infra" else "Service"
            segments.append(f"{label} `{item}`")
    outputs = data.get("outputs", [])
    if outputs:
        segments.append("Outputs " + ", ".join(outputs))
    return segments


def generate_interactions() -> str:
    lines: List[str] = []
    lines.append("# System Interactions")
    lines.append("")
    lines.append(f"> {ANCHOR_NOTE}")
    lines.append("")

    for capability in sorted(EXECUTION_REGISTRY):
        data = EXECUTION_REGISTRY[capability]
        lines.append(f"## {_capability_title(capability, data.get('alias_of'))}")
        lines.append("")
        description = data.get("description") or "Description not provided."
        lines.append(f"**What it does:** {description}")
        lines.append("")
        if not data.get("available", False):
            reason = data.get("reason") or "Capability unavailable upstream."
            lines.append(f"> GAP: {reason}")
            lines.append("")
        else:
            flow = " → ".join(_flow_segments(data)) or "Flow details pending."
            lines.append(f"**Flow:** {flow}")
            lines.append("")

        cli = data.get("cli", {})
        lines.append("**Sample CLI**")
        lines.append("")
        lines.append("```bash")
        lines.append(cli.get("syntax", "aldecI <command>"))
        lines.append("```")
        lines.append("")

        api = data.get("api", {})
        method = api.get("method", "POST").upper()
        route = api.get("route", "/v1/<placeholder>")
        lines.append("**Sample cURL**")
        lines.append("")
        lines.append("```bash")
        lines.append(
            "curl -X {method} https://api.example.com{route} \\\n  -H 'Authorization: Bearer <token>' \\\n  -H 'Content-Type: application/json' \\\n  -d '{{\"payload\": \"...\"}}'".format(method=method, route=route)
        )
        lines.append("```")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    (DOCS_DIR / "API_CLI_MAP.md").write_text(generate_api_cli_map(), encoding="utf-8")
    (DOCS_DIR / "INTERACTIONS.md").write_text(generate_interactions(), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
