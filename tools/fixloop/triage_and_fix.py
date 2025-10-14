"""Automated bug gate workflow for Aldeci scenarios."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PATCH_ROOT = ROOT / "patches" / "fixops"
REPORT_ROOT = ROOT / "reports" / "fixloop"
EXECUTION_MAP = ROOT / "apps" / "registry" / "execution_map.py"


TEMPLATE = """# Fixloop Report

- Scenario: {scenario_id}
- Overlay: {overlay}
- Backend: {backend}
- Failure: {failure_summary}

Steps:
1. Review generated test under `tests/scenarios/{scenario_id}_regression.py`.
2. Edit the patch skeleton in `{patch_path}` referencing the upstream file & SHA.
3. Update artifacts/upstream_map.json marking the patched file.
4. Commit changes and open a PR via the standard workflow.
"""


def ensure_branch(branch: str) -> None:
    subprocess.run(["git", "checkout", "-B", branch], cwd=ROOT, check=True)


def scaffold_test(scenario_id: str) -> Path:
    tests_dir = ROOT / "tests" / "scenarios"
    tests_dir.mkdir(parents=True, exist_ok=True)
    path = tests_dir / f"test_{scenario_id}_regression.py"
    if path.exists():
        return path
    path.write_text(
        """from tools.e2e.run_matrix import main as run_matrix_main


def test_regression():
    run_matrix_main()
""",
        encoding="utf-8",
    )
    return path


def scaffold_patch(upstream_path: str, scenario_id: str) -> Path:
    patch_dir = PATCH_ROOT / Path(upstream_path).parent
    patch_dir.mkdir(parents=True, exist_ok=True)
    patch_path = patch_dir / f"{Path(upstream_path).name}.{scenario_id}.patch"
    if patch_path.exists():
        return patch_path
    header = (
        f"# Patch for {upstream_path}\n"
        f"# Source-SHA: <fill-upstream-sha>\n"
        f"# Scenario: {scenario_id}\n"
    )
    patch_path.write_text(header, encoding="utf-8")
    return patch_path


def run_tests() -> None:
    subprocess.run(["pytest", "-q"], cwd=ROOT, check=False)


def record_report(scenario_id: str, overlay: str, backend: str, failure: str, patch_path: Path) -> None:
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    report = REPORT_ROOT / f"{scenario_id}.md"
    report.write_text(
        TEMPLATE.format(
            scenario_id=scenario_id,
            overlay=overlay,
            backend=backend,
            failure_summary=failure,
            patch_path=patch_path,
        ),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Triage a failing scenario")
    parser.add_argument("result", type=Path, help="Path to failing result.json")
    parser.add_argument("--upstream", required=True, help="Relative upstream file to patch")
    args = parser.parse_args()

    data = json.loads(args.result.read_text(encoding="utf-8"))
    scenario_id = data["scenario"]
    overlay = data["overlay"]
    backend = data["backend"]
    failure = json.dumps(data.get("invariant_report", {}))

    branch = f"fix/{scenario_id}"
    ensure_branch(branch)
    test_path = scaffold_test(scenario_id)
    patch_path = scaffold_patch(args.upstream, scenario_id)
    run_tests()
    record_report(scenario_id, overlay, backend, failure, patch_path)
    print(f"Fix branch {branch} prepared with test {test_path}")


if __name__ == "__main__":
    main()
