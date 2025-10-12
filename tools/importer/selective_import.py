"""Selectively import capabilities from the upstream FixOps repository."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

ROOT = Path(__file__).resolve().parents[2]
UPSTREAM_DIR = ROOT / ".upstream" / "Fixops"
ARTIFACTS_DIR = ROOT / "artifacts"
INDEX_PATH = ARTIFACTS_DIR / "upstream_symbol_index.json"
SHA_PATH = ARTIFACTS_DIR / "upstream_sha.txt"
ATTRIBUTION_TEMPLATE = "# Sourced from FixOps ({sha})"
BANNER_WIDTH = "# ----------------------------------------"


@dataclass
class UpstreamFile:
    path: str
    language: str
    module: str | None


@dataclass
class ImportRequest:
    capability: str
    candidates: List[UpstreamFile]


def load_index() -> Dict[str, UpstreamFile]:
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
    return records


def tokenize_capability(capability: str) -> List[str]:
    tokens: List[str] = []
    for segment in capability.replace("-", ".").split('.'):
        cleaned = segment.strip().lower()
        if cleaned:
            tokens.append(cleaned)
    return tokens


def find_candidates(capability: str, records: Dict[str, UpstreamFile]) -> List[UpstreamFile]:
    tokens = tokenize_capability(capability)
    matches: List[UpstreamFile] = []
    for record in records.values():
        haystack = record.path.lower()
        if all(token in haystack for token in tokens):
            matches.append(record)
    matches.sort(key=lambda item: item.path)
    return matches


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


def build_import_plan(capabilities: Sequence[str], records: Dict[str, UpstreamFile]) -> List[ImportRequest]:
    plan: List[ImportRequest] = []
    for capability in capabilities:
        candidates = find_candidates(capability, records)
        plan.append(ImportRequest(capability=capability, candidates=candidates))
    return plan


def write_import_map(mapping: Dict[str, Dict[str, str]]) -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS_DIR / "upstream_map.json").write_text(
        json.dumps(mapping, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Selectively import FixOps capabilities")
    parser.add_argument("capabilities", nargs="+", help="Capability identifiers to import")
    parser.add_argument("--dest-root", default=".", help="Destination root override")
    args = parser.parse_args(argv)

    records = load_index()
    plan = build_import_plan(args.capabilities, records)
    sha = SHA_PATH.read_text(encoding="utf-8").strip() if SHA_PATH.is_file() else "unknown"
    dest_root = Path(args.dest_root).resolve()

    import_map: Dict[str, Dict[str, str]] = {}
    gaps: List[str] = []

    for request in plan:
        if not request.candidates:
            gaps.append(request.capability)
            continue
        selected = request.candidates[0]
        source_path = selected.path
        dest_path = dest_root / source_path
        copy_file(selected, dest_path, sha)
        import_map[source_path] = {
            "destination": dest_path.relative_to(dest_root).as_posix(),
            "sha256": calculate_sha256(dest_path),
        }

    write_import_map(import_map)

    if gaps:
        raise SystemExit(f"GAP: missing upstream capabilities: {', '.join(gaps)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
