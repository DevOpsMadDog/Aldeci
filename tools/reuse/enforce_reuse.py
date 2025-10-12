"""Enforce reuse guardrails for the AlDeci repository."""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[2]
INDEX_PATH = ROOT / "artifacts" / "upstream_symbol_index.json"
HOT_PATHS = [
    ROOT / "services",
    ROOT / "infra" / "feeds",
    ROOT / "infra" / "signing",
]
STUB_MARKERS = ["raise NotImplementedError", "# stub", "TODO stub"]
SKIP_PREFIXES = {".git", ".upstream", "artifacts", "reports", "__pycache__", ".venv"}


def iter_python_files(base_paths: Sequence[Path]) -> Iterable[Path]:
    for base in base_paths:
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if any(part in SKIP_PREFIXES for part in path.parts):
                continue
            yield path


def extract_top_level_symbols(tree: ast.AST) -> Tuple[List[str], List[str]]:
    classes: List[str] = []
    functions: List[str] = []
    for node in tree.body if isinstance(tree, ast.Module) else []:
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, ast.FunctionDef):
            functions.append(node.name)
        elif isinstance(node, ast.AsyncFunctionDef):
            functions.append(node.name)
    return classes, functions


def check_stub_markers() -> List[str]:
    offenders: List[str] = []
    for path in iter_python_files(HOT_PATHS):
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in STUB_MARKERS):
            offenders.append(path.relative_to(ROOT).as_posix())
    return offenders


def load_symbol_index() -> Dict[str, str]:
    if not INDEX_PATH.is_file():
        raise FileNotFoundError("Missing upstream symbol index; run index_upstream.py first.")
    payload = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    return payload.get("symbols", {})


def project_symbols() -> Dict[str, str]:
    symbols: Dict[str, str] = {}
    targets = [
        ROOT / "apps",
        ROOT / "cli",
        ROOT / "domain",
        ROOT / "services",
        ROOT / "infra",
        ROOT / "tools",
    ]
    for path in iter_python_files(targets):
        rel = path.relative_to(ROOT).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        classes, functions = extract_top_level_symbols(tree)
        module = rel[:-3].replace("/", ".")
        for cls in classes:
            symbols[f"{module}.{cls}"] = rel
        for func in functions:
            symbols[f"{module}.{func}"] = rel
    return symbols


def check_reimplementation(upstream_symbols: Dict[str, str], local_symbols: Dict[str, str]) -> List[Tuple[str, str, str]]:
    conflicts: List[Tuple[str, str, str]] = []
    for name, local_path in local_symbols.items():
        upstream_path = upstream_symbols.get(name)
        if upstream_path and upstream_path != local_path:
            conflicts.append((name, upstream_path, local_path))
    return conflicts


def main() -> int:
    stub_offenders = check_stub_markers()
    if stub_offenders:
        for path in stub_offenders:
            print(f"Stub marker found in hot path: {path}", file=sys.stderr)
        raise SystemExit("reuse-check failed: stub markers detected")

    upstream_symbols = load_symbol_index()
    local_symbols = project_symbols()
    conflicts = check_reimplementation(upstream_symbols, local_symbols)
    if conflicts:
        for name, upstream_path, local_path in conflicts:
            print(
                f"Symbol '{name}' already provided upstream in {upstream_path}; local copy in {local_path}",
                file=sys.stderr,
            )
        raise SystemExit("reuse-check failed: re-implementation detected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
