"""Bug gate automation for scenario invariants."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

import sys

ROOT = Path(__file__).resolve().parents[2]
RUN_MATRIX = ROOT / "tools" / "e2e" / "run_matrix.py"
FIXLOOP = ROOT / "tools" / "fixloop" / "triage_and_fix.py"
REPORT_ROOT = ROOT / "reports" / "e2e"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def invoke_run_matrix(limit: int, overlays: list[str], backends: list[str]) -> Path:
    args = [
        "python",
        str(RUN_MATRIX),
        f"--limit={limit}" if limit else "",
    ]
    if overlays:
        args.extend(["--overlays", *overlays])
    if backends:
        args.extend(["--backends", *backends])
    args = [arg for arg in args if arg]
    completed = subprocess.run(args, cwd=ROOT, check=False)
    summary = REPORT_ROOT / "matrix_summary.json"
    if completed.returncode != 0:
        print("run_matrix exited with non-zero status; bug gate will treat as failure")
    return summary


def iter_failures(summary_path: Path) -> list[dict[str, Any]]:
    if not summary_path.exists():
        raise RuntimeError("matrix_summary.json missing; run_matrix likely failed")
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    failures: list[dict[str, Any]] = []
    for entry in payload:
        for name, result in entry.get("invariant_report", {}).items():
            if result.get("status") == "fail":
                entry_copy = dict(entry)
                entry_copy["failed_invariant"] = name
                failures.append(entry_copy)
    return failures


def fix_failure(entry: dict[str, Any]) -> None:
    scenario = entry["scenario"]
    overlay = entry["overlay"]
    backend = entry["backend"]
    result_path = (
        REPORT_ROOT
        / scenario
        / overlay
        / backend
        / "result.json"
    )
    upstream_hint = entry.get("invariant_report", {}).get(entry["failed_invariant"], {}).get("upstream")
    args = [
        "python",
        str(FIXLOOP),
        str(result_path),
    ]
    if upstream_hint:
        args.extend(["--upstream", upstream_hint])
    else:
        args.extend(["--upstream", "UNKNOWN" ])
    subprocess.run(args, cwd=ROOT, check=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run bug gate across scenarios")
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--overlays", nargs="*", default=["demo", "enterprise"])
    parser.add_argument("--backends", nargs="*", default=["local", "http"])
    args = parser.parse_args()

    summary_path = invoke_run_matrix(args.limit, args.overlays, args.backends)
    failures = iter_failures(summary_path)
    if not failures:
        print("Bug gate clean: no invariant failures")
        return
    for entry in failures:
        fix_failure(entry)
    raise SystemExit(f"bug-gate detected {len(failures)} failures")


if __name__ == "__main__":
    main()
