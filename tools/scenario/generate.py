"""Scenario corpus generator for Aldeci Phase 5.

This utility mines upstream FixOps samples (when available) and synthesizes a
large scenario corpus that drives the end-to-end matrix harness. The resulting
scenarios live under `scenarios/<stage>/` and are catalogued in
`tools/scenario/catalog.json`.
"""
from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Iterable

import yaml

ROOT = Path(__file__).resolve().parents[2]
SCENARIO_ROOT = ROOT / "scenarios"
CATALOG_PATH = ROOT / "tools" / "scenario" / "catalog.json"
SAMPLES_ROOT = ROOT / "samples" / "fixops_import"
UPSTREAM_ROOT = ROOT / ".upstream" / "Fixops"
WORKSPACE_ROOT = Path("artifacts") / "e2e"

STAGES = ["design", "build", "test", "deploy", "operate"]
DEFAULT_COMMAND_CHAIN = [
    "ingest sbom",
    "risk score",
    "graph lineage",
    "evidence bundle",
    "gate",
]


def load_upstream_samples() -> dict[str, list[Path]]:
    """Return available upstream artifact paths grouped by type."""
    groups: dict[str, list[Path]] = defaultdict(list)
    if not UPSTREAM_ROOT.exists():
        return groups

    for pattern, key in [
        ("**/*.sbom.json", "sbom"),
        ("**/*.sarif", "sarif"),
        ("**/*.sarif.json", "sarif"),
        ("**/*.attestation.json", "attestation"),
        ("**/*.sbom", "sbom"),
        ("**/*.json", "json"),
    ]:
        for path in UPSTREAM_ROOT.glob(pattern):
            if path.is_file() and path.stat().st_size > 0:
                groups[key].append(path)
    return groups


def copy_samples(groups: dict[str, list[Path]]) -> dict[str, list[Path]]:
    """Copy upstream samples into the repository-local fixture directory."""
    SAMPLES_ROOT.mkdir(parents=True, exist_ok=True)
    copied: dict[str, list[Path]] = defaultdict(list)
    for key, paths in groups.items():
        for path in paths:
            rel_name = "_".join(path.parts[-3:])
            dest = SAMPLES_ROOT / f"{key}_{rel_name}"
            if dest.exists():
                continue
            try:
                dest.write_bytes(path.read_bytes())
            except FileNotFoundError:
                continue
            copied[key].append(dest)
    return copied


def synthesize_inputs(groups: dict[str, list[Path]]) -> dict[str, dict[str, str]]:
    """Build a mapping of canonical inputs used across scenarios."""
    inputs: dict[str, dict[str, str]] = {}
    for key, paths in groups.items():
        if not paths:
            continue
        sample = random.choice(paths)
        inputs[f"sample_{key}"] = {
            "source": str(sample.relative_to(ROOT)) if sample.exists() else str(sample),
            "format": key,
        }
    if "sample_sbom" not in inputs:
        inputs["sample_sbom"] = {
            "source": "samples/fixops_import/example.sbom.json",
            "format": "sbom",
        }
    if "sample_sarif" not in inputs:
        inputs["sample_sarif"] = {
            "source": "samples/fixops_import/example.sarif.json",
            "format": "sarif",
        }
    inputs.setdefault(
        "sample_epss",
        {"source": "samples/fixops_import/example.epss.csv", "format": "epss"},
    )
    inputs.setdefault(
        "sample_kev",
        {"source": "samples/fixops_import/example.kev.json", "format": "kev"},
    )
    inputs.setdefault(
        "sample_policy",
        {"source": "samples/fixops_import/example.policy.json", "format": "policy"},
    )
    inputs.setdefault(
        "sample_sbom_quality_json",
        {"source": "samples/fixops_import/example.sbom_quality.json", "format": "quality-json"},
    )
    inputs.setdefault(
        "sample_sbom_quality_html",
        {"source": "samples/fixops_import/example.sbom_quality.html", "format": "quality-html"},
    )
    inputs.setdefault(
        "sample_repro_attestation",
        {"source": "samples/fixops_import/example.repro_attestation.json", "format": "attestation"},
    )
    inputs.setdefault(
        "sample_provenance_dir",
        {"source": "samples/fixops_import/provenance", "format": "dir"},
    )
    return inputs


def workspace_path(scenario_id: str, filename: str) -> str:
    return str((WORKSPACE_ROOT / scenario_id / filename).as_posix())


def command_args(name: str, scenario_id: str, template: dict) -> list[str]:
    normalized_sbom = workspace_path(scenario_id, "normalized_sbom.json")
    risk_report = workspace_path(scenario_id, "risk.json")
    quality = template["quality"]
    feeds = template["feeds"]
    policy = template["policy"]

    if name == "ingest sbom":
        return ["--in", template["inputs"]["sbom"]["source"], "--out", normalized_sbom]
    if name == "risk score":
        return [
            "--sbom",
            normalized_sbom,
            "--epss",
            feeds["epss"],
            "--kev",
            feeds["kev"],
            "--out",
            risk_report,
        ]
    if name == "graph lineage":
        return [
            "--artifact",
            f"{scenario_id}-artifact",
            "--normalized-sbom",
            normalized_sbom,
            "--risk-report",
            risk_report,
        ]
    if name == "evidence bundle":
        return [
            "--release",
            scenario_id,
            "--normalized-sbom",
            normalized_sbom,
            "--sbom-quality-json",
            quality["json"],
            "--sbom-quality-html",
            quality["html"],
            "--risk-report",
            risk_report,
            "--repro-attestation",
            quality["attestation"],
            "--provenance-dir",
            quality["provenance"],
            "--out",
            workspace_path(scenario_id, "evidence.zip"),
        ]
    if name == "gate":
        return [
            "--policy",
            policy,
            "--risk-report",
            risk_report,
            "--provenance-dir",
            quality["provenance"],
            "--repro-attestation",
            quality["attestation"],
        ]
    return []


def build_scenario(stage: str, index: int, template: dict, extra_tags: Iterable[str]) -> dict:
    scenario_id = f"{stage}_{index:04d}"
    description = f"{stage.title()} scenario #{index} covering {template['topology']} topology"
    commands = []
    for name in template["command_chain"]:
        cmd = {"name": name}
        args = command_args(name, scenario_id, template)
        if args:
            cmd["args"] = args
        if name in template.get("gaps", set()):
            cmd["expect_gap"] = True
        commands.append(cmd)
    scenario = {
        "id": scenario_id,
        "stage": stage,
        "description": description,
        "tags": sorted(set(template["tags"]).union(extra_tags)),
        "inputs": template["inputs"],
        "commands": commands,
        "expected": {
            "exit_code": 0,
        },
        "invariants": template["invariants"],
        "skip_if_gap": template.get("skip_if_gap", []),
    }
    return scenario


def generate_scenarios(groups: dict[str, list[Path]], *, count: int) -> list[dict]:
    synthetic_inputs = synthesize_inputs(groups)
    topologies = ["linear", "diamond", "fan-out", "mesh"]
    epss_bands = ["low", "medium", "high", "critical"]
    templates: list[dict] = []
    for topology in topologies:
        for band in epss_bands:
            templates.append(
                {
                    "topology": topology,
                    "tags": {f"topology:{topology}", f"epss:{band}"},
                    "inputs": {
                        "sbom": synthetic_inputs["sample_sbom"],
                        "sarif": synthetic_inputs["sample_sarif"],
                    },
                    "feeds": {
                        "epss": synthetic_inputs["sample_epss"]["source"],
                        "kev": synthetic_inputs["sample_kev"]["source"],
                    },
                    "quality": {
                        "json": synthetic_inputs["sample_sbom_quality_json"]["source"],
                        "html": synthetic_inputs["sample_sbom_quality_html"]["source"],
                        "attestation": synthetic_inputs["sample_repro_attestation"]["source"],
                        "provenance": synthetic_inputs["sample_provenance_dir"]["source"],
                    },
                    "policy": synthetic_inputs["sample_policy"]["source"],
                    "command_chain": DEFAULT_COMMAND_CHAIN,
                    "invariants": [
                        "kev_policy",
                        "epss_monotonic",
                        "idempotence",
                        "manifest_integrity",
                    ],
                    "gaps": set(),
                }
            )
    # Additional variations
    version_lags = [-3, -1, 0, 1, 3]
    for lag in version_lags:
        templates.append(
            {
                "topology": "version-lag",
                "tags": {"topology:version-lag", f"version_lag:{lag}"},
                "inputs": {
                    "sbom": synthetic_inputs["sample_sbom"],
                },
                "feeds": {
                    "epss": synthetic_inputs["sample_epss"]["source"],
                    "kev": synthetic_inputs["sample_kev"]["source"],
                },
                "quality": {
                    "json": synthetic_inputs["sample_sbom_quality_json"]["source"],
                    "html": synthetic_inputs["sample_sbom_quality_html"]["source"],
                    "attestation": synthetic_inputs["sample_repro_attestation"]["source"],
                    "provenance": synthetic_inputs["sample_provenance_dir"]["source"],
                },
                "policy": synthetic_inputs["sample_policy"]["source"],
                "command_chain": ["ingest sbom", "risk score", "gate"],
                "invariants": ["kev_policy", "idempotence"],
                "gaps": set(),
            }
        )
    # KEV focused templates
    templates.append(
        {
            "topology": "kev",
            "tags": {"kev:true", "policy:fail_on_kev"},
            "inputs": {
                "sbom": synthetic_inputs["sample_sbom"],
            },
            "feeds": {
                "epss": synthetic_inputs["sample_epss"]["source"],
                "kev": synthetic_inputs["sample_kev"]["source"],
            },
            "quality": {
                "json": synthetic_inputs["sample_sbom_quality_json"]["source"],
                "html": synthetic_inputs["sample_sbom_quality_html"]["source"],
                "attestation": synthetic_inputs["sample_repro_attestation"]["source"],
                "provenance": synthetic_inputs["sample_provenance_dir"]["source"],
            },
            "policy": synthetic_inputs["sample_policy"]["source"],
            "command_chain": ["ingest sbom", "risk score", "gate"],
            "invariants": ["kev_policy"],
            "gaps": set(),
            "skip_if_gap": ["risk score"],
        }
    )

    scenarios: list[dict] = []
    per_stage = max(count // len(STAGES), 1)
    random.seed(42)

    for stage in STAGES:
        for index in range(per_stage):
            template = random.choice(templates)
            extra_tags = {f"stage:{stage}"}
            scenario = build_scenario(stage, index, template, extra_tags)
            scenarios.append(scenario)

    # ensure at least requested count by adding more variations if necessary
    while len(scenarios) < count:
        stage = random.choice(STAGES)
        template = random.choice(templates)
        index = len([s for s in scenarios if s["stage"] == stage])
        scenario = build_scenario(stage, index, template, {f"stage:{stage}"})
        scenarios.append(scenario)

    return scenarios


def write_scenarios(scenarios: list[dict]) -> None:
    for stage in STAGES:
        (SCENARIO_ROOT / stage).mkdir(parents=True, exist_ok=True)

    catalog: list[dict] = []
    for scenario in scenarios:
        stage = scenario["stage"]
        scenario_path = SCENARIO_ROOT / stage / f"{scenario['id']}.yaml"
        with scenario_path.open("w", encoding="utf-8") as fh:
            yaml.safe_dump(scenario, fh, sort_keys=False)
        catalog.append(
            {
                "id": scenario["id"],
                "stage": stage,
                "path": str(scenario_path.relative_to(ROOT)),
                "tags": scenario.get("tags", []),
            }
        )

    CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CATALOG_PATH.open("w", encoding="utf-8") as fh:
        json.dump({"scenarios": catalog}, fh, indent=2)



def main() -> None:
    parser = argparse.ArgumentParser(description="Generate scenario corpus")
    parser.add_argument(
        "--count",
        type=int,
        default=1200,
        help="Number of scenarios to generate (minimum).",
    )
    args = parser.parse_args()

    groups = load_upstream_samples()
    if groups:
        groups = copy_samples(groups)

    scenarios = generate_scenarios(groups, count=max(args.count, 1000))
    write_scenarios(scenarios)
    print(f"Generated {len(scenarios)} scenarios")


if __name__ == "__main__":
    main()
