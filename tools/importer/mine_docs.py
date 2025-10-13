"""Mine upstream FixOps documentation for capability keywords."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[2]
UPSTREAM_ROOT = ROOT / ".upstream" / "Fixops"
ARTIFACTS_DIR = ROOT / "artifacts"
SYMBOL_INDEX_PATH = ARTIFACTS_DIR / "upstream_symbol_index.json"
DOC_INDEX_PATH = ARTIFACTS_DIR / "upstream_doc_index.json"

KEYWORDS = [
    "SBOM",
    "SARIF",
    "EPSS",
    "KEV",
    "SLSA",
    "cosign",
    "SSVC",
    "provenance",
    "evidence",
    "graph",
]


@dataclass
class Mention:
    feature: str
    file: Path
    line_number: int
    context: str


def _ensure_upstream() -> None:
    if UPSTREAM_ROOT.is_dir():
        subprocess.run(
            ["git", "fetch", "--depth", "1", "origin"],
            cwd=UPSTREAM_ROOT,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    subprocess.check_call(
        [
            "git",
            "clone",
            "--depth",
            "1",
            "https://github.com/fixopsai/Fixops",
            str(UPSTREAM_ROOT),
        ]
    )


def _load_symbol_index() -> Dict[str, str]:
    if not SYMBOL_INDEX_PATH.is_file():
        raise FileNotFoundError(
            "Missing upstream_symbol_index.json. Run tools/importer/index_upstream.py first."
        )
    payload = json.loads(SYMBOL_INDEX_PATH.read_text(encoding="utf-8"))
    symbols = payload.get("symbols", {})
    return {str(key): str(value) for key, value in symbols.items()}


def _candidate_files(symbol_index: Dict[str, str], keyword: str) -> List[str]:
    matches: List[str] = []
    needle = keyword.lower()
    seen = set()
    for symbol, path in symbol_index.items():
        if needle in symbol.lower() or needle in path.lower():
            if symbol not in seen:
                seen.add(symbol)
                matches.append(symbol)
    return matches


def _candidate_paths(symbol_index: Dict[str, str], keyword: str) -> List[str]:
    needle = keyword.lower()
    paths = {path for path in symbol_index.values() if needle in path.lower()}
    return sorted(paths)


def _iter_readme_files() -> Iterable[Path]:
    for candidate in UPSTREAM_ROOT.glob("*.md"):
        name = candidate.name.lower()
        if "readme" in name:
            yield candidate


def _extract_mentions(keyword: str, path: Path) -> List[Mention]:
    mentions: List[Mention] = []
    pattern = re.compile(rf"\b{re.escape(keyword)}\b", flags=re.IGNORECASE)
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if pattern.search(line):
            mentions.append(
                Mention(
                    feature=keyword.lower(),
                    file=path.relative_to(UPSTREAM_ROOT),
                    line_number=lineno,
                    context=line.strip(),
                )
            )
    return mentions


def mine_docs() -> Dict[str, Dict[str, object]]:
    _ensure_upstream()
    symbol_index = _load_symbol_index()

    feature_index: Dict[str, Dict[str, object]] = {}
    documents = sorted(_iter_readme_files())
    for keyword in KEYWORDS:
        feature_key = keyword.lower()
        feature_index[feature_key] = {
            "keyword": keyword,
            "mentions": [],
            "candidate_symbols": [],
            "candidate_files": [],
        }
        for doc in documents:
            for mention in _extract_mentions(keyword, doc):
                feature_index[feature_key]["mentions"].append(
                    {
                        "file": str(mention.file),
                        "line": mention.line_number,
                        "context": mention.context,
                    }
                )
        candidates = _candidate_files(symbol_index, keyword)
        feature_index[feature_key]["candidate_symbols"] = candidates
        candidate_paths = _candidate_paths(symbol_index, keyword)
        feature_index[feature_key]["candidate_files"] = candidate_paths

    payload = {
        "keywords": KEYWORDS,
        "documents": [str(path.relative_to(UPSTREAM_ROOT)) for path in documents],
        "features": feature_index,
    }
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    DOC_INDEX_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return feature_index


def main() -> int:
    feature_index = mine_docs()
    total_mentions = sum(len(entry.get("mentions", [])) for entry in feature_index.values())
    print(f"Processed {len(feature_index)} features with {total_mentions} doc mentions.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
