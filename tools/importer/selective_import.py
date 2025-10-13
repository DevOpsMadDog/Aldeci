"""Selectively import capabilities from the upstream FixOps repository."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Mapping, MutableMapping, Sequence

ROOT = Path(__file__).resolve().parents[2]
UPSTREAM_DIR = ROOT / ".upstream" / "Fixops"
ARTIFACTS_DIR = ROOT / "artifacts"
INDEX_PATH = ARTIFACTS_DIR / "upstream_symbol_index.json"
SHA_PATH = ARTIFACTS_DIR / "upstream_sha.txt"
ATTRIBUTION_TEMPLATE = "# Sourced from FixOps ({sha})"
BANNER_WIDTH = "# ----------------------------------------"


@dataclass(frozen=True)
class UpstreamFile:
    path: str
    language: str
    module: str | None


@dataclass(frozen=True)
class Selector:
    """Describe an upstream file to copy into the repository."""

    source: str
    destination: str


@dataclass(frozen=True)
class CapabilityConfig:
    """Mapping of a logical capability to upstream files or an alias."""

    selectors: Sequence[Selector] | None = None
    alias_of: str | None = None


CAPABILITY_MAP: Dict[str, CapabilityConfig] = {
    "sbom.normalize": CapabilityConfig(
        selectors=[
            Selector("lib4sbom/normalizer.py", "services/sbom/normalizer.py"),
        ]
    ),
    "sarif.normalize": CapabilityConfig(
        selectors=[
            Selector("apps/api/normalizers.py", "services/normalize/normalizers.py"),
        ]
    ),
    "risk.score": CapabilityConfig(
        selectors=[
            Selector("risk/scoring.py", "services/risk/scoring.py"),
        ]
    ),
    "epss": CapabilityConfig(
        selectors=[
            Selector("risk/feeds/__init__.py", "infra/feeds/__init__.py"),
            Selector("risk/feeds/epss.py", "infra/feeds/epss.py"),
        ]
    ),
    "kev": CapabilityConfig(
        selectors=[
            Selector("risk/feeds/__init__.py", "infra/feeds/__init__.py"),
            Selector("risk/feeds/kev.py", "infra/feeds/kev.py"),
        ]
    ),
    "provenance.attest": CapabilityConfig(
        selectors=[
            Selector("services/provenance/attestation.py", "services/provenance/attestation.py"),
            Selector("telemetry/__init__.py", "telemetry/__init__.py"),
            Selector("telemetry/_noop.py", "telemetry/_noop.py"),
            Selector("telemetry/fastapi_noop.py", "telemetry/fastapi_noop.py"),
        ]
    ),
    "provenance.verify": CapabilityConfig(alias_of="provenance.attest"),
    "evidence.bundle": CapabilityConfig(
        selectors=[
            Selector("evidence/__init__.py", "services/evidence/__init__.py"),
            Selector("evidence/packager.py", "services/evidence/packager.py"),
            Selector("scripts/signing/sign-artifact.sh", "infra/signing/sign-artifact.sh"),
            Selector("scripts/signing/verify-artifact.sh", "infra/signing/verify-artifact.sh"),
        ]
    ),
    "graph.lineage": CapabilityConfig(
        selectors=[
            Selector("services/graph/__init__.py", "services/graph/__init__.py"),
            Selector("services/graph/graph.py", "services/graph/graph.py"),
        ]
    ),
    "graph.kev_in_last": CapabilityConfig(alias_of="graph.lineage"),
    "graph.anomalies": CapabilityConfig(alias_of="graph.lineage"),
    "stage.run": CapabilityConfig(
        selectors=[
            Selector("core/stage_runner.py", "core/stage_runner.py"),
            Selector(
                "fixops-enterprise/src/services/run_registry.py",
                "services/run_registry.py",
            ),
            Selector(
                "fixops-enterprise/src/services/id_allocator.py",
                "services/id_allocator.py",
            ),
            Selector(
                "fixops-enterprise/src/services/signing.py",
                "services/signing.py",
            ),
            Selector(
                "fixops-enterprise/src/config/settings.py",
                "config/settings.py",
            ),
            Selector("core/configuration.py", "core/configuration.py"),
        ]
    ),
    "gate.check": CapabilityConfig(alias_of="evidence.bundle"),
    "persona.explain": CapabilityConfig(
        selectors=[
            Selector(
                "WIP/code/enterprise_legacy/src/services/explainability.py",
                "services/explainability.py",
            ),
        ]
    ),
}


def load_index() -> tuple[Dict[str, UpstreamFile], Dict[str, str]]:
    if not INDEX_PATH.is_file():
        raise FileNotFoundError("Run tools/importer/index_upstream.py before selective imports.")
    payload = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    records: Dict[str, UpstreamFile] = {}
    for entry in payload.get("files", []):
        record = UpstreamFile(
            path=entry["path"],
            language=entry.get("language", "Unknown"),
            module=entry.get("module"),
        )
        records[record.path] = record
    symbols = payload.get("symbols", {})
    return records, symbols


def ensure_destination(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def ensure_banner(content: str, sha: str) -> str:
    header = ATTRIBUTION_TEMPLATE.format(sha=sha)
    lines = content.splitlines()
    banner = [BANNER_WIDTH, header, BANNER_WIDTH]
    if lines[:3] == banner:
        return content
    if content.startswith("#!"):
        shebang, *rest = content.splitlines()
        remainder = "\n".join(rest)
        return "\n".join([shebang, *banner, remainder])
    return "\n".join([*banner, content])


def copy_file(record: UpstreamFile, destination: Path, sha: str) -> None:
    source = UPSTREAM_DIR / record.path
    if not source.is_file():
        raise FileNotFoundError(f"Missing upstream source: {record.path}")
    ensure_destination(destination)
    if record.language == "Python":
        content = source.read_text(encoding="utf-8")
        patched = ensure_banner(content, sha)
        destination.write_text(patched, encoding="utf-8")
    else:
        shutil.copy2(source, destination)


def calculate_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def capability_tokens(capability: str) -> List[str]:
    tokens: List[str] = []
    for segment in capability.replace("-", ".").split("."):
        cleaned = segment.strip().lower()
        if cleaned:
            tokens.append(cleaned)
    return tokens


def write_artifacts(
    mapping: Mapping[str, MutableMapping[str, object]],
    *,
    gaps: Sequence[Mapping[str, object]],
    sha: str,
) -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "upstream_sha": sha,
        "capabilities": mapping,
    }
    (ARTIFACTS_DIR / "upstream_map.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (ARTIFACTS_DIR / "gaps.json").write_text(
        json.dumps({"upstream_sha": sha, "gaps": list(gaps)}, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Selectively import FixOps capabilities")
    parser.add_argument("capabilities", nargs="+", help="Capability identifiers to import")
    parser.add_argument("--dest-root", default=".", help="Destination root override")
    args = parser.parse_args(argv)

    records, _ = load_index()
    sha = SHA_PATH.read_text(encoding="utf-8").strip() if SHA_PATH.is_file() else "unknown"
    dest_root = Path(args.dest_root).resolve()

    results: Dict[str, MutableMapping[str, object]] = {}
    gaps: List[Mapping[str, object]] = []

    def process(capability: str, stack: Sequence[str] | None = None) -> MutableMapping[str, object]:
        if capability in results:
            return results[capability]
        stack = list(stack or [])
        if capability in stack:
            raise RuntimeError(f"Cyclic capability alias detected: {' -> '.join(stack + [capability])}")
        stack.append(capability)

        config = CAPABILITY_MAP.get(capability)
        if config is None:
            entry = {
                "available": False,
                "reason": "no mapping configured",
                "suggested_search_terms": capability_tokens(capability),
            }
            results[capability] = entry
            return entry

        if config.alias_of:
            alias_result = process(config.alias_of, stack)
            entry = {
                "available": alias_result.get("available", False),
                "alias_of": config.alias_of,
                "artifacts": alias_result.get("artifacts", []),
            }
            if not entry["available"]:
                entry["reason"] = alias_result.get("reason", "not available")
                entry["suggested_search_terms"] = capability_tokens(capability)
            results[capability] = entry
            return entry

        selectors = config.selectors or []
        artifacts: List[Mapping[str, str]] = []
        missing_sources: List[str] = []
        for selector in selectors:
            record = records.get(selector.source)
            if record is None:
                missing_sources.append(selector.source)
                continue
            destination = dest_root / selector.destination
            try:
                copy_file(record, destination, sha)
            except FileNotFoundError:
                missing_sources.append(selector.source)
                continue
            sha256 = calculate_sha256(destination)
            artifacts.append(
                {
                    "source": record.path,
                    "destination": selector.destination,
                    "sha256": sha256,
                }
            )
        if missing_sources:
            entry = {
                "available": False,
                "reason": f"missing upstream source(s): {', '.join(sorted(missing_sources))}",
                "suggested_search_terms": capability_tokens(capability),
            }
            results[capability] = entry
            return entry

        entry = {
            "available": True,
            "artifacts": artifacts,
        }
        results[capability] = entry
        return entry

    for capability in args.capabilities:
        outcome = process(capability)
        if not outcome.get("available"):
            gaps.append(
                {
                    "capability": capability,
                    "reason": outcome.get("reason", "not found"),
                    "upstream_sha": sha,
                    "suggested_search_terms": outcome.get("suggested_search_terms", capability_tokens(capability)),
                }
            )

    write_artifacts(results, gaps=gaps, sha=sha)

    if gaps:
        missing = ", ".join(entry["capability"] for entry in gaps)
        raise SystemExit(f"GAP: missing upstream capabilities: {missing}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
