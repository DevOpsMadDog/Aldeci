"""Execution registry bridging CLI commands, API routes, and reused services."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS_DIR = ROOT / "artifacts"
UPSTREAM_MAP_PATH = ARTIFACTS_DIR / "upstream_map.json"
GAPS_PATH = ARTIFACTS_DIR / "gaps.json"

if not UPSTREAM_MAP_PATH.is_file():
    raise FileNotFoundError(
        "Missing upstream_map.json. Run tools/importer/selective_import.py first."
    )

UPSTREAM_PAYLOAD = json.loads(UPSTREAM_MAP_PATH.read_text(encoding="utf-8"))
GAPS_PAYLOAD = (
    json.loads(GAPS_PATH.read_text(encoding="utf-8")) if GAPS_PATH.is_file() else {"gaps": []}
)
GAP_INDEX: Dict[str, Dict[str, Any]] = {
    entry["capability"]: entry for entry in GAPS_PAYLOAD.get("gaps", [])
}


def _upstream_entry(capability: str) -> Dict[str, Any]:
    return UPSTREAM_PAYLOAD.get("capabilities", {}).get(capability, {})


def _availability(capability: str) -> Dict[str, Any]:
    entry = _upstream_entry(capability)
    available = bool(entry.get("available"))
    alias_of = entry.get("alias_of")
    reason = None
    if not available:
        reason = GAP_INDEX.get(capability, {}).get("reason")
    return {
        "available": available,
        "alias_of": alias_of,
        "reason": reason,
    }


def _availability_entry(
    capability: str,
    *,
    alias_of: str | None = None,
    default_reason: str | None = None,
) -> Dict[str, Any]:
    """Return availability metadata with optional alias and fallback reason."""

    payload = _availability(capability)
    if alias_of:
        payload["alias_of"] = alias_of
    if default_reason and not payload.get("reason"):
        payload["reason"] = default_reason
    return payload


EXECUTION_REGISTRY: Dict[str, Dict[str, Any]] = {
    "stage.run": {
        **_availability_entry(
            "stage.run",
            default_reason="Upstream stage runner not available in reuse bundle.",
        ),
        "cli": {
            "command": "stage run",
            "syntax": "aldecI stage run --stage <requirements|design|build|test|deploy|operate|decision>",
        },
        "api": {"method": "POST", "route": "/v1/stage/run"},
        "domain": [],
        "services": [],
        "infra": [],
        "overlays": ["demo", "enterprise"],
        "outputs": ["artifacts/stage/<stage>.json"],
        "description": "Execute a FixOps SDLC stage runbook.",
    },
    "ingest.sbom": {
        **_availability_entry("sbom.normalize", alias_of="sbom.normalize"),
        "cli": {
            "command": "ingest sbom",
            "syntax": "aldecI ingest sbom --in <sbom.json> --out artifacts/sbom/normalized.json",
        },
        "api": {"method": "POST", "route": "/v1/ingest/sbom"},
        "domain": ["domain.sbom.normalize_sbom"],
        "services": [
            "services.normalize.normalizers.InputNormalizer.load_sbom",
        ],
        "infra": [],
        "overlays": ["demo", "enterprise"],
        "outputs": ["artifacts/sbom/normalized.json"],
        "description": "Normalise CycloneDX/SPDX SBOM payloads to a canonical structure.",
    },
    "ingest.sarif": {
        **_availability_entry("sarif.normalize", alias_of="sarif.normalize"),
        "cli": {
            "command": "ingest sarif",
            "syntax": "aldecI ingest sarif --in <sarif.json> --out artifacts/sarif/normalized.json",
        },
        "api": {"method": "POST", "route": "/v1/ingest/sarif"},
        "domain": ["domain.sarif.normalize_sarif"],
        "services": [
            "services.normalize.normalizers.InputNormalizer.load_sarif",
        ],
        "infra": [],
        "overlays": ["demo", "enterprise"],
        "outputs": ["artifacts/sarif/normalized.json"],
        "description": "Parse SARIF logs, harmonise severities, and summarise findings.",
    },
    "risk.score": {
        **_availability_entry("risk.score"),
        "cli": {
            "command": "risk score",
            "syntax": "aldecI risk score --sbom artifacts/sbom/normalized.json --epss feeds/epss.csv --kev feeds/kev.json --out artifacts/risk.json",
        },
        "api": {"method": "POST", "route": "/v1/risk/score"},
        "domain": [],
        "services": [
            "services.risk.scoring.compute_risk_profile",
            "services.risk.scoring.write_risk_report",
        ],
        "infra": [
            "infra.feeds.epss.load_epss_scores",
            "infra.feeds.kev.load_kev_catalog",
        ],
        "overlays": ["demo", "enterprise"],
        "outputs": ["artifacts/risk.json"],
        "description": "Fuse EPSS, KEV, exposure, and version lag data into risk scores.",
    },
    "provenance.attest": {
        **_availability_entry("provenance.attest"),
        "cli": {
            "command": "prov attest",
            "syntax": "aldecI prov attest --artifact <path> --out artifacts/attestations/<id>.json",
        },
        "api": {"method": "POST", "route": "/v1/provenance/attest"},
        "domain": ["domain.provenance.generate_attestation"],
        "services": [
            "services.provenance.attestation.generate_attestation",
            "services.provenance.attestation.write_attestation",
        ],
        "infra": ["telemetry.configure"],
        "overlays": ["demo", "enterprise"],
        "outputs": ["artifacts/attestations/<id>.json"],
        "description": "Create SLSA v1 DSSE attestations for build artefacts.",
    },
    "provenance.verify": {
        **_availability_entry("provenance.verify"),
        "cli": {
            "command": "prov verify",
            "syntax": "aldecI prov verify --artifact <path> --attestation <attestation.json>",
        },
        "api": {"method": "POST", "route": "/v1/provenance/verify"},
        "domain": ["domain.provenance.verify_attestation"],
        "services": [
            "services.provenance.attestation.verify_attestation",
        ],
        "infra": ["telemetry.configure"],
        "overlays": ["demo", "enterprise"],
        "outputs": ["artifacts/attestations/verification.json"],
        "description": "Validate attestations against artefact digests, builders, and metadata.",
    },
    "graph.lineage": {
        **_availability_entry("graph.lineage"),
        "cli": {
            "command": "graph lineage",
            "syntax": "aldecI graph lineage --artifact <id|path>",
        },
        "api": {"method": "POST", "route": "/v1/graph/lineage"},
        "domain": [],
        "services": [
            "services.graph.graph.ProvenanceGraph.lineage",
            "services.graph.graph.build_graph_from_sources",
        ],
        "infra": ["telemetry.configure"],
        "overlays": ["demo", "enterprise"],
        "outputs": ["artifacts/graph/lineage.json"],
        "description": "Construct provenance graphs and return artefact lineage traversals.",
    },
    "graph.kev_in_last": {
        **_availability_entry("graph.kev_in_last"),
        "cli": {
            "command": "graph kev-in-last",
            "syntax": "aldecI graph kev-in-last --releases <N>",
        },
        "api": {"method": "POST", "route": "/v1/graph/kev-in-last"},
        "domain": [],
        "services": [
            "services.graph.graph.ProvenanceGraph.components_with_kev",
            "services.graph.graph.build_graph_from_sources",
        ],
        "infra": ["telemetry.configure"],
        "overlays": ["demo", "enterprise"],
        "outputs": ["artifacts/graph/kev_components.json"],
        "description": "Identify components linked to KEV CVEs in the most recent releases.",
    },
    "graph.anomalies": {
        **_availability_entry("graph.anomalies"),
        "cli": {
            "command": "graph anomalies",
            "syntax": "aldecI graph anomalies --type version-drift",
        },
        "api": {"method": "POST", "route": "/v1/graph/anomalies"},
        "domain": [],
        "services": [
            "services.graph.graph.ProvenanceGraph.detect_version_anomalies",
            "services.graph.graph.build_graph_from_sources",
        ],
        "infra": ["telemetry.configure"],
        "overlays": ["demo", "enterprise"],
        "outputs": ["artifacts/graph/anomalies.json"],
        "description": "Detect release timeline anomalies across the provenance graph.",
    },
    "evidence.bundle": {
        **_availability_entry("evidence.bundle"),
        "cli": {
            "command": "evidence bundle",
            "syntax": "aldecI evidence bundle --release <id> --out artifacts/evidence/<id>.zip",
        },
        "api": {"method": "POST", "route": "/v1/evidence/bundle"},
        "domain": [],
        "services": [
            "services.evidence.packager.load_policy",
            "services.evidence.packager.evaluate_policy",
            "services.evidence.packager.create_bundle",
        ],
        "infra": ["infra.signing.sign-artifact.sh"],
        "overlays": ["demo", "enterprise"],
        "outputs": ["artifacts/evidence/<id>.zip", "artifacts/evidence/<id>.yaml"],
        "description": "Assemble signed evidence bundles with policy evaluation results.",
    },
    "gate.check": {
        **_availability_entry(
            "gate.check",
            default_reason="Policy gate evaluation not included in reuse artefacts.",
        ),
        "cli": {
            "command": "gate",
            "syntax": "aldecI gate --policy config/policy.yml",
        },
        "api": {"method": "POST", "route": "/v1/gate/check"},
        "domain": [],
        "services": [],
        "infra": [],
        "overlays": ["demo", "enterprise"],
        "outputs": ["artifacts/gate/report.json"],
        "description": "Evaluate policy gates against collected evidence.",
    },
    "persona.explain": {
        **_availability_entry(
            "persona.explain",
            default_reason="Persona explanation models are not part of the reuse snapshot.",
        ),
        "cli": {
            "command": "persona explain",
            "syntax": "aldecI persona explain --role <role> --risk artifacts/risk.json",
        },
        "api": {"method": "POST", "route": "/v1/persona/explain"},
        "domain": [],
        "services": [],
        "infra": [],
        "overlays": ["demo", "enterprise"],
        "outputs": ["artifacts/persona/<role>.md"],
        "description": "Generate risk narratives tailored for specific personas.",
    },
}

__all__ = ["EXECUTION_REGISTRY"]
