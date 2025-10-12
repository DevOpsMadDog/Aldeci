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
GAPS_PAYLOAD = json.loads(GAPS_PATH.read_text(encoding="utf-8")) if GAPS_PATH.is_file() else {"gaps": []}
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


EXECUTION_REGISTRY: Dict[str, Dict[str, Any]] = {
    "sbom.normalize": {
        **_availability("sbom.normalize"),
        "cli": {
            "command": "sbom normalize",
            "syntax": "aldecI sbom normalize --input <sbom.json> [--sbom-type auto]",
        },
        "api": {"method": "POST", "route": "/v1/sbom/normalize"},
        "domain": ["domain.sbom.normalize_sbom"],
        "services": [
            "services.normalize.normalizers.InputNormalizer.load_sbom",
        ],
        "infra": [],
        "overlays": ["demo", "enterprise"],
        "outputs": ["normalized_sbom.json"],
        "description": "Normalise CycloneDX/SPDX SBOM payloads to a canonical structure.",
    },
    "sarif.normalize": {
        **_availability("sarif.normalize"),
        "cli": {
            "command": "sarif normalize",
            "syntax": "aldecI sarif normalize --input <sarif.json>",
        },
        "api": {"method": "POST", "route": "/v1/sarif/normalize"},
        "domain": ["domain.sarif.normalize_sarif"],
        "services": [
            "services.normalize.normalizers.InputNormalizer.load_sarif",
        ],
        "infra": [],
        "overlays": ["demo", "enterprise"],
        "outputs": ["normalized_sarif.json"],
        "description": "Parse SARIF logs, harmonise severities, and summarise findings.",
    },
    "risk.score": {
        **_availability("risk.score"),
        "cli": {
            "command": "risk score",
            "syntax": "aldecI risk score --sbom <normalized.json> --epss <epss.csv> --kev <kev.json>",
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
        "outputs": ["risk_report.json", "risk_report.html"],
        "description": "Fuse EPSS, KEV, exposure, and version lag data into risk scores.",
    },
    "epss": {
        **_availability("epss"),
        "cli": {
            "command": "feeds epss",
            "syntax": "aldecI feeds epss --out data/feeds/epss.csv",
        },
        "api": {"method": "POST", "route": "/v1/feeds/epss"},
        "domain": [],
        "services": [],
        "infra": [
            "infra.feeds.epss.update_epss_feed",
            "infra.feeds.epss.load_epss_scores",
        ],
        "overlays": ["demo", "enterprise"],
        "outputs": ["data/feeds/epss.csv"],
        "description": "Download and cache the latest EPSS probability scores.",
    },
    "kev": {
        **_availability("kev"),
        "cli": {
            "command": "feeds kev",
            "syntax": "aldecI feeds kev --out data/feeds/kev.json",
        },
        "api": {"method": "POST", "route": "/v1/feeds/kev"},
        "domain": [],
        "services": [],
        "infra": [
            "infra.feeds.kev.update_kev_feed",
            "infra.feeds.kev.load_kev_catalog",
        ],
        "overlays": ["demo", "enterprise"],
        "outputs": ["data/feeds/kev.json"],
        "description": "Fetch and normalise the CISA Known Exploited Vulnerabilities catalogue.",
    },
    "provenance.attest": {
        **_availability("provenance.attest"),
        "cli": {
            "command": "provenance attest",
            "syntax": "aldecI provenance attest --artifact <path> --builder <id> --source <uri> --out <attestation.json>",
        },
        "api": {"method": "POST", "route": "/v1/provenance/attest"},
        "domain": ["domain.provenance.generate_attestation"],
        "services": [
            "services.provenance.attestation.generate_attestation",
            "services.provenance.attestation.write_attestation",
        ],
        "infra": ["telemetry.configure"],
        "overlays": ["demo", "enterprise"],
        "outputs": ["attestations/<artifact>.json"],
        "description": "Create SLSA v1 DSSE attestations for build artefacts.",
    },
    "provenance.verify": {
        **_availability("provenance.verify"),
        "cli": {
            "command": "provenance verify",
            "syntax": "aldecI provenance verify --artifact <path> --attestation <attestation.json>",
        },
        "api": {"method": "POST", "route": "/v1/provenance/verify"},
        "domain": ["domain.provenance.verify_attestation"],
        "services": [
            "services.provenance.attestation.verify_attestation",
        ],
        "infra": ["telemetry.configure"],
        "overlays": ["demo", "enterprise"],
        "outputs": ["verification_report.json"],
        "description": "Validate attestations against artefact digests, builders, and metadata.",
    },
    "evidence.bundle": {
        **_availability("evidence.bundle"),
        "cli": {
            "command": "evidence bundle",
            "syntax": "aldecI evidence bundle --config <bundle.yml> --out-dir evidence/",
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
        "outputs": ["evidence/bundles/<tag>.zip", "evidence/bundles/MANIFEST.yaml"],
        "description": "Assemble signed evidence bundles with policy evaluation results.",
    },
    "graph.lineage": {
        **_availability("graph.lineage"),
        "cli": {
            "command": "graph lineage",
            "syntax": "aldecI graph lineage --repo <path> --artifact <name>",
        },
        "api": {"method": "POST", "route": "/v1/graph/lineage"},
        "domain": [],
        "services": [
            "services.graph.graph.build_graph_from_sources",
            "services.graph.graph.ProvenanceGraph.lineage",
        ],
        "infra": ["telemetry.configure"],
        "overlays": ["demo", "enterprise"],
        "outputs": ["graph/lineage.json"],
        "description": "Construct provenance graphs and return artefact lineage traversals.",
    },
    "graph.kev_in_last": {
        **_availability("graph.kev_in_last"),
        "cli": {
            "command": "graph kev-in-last",
            "syntax": "aldecI graph kev-in-last --repo <path> --releases <n>",
        },
        "api": {"method": "POST", "route": "/v1/graph/kev-in-last"},
        "domain": [],
        "services": [
            "services.graph.graph.build_graph_from_sources",
            "services.graph.graph.ProvenanceGraph.components_with_kev",
        ],
        "infra": ["telemetry.configure"],
        "overlays": ["demo", "enterprise"],
        "outputs": ["graph/kev_components.json"],
        "description": "Identify components linked to KEV CVEs in the most recent releases.",
    },
    "graph.anomalies": {
        **_availability("graph.anomalies"),
        "cli": {
            "command": "graph anomalies",
            "syntax": "aldecI graph anomalies --repo <path>",
        },
        "api": {"method": "POST", "route": "/v1/graph/anomalies"},
        "domain": [],
        "services": [
            "services.graph.graph.build_graph_from_sources",
            "services.graph.graph.ProvenanceGraph.detect_version_anomalies",
        ],
        "infra": ["telemetry.configure"],
        "overlays": ["demo", "enterprise"],
        "outputs": ["graph/anomalies.json"],
        "description": "Detect release timeline anomalies across the provenance graph.",
    },
}

__all__ = ["EXECUTION_REGISTRY"]
