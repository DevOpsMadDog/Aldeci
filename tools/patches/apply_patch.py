"""Utility for applying FixOps overlay patches within Aldeci."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
PATCH_ROOT = ROOT / "patches" / "fixops"
UPSTREAM_MAP = ROOT / "artifacts" / "upstream_map.json"


def iter_patches() -> Iterable[Path]:
    if not PATCH_ROOT.exists():
        return []
    return sorted(patch for patch in PATCH_ROOT.rglob("*.patch") if patch.is_file())


def apply_patch(patch: Path) -> None:
    rel = patch.relative_to(ROOT)
    print(f"Applying {rel}")
    subprocess.run(["patch", "-p1", "-i", str(patch)], cwd=ROOT, check=True)


def mark_patched(patch: Path) -> None:
    if not UPSTREAM_MAP.exists():
        return
    try:
        data = json.loads(UPSTREAM_MAP.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        data = {}
    if not isinstance(data, dict):
        data = {}
    target = patch.stem.replace("__", "/")
    record = data.setdefault(target, {})
    record["patched"] = True
    UPSTREAM_MAP.write_text(json.dumps(data, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply overlay patches")
    parser.add_argument("--dry-run", action="store_true", help="Validate without applying")
    args = parser.parse_args()

    for patch in iter_patches():
        if args.dry_run:
            print(f"Would apply {patch}")
            continue
        apply_patch(patch)
        mark_patched(patch)


if __name__ == "__main__":
    main()
