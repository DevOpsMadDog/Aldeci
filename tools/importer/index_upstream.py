"""Clone and index the upstream FixOps repository."""
from __future__ import annotations

import ast
import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

REPO_URL = "https://github.com/DevOpsMadDog/Fixops.git"
ROOT = Path(__file__).resolve().parents[2]
UPSTREAM_DIR = ROOT / ".upstream" / "Fixops"
ARTIFACTS_DIR = ROOT / "artifacts"
DEFAULT_TARGET_DIRS = [
    "apps",
    "core",
    "enterprise",
    "prototypes",
    "scripts",
    "tests",
]

LANGUAGE_MAP = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".go": "Go",
    ".json": "JSON",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".md": "Markdown",
}


@dataclass
class SymbolRecord:
    path: str
    language: str
    module: str | None
    classes: List[str]
    functions: List[str]


def clone_upstream() -> None:
    if UPSTREAM_DIR.exists():
        shutil.rmtree(UPSTREAM_DIR)
    UPSTREAM_DIR.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "clone", "--depth", "1", REPO_URL, str(UPSTREAM_DIR)],
        check=True,
    )


def iter_python_files(target_dirs: Sequence[str]) -> Iterable[Path]:
    for directory in target_dirs:
        base = UPSTREAM_DIR / directory
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            yield path


def detect_language(path: Path) -> str:
    return LANGUAGE_MAP.get(path.suffix.lower(), "Unknown")


def load_module_map(files: Iterable[Path]) -> Dict[str, str]:
    module_map: Dict[str, str] = {}
    for path in files:
        rel = path.relative_to(UPSTREAM_DIR).as_posix()
        module_map[rel] = rel[:-3].replace("/", ".")
    return module_map


def extract_top_level_symbols(tree: ast.AST) -> tuple[List[str], List[str]]:
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


def collect_symbol_records(target_dirs: Sequence[str]) -> List[SymbolRecord]:
    files = list(iter_python_files(target_dirs))
    module_map = load_module_map(files)
    records: List[SymbolRecord] = []
    for path in files:
        rel = path.relative_to(UPSTREAM_DIR).as_posix()
        module = module_map.get(rel)
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        classes, functions = extract_top_level_symbols(tree)
        records.append(
            SymbolRecord(
                path=rel,
                language="Python",
                module=module,
                classes=classes,
                functions=functions,
            )
        )
    return records


def include_non_python(records: List[SymbolRecord]) -> List[SymbolRecord]:
    tracked_paths = {record.path for record in records}
    new_records = list(records)
    for path in UPSTREAM_DIR.rglob("*"):
        if path.is_dir() or path.name.startswith(".git"):
            continue
        rel = path.relative_to(UPSTREAM_DIR).as_posix()
        if rel in tracked_paths:
            continue
        language = detect_language(path)
        new_records.append(
            SymbolRecord(
                path=rel,
                language=language,
                module=None,
                classes=[],
                functions=[],
            )
        )
    new_records.sort(key=lambda item: item.path)
    return new_records


def build_symbol_map(records: Sequence[SymbolRecord]) -> Dict[str, str]:
    symbol_map: Dict[str, str] = {}
    for record in records:
        if not record.module:
            continue
        for cls in record.classes:
            symbol_map[f"{record.module}.{cls}"] = record.path
        for func in record.functions:
            symbol_map[f"{record.module}.{func}"] = record.path
    return symbol_map


def write_artifacts(records: Sequence[SymbolRecord], sha: str) -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "upstream": {
            "repository": "Fixops",
            "sha": sha,
        },
        "files": [
            {
                "path": record.path,
                "language": record.language,
                "module": record.module,
                "classes": record.classes,
                "functions": record.functions,
            }
            for record in records
        ],
        "symbols": build_symbol_map(records),
    }
    (ARTIFACTS_DIR / "upstream_symbol_index.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (ARTIFACTS_DIR / "upstream_sha.txt").write_text(sha + "\n", encoding="utf-8")


def get_upstream_sha() -> str:
    result = subprocess.run(
        ["git", "-C", str(UPSTREAM_DIR), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def main() -> None:
    clone_upstream()
    records = collect_symbol_records(DEFAULT_TARGET_DIRS)
    records = include_non_python(records)
    sha = get_upstream_sha()
    write_artifacts(records, sha)


if __name__ == "__main__":
    main()
