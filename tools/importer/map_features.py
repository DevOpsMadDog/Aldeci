"""Map mined FixOps features to imported symbols for reuse tracking."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS_DIR = ROOT / "artifacts"
REPORTS_DIR = ROOT / "reports"
DOC_INDEX_PATH = ARTIFACTS_DIR / "upstream_doc_index.json"
SYMBOL_INDEX_PATH = ARTIFACTS_DIR / "upstream_symbol_index.json"
FEATURE_MAP_PATH = ARTIFACTS_DIR / "feature_to_symbol_map.json"


def _load_json(path: Path) -> Dict[str, object]:
    if not path.is_file():
        raise FileNotFoundError(f"Required artifact missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _confidence(mentions: int, symbols: int, files: int) -> float:
    score = 0.0
    score += min(mentions, 5) * 0.1
    score += min(symbols, 5) * 0.12
    score += min(files, 5) * 0.08
    return round(min(score, 1.0), 2)


def _format_table_row(values: Iterable[str]) -> str:
    return "| " + " | ".join(values) + " |"


def build_feature_map() -> Tuple[Dict[str, Dict[str, List[str]]], List[str], str]:
    doc_index = _load_json(DOC_INDEX_PATH)
    symbol_index = _load_json(SYMBOL_INDEX_PATH)
    features = doc_index.get("features", {}) if isinstance(doc_index, dict) else {}
    symbols = symbol_index.get("symbols", {}) if isinstance(symbol_index, dict) else {}

    feature_map: Dict[str, Dict[str, List[str]]] = {}
    report_lines: List[str] = []
    report_lines.append("# Upstream Deep Dive")
    report_lines.append("")
    report_lines.append(
        "Generated from tools/importer/mine_docs.py and tools/importer/map_features.py."
    )
    report_lines.append("")
    header = [
        "Feature",
        "Mentions",
        "Candidate Symbols",
        "Candidate Files",
        "Confidence",
    ]
    report_lines.append(_format_table_row(header))
    report_lines.append(_format_table_row(["---"] * len(header)))

    missing: List[str] = []

    for feature, payload in sorted(features.items()):
        mentions = payload.get("mentions", []) if isinstance(payload, dict) else []
        candidate_symbols = payload.get("candidate_symbols", []) if isinstance(payload, dict) else []
        candidate_files = payload.get("candidate_files", []) if isinstance(payload, dict) else []
        mention_count = len(mentions)
        symbol_names = [str(item) for item in candidate_symbols[:10]]
        file_paths = [str(item) for item in candidate_files[:10]]
        confidence = _confidence(mention_count, len(symbol_names), len(file_paths))
        if not symbol_names and not file_paths:
            missing.append(feature)
        feature_map[feature] = {
            "symbols": symbol_names,
            "files": file_paths,
        }
        report_lines.append(
            _format_table_row(
                [
                    feature,
                    str(mention_count),
                    "<br>".join(symbol_names) or "—",
                    "<br>".join(file_paths) or "—",
                    f"{confidence:.2f}",
                ]
            )
        )

    report_lines.append("")
    report_lines.append("## Missing in Upstream")
    report_lines.append("")
    if missing:
        for feature in missing:
            report_lines.append(f"- {feature}")
    else:
        report_lines.append("- None detected")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.joinpath("UPSTREAM_DEEP_DIVE.md").write_text(
        "\n".join(report_lines) + "\n", encoding="utf-8"
    )
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    FEATURE_MAP_PATH.write_text(
        json.dumps(feature_map, indent=2, sort_keys=True), encoding="utf-8"
    )
    return feature_map, missing, "\n".join(report_lines)


def main() -> int:
    feature_map, missing, _ = build_feature_map()
    print(f"Mapped {len(feature_map)} features. Missing: {len(missing)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
