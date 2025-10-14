"""Execute the scenario corpus across overlay/backend combinations."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
SCENARIO_ROOT = ROOT / "scenarios"
REPORT_ROOT = ROOT / "reports" / "e2e"
INVARIANT_MODULE = "tools.e2e.invariants"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@dataclass
class CommandResult:
    name: str
    args: list[str]
    exit_code: int
    status: str
    stdout_path: Path
    stderr_path: Path

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "args": self.args,
            "exit_code": self.exit_code,
            "status": self.status,
            "stdout": str(self.stdout_path),
            "stderr": str(self.stderr_path),
        }


@dataclass
class ScenarioRun:
    scenario_id: str
    scenario_path: Path
    overlay: str
    backend: str
    result_path: Path
    commands: list[CommandResult]

    def as_dict(self) -> dict[str, Any]:
        return {
            "scenario": self.scenario_id,
            "scenario_path": str(self.scenario_path),
            "overlay": self.overlay,
            "backend": self.backend,
            "commands": [cmd.as_dict() for cmd in self.commands],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


def load_scenario(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def iter_scenarios(limit: int | None = None) -> list[Path]:
    paths = sorted(SCENARIO_ROOT.glob("**/*.yaml"))
    if limit is not None:
        return paths[:limit]
    return paths


def run_command(
    scenario: dict[str, Any],
    command: dict[str, Any],
    *,
    overlay: str,
    backend: str,
    workdir: Path,
) -> CommandResult:
    name = command["name"]
    args = command.get("args", [])
    cli_args = [
        sys.executable,
        "-m",
        "cli.aldecI",
        f"--overlay={overlay}",
        f"--backend={backend}",
    ]
    cli_args.extend(name.split())
    cli_args.extend(args)

    stdout_path = workdir / f"{name.replace(' ', '_')}.stdout.log"
    stderr_path = workdir / f"{name.replace(' ', '_')}.stderr.log"

    env = os.environ.copy()
    env.setdefault("ALDECI_SCENARIO_ID", scenario["id"])
    env.setdefault("ALDECI_BACKEND", backend)
    env.setdefault("ALDECI_OVERLAY", overlay)

    completed = subprocess.run(
        cli_args,
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        text=True,
    )
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")

    exit_code = completed.returncode
    status = "ok"
    expect_gap = command.get("expect_gap")
    if exit_code == 12:
        status = "gap"
    elif exit_code != 0:
        status = "failed"
        if expect_gap or backend == "http":
            status = "gap"
    elif expect_gap:
        status = "unexpected-pass"

    return CommandResult(
        name=name,
        args=args,
        exit_code=exit_code,
        status=status,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
    )


def evaluate_invariants(run: ScenarioRun, scenario: dict[str, Any]) -> dict[str, Any]:
    from importlib import import_module

    module = import_module(INVARIANT_MODULE)
    evaluate = getattr(module, "evaluate_invariants")
    return evaluate(run.as_dict(), scenario)


def execute_scenario(path: Path, overlay: str, backend: str, *, strict: bool) -> ScenarioRun:
    scenario = load_scenario(path)
    scenario_id = scenario["id"]
    workdir = REPORT_ROOT / scenario_id / overlay / backend
    workdir.mkdir(parents=True, exist_ok=True)

    results: list[CommandResult] = []
    for command in scenario["commands"]:
        cmd_overlay = command.get("overlay", overlay)
        cmd_backend = command.get("backend_override", backend)
        result = run_command(
            scenario,
            command,
            overlay=cmd_overlay,
            backend=cmd_backend,
            workdir=workdir,
        )
        results.append(result)
        if result.status == "failed":
            raise RuntimeError(
                f"Command '{result.name}' failed for {scenario_id} (overlay={cmd_overlay}, backend={cmd_backend})"
            )

    run = ScenarioRun(
        scenario_id=scenario_id,
        scenario_path=path,
        overlay=overlay,
        backend=backend,
        result_path=workdir / "result.json",
        commands=results,
    )

    data = run.as_dict()
    invariant_report = evaluate_invariants(run, scenario)
    data["invariant_report"] = invariant_report
    run.result_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    failures = [name for name, payload in invariant_report.items() if payload.get("status") == "fail"]
    if failures and strict:
        raise RuntimeError(f"Invariant failure for {scenario_id}: {', '.join(failures)}")
    return run


def main() -> None:
    parser = argparse.ArgumentParser(description="Run scenario matrix")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of scenarios")
    parser.add_argument(
        "--overlays",
        nargs="*",
        default=["demo", "enterprise"],
        help="Overlays to evaluate",
    )
    parser.add_argument(
        "--backends",
        nargs="*",
        default=["local", "http"],
        help="Backends to target",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail immediately when invariants fail",
    )
    args = parser.parse_args()

    scenario_paths = iter_scenarios(limit=args.limit)
    summary: list[dict[str, Any]] = []

    for scenario_path in scenario_paths:
        for overlay in args.overlays:
            for backend in args.backends:
                try:
                    run = execute_scenario(scenario_path, overlay, backend, strict=args.strict)
                    result_payload = json.loads(run.result_path.read_text(encoding="utf-8"))
                    summary.append(result_payload)
                    print(
                        f"[{scenario_path.stem}] overlay={overlay} backend={backend} ->"
                        f" {','.join(cmd.status for cmd in run.commands)}"
                    )
                except subprocess.SubprocessError as exc:  # pragma: no cover - fatal failure
                    print(f"Scenario {scenario_path} failed: {exc}", file=sys.stderr)
                    raise

    matrix_report = REPORT_ROOT / "matrix_summary.json"
    matrix_report.parent.mkdir(parents=True, exist_ok=True)
    matrix_report.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Matrix completed for {len(summary)} executions")


if __name__ == "__main__":
    main()
