"""Ensure overlay configuration and generated documentation remain consistent."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.registry.execution_map import EXECUTION_REGISTRY
DOCS = ROOT / "docs"
CONFIG = ROOT / "config"
ANCHOR_TEXT = "These docs are generated from apps/registry/execution_map.py."


def _load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def test_overlays_load_successfully() -> None:
    demo = _load_yaml(CONFIG / "overlay.demo.yml")
    enterprise = _load_yaml(CONFIG / "overlay.enterprise.yml")
    assert demo, "Demo overlay should load into a mapping"
    assert enterprise, "Enterprise overlay should load into a mapping"


def test_registry_reports_available_capability() -> None:
    available = [cap for cap, meta in EXECUTION_REGISTRY.items() if meta.get("available")]
    assert available, "At least one capability must be marked available"


def test_docs_include_generation_anchor() -> None:
    for path in (DOCS / "API_CLI_MAP.md", DOCS / "INTERACTIONS.md"):
        content = path.read_text(encoding="utf-8")
        assert ANCHOR_TEXT in content, f"Expected anchor text missing from {path.name}"
