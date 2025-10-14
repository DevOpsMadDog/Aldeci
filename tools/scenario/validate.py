"""Validate scenario definitions against the schema."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
SCENARIO_ROOT = ROOT / "scenarios"
SCHEMA_PATH = ROOT / "tools" / "scenario" / "schema.yaml"


try:  # pragma: no cover - optional dependency
    import jsonschema
except Exception:  # pragma: no cover - library may be absent
    jsonschema = None


class ValidationError(Exception):
    """Raised when a scenario fails validation."""


def load_schema() -> dict[str, Any]:
    return yaml.safe_load(SCHEMA_PATH.read_text(encoding="utf-8"))


def validate_schema(schema: dict[str, Any], document: dict[str, Any], path: Path) -> None:
    if jsonschema:
        jsonschema.validate(document, schema)
        return
    required = schema.get("required", [])
    for field in required:
        if field not in document:
            raise ValidationError(f"Missing required field '{field}' in {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate scenario YAML files")
    parser.add_argument("--limit", type=int, default=None, help="Validate only N scenarios")
    args = parser.parse_args()

    schema = load_schema()
    paths = sorted(SCENARIO_ROOT.glob("**/*.yaml"))
    if args.limit is not None:
        paths = paths[: args.limit]

    for path in paths:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        validate_schema(schema, document, path)
    print(f"Validated {len(paths)} scenarios")


if __name__ == "__main__":
    main()
