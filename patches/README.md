# Patch overlay policy

Patch overlays are the only mechanism to modify imported FixOps logic. All
changes must be captured as discrete `.patch` files under `patches/fixops/`
mirroring the upstream relative path. Each patch must reference the upstream
commit SHA and include only the minimal diff necessary to address the scenario
regression.

Process summary:

1. Reproduce the failure via `tools/e2e/run_matrix.py` or targeted tests.
2. Capture the failing scenario ID and invoke `tools/fixloop/triage_and_fix.py`.
3. The fixloop script creates a branch `fix/<scenario-id>`, generates a focused
   regression test, and scaffolds a patch file under `patches/fixops/`.
4. Edit the patch file to adjust the minimal upstream lines. Never re-implement
   an entire function – use the upstream import and modify behaviour via the
   patch.
5. Update `artifacts/upstream_map.json` marking the touched file with
   `"patched": true` and re-run CI.

If an upstream capability is missing entirely, do not create a patch. Instead
ensure the CLI surfaces `Unavailable` (exit 12 or HTTP 501) and record the GAP
in `artifacts/gaps.json`.
