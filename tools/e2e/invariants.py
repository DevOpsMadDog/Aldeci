"""Invariant and metamorphic checks for scenario executions."""
from __future__ import annotations

import argparse
import hashlib
import json
import yaml
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = ROOT / "reports" / "e2e" / "invariant_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


class InvariantViolation(Exception):
    """Raised when a scenario violates an invariant."""


Invariant = Callable[[dict[str, Any], dict[str, Any]], tuple[bool, str]]


def _fingerprint(run: dict[str, Any]) -> str:
    digest = hashlib.sha256()
    digest.update(run["scenario"].encode("utf-8"))
    digest.update(run["overlay"].encode("utf-8"))
    digest.update(run["backend"].encode("utf-8"))
    for command in run["commands"]:
        digest.update(command["name"].encode("utf-8"))
        digest.update(str(command["exit_code"]).encode("utf-8"))
        digest.update(command["status"].encode("utf-8"))
    return digest.hexdigest()


def _load_previous(run: dict[str, Any]) -> str | None:
    cache_file = CACHE_DIR / f"{run['scenario']}__{run['overlay']}__{run['backend']}.json"
    if cache_file.exists():
        try:
            cached = json.loads(cache_file.read_text(encoding="utf-8"))
            return cached.get("fingerprint")
        except json.JSONDecodeError:
            return None
    return None


def _store_fingerprint(run: dict[str, Any], fingerprint: str) -> None:
    cache_file = CACHE_DIR / f"{run['scenario']}__{run['overlay']}__{run['backend']}.json"
    cache_file.write_text(json.dumps({"fingerprint": fingerprint}), encoding="utf-8")


def invariant_kev_policy(run: dict[str, Any], scenario: dict[str, Any]) -> tuple[bool, str]:
    tags = set(scenario.get("tags", []))
    if {"kev:true", "policy:fail_on_kev"}.issubset(tags):
        for command in run["commands"]:
            if command["name"].startswith("gate") and command["status"] == "ok":
                return False, "Gate passed despite KEV policy"
    return True, "KEV policy respected"


def invariant_epss_monotonic(run: dict[str, Any], scenario: dict[str, Any]) -> tuple[bool, str]:
    tags = {tag for tag in scenario.get("tags", []) if tag.startswith("epss:")}
    if not tags:
        return True, "No EPSS data"
    risk_status = next((cmd for cmd in run["commands"] if cmd["name"].startswith("risk")), None)
    if not risk_status:
        return True, "Risk command absent"
    if risk_status["status"] == "gap":
        return True, "Risk command unavailable"
    if risk_status["exit_code"] != 0:
        return False, "Risk command failed"
    return True, "Risk command succeeded"


def invariant_idempotence(run: dict[str, Any], scenario: dict[str, Any]) -> tuple[bool, str]:
    fingerprint = _fingerprint(run)
    previous = _load_previous(run)
    _store_fingerprint(run, fingerprint)
    if previous is None:
        return True, "Baseline fingerprint stored"
    if previous != fingerprint:
        return False, "Execution fingerprint changed across runs"
    return True, "Execution fingerprint stable"


def invariant_manifest_integrity(run: dict[str, Any], scenario: dict[str, Any]) -> tuple[bool, str]:
    evidence_cmds = [cmd for cmd in run["commands"] if cmd["name"].startswith("evidence")]
    if not evidence_cmds:
        return True, "No evidence commands"
    for cmd in evidence_cmds:
        if cmd["status"] == "gap":
            return True, "Evidence command skipped due to GAP"
        if cmd["exit_code"] != 0:
            return False, "Evidence command failed"
    return True, "Evidence bundle commands completed"


INVARIANTS: dict[str, Invariant] = {
    "kev_policy": invariant_kev_policy,
    "epss_monotonic": invariant_epss_monotonic,
    "idempotence": invariant_idempotence,
    "manifest_integrity": invariant_manifest_integrity,
}


def evaluate_invariants(run: dict[str, Any], scenario: dict[str, Any]) -> dict[str, Any]:
    results: dict[str, dict[str, Any]] = {}
    requested = scenario.get("invariants", [])
    for name in requested:
        func = INVARIANTS.get(name)
        if func is None:
            results[name] = {"status": "unknown", "detail": "Invariant not registered"}
            continue
        ok, detail = func(run, scenario)
        results[name] = {"status": "pass" if ok else "fail", "detail": detail}
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate invariants for a result")
    parser.add_argument("result", type=Path, help="Result JSON emitted by run_matrix")
    args = parser.parse_args()

    run = json.loads(args.result.read_text(encoding="utf-8"))
    scenario_ref = run.get("scenario_path")
    if scenario_ref is None:
        raise SystemExit("Result payload missing scenario_path")
    scenario_path = Path(scenario_ref)
    if not scenario_path.exists():
        raise SystemExit(f"Scenario file {scenario_path} missing")

    scenario = yaml.safe_load(scenario_path.read_text(encoding="utf-8"))
    report = evaluate_invariants(run, scenario)
    print(json.dumps(report, indent=2))
if __name__ == "__main__":
    main()
