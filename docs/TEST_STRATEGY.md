# Test Strategy — Phase 5

## Scenario Corpus
- Scenarios are defined using `tools/scenario/schema.yaml` and generated via
  `tools/scenario/generate.py`.
- 1200 scenarios are emitted under `scenarios/<stage>/` covering design, build,
  test, deploy, and operate phases.
- Each scenario tags topology, EPSS band, KEV posture, and overlay metadata.
- The catalog (`tools/scenario/catalog.json`) enumerates the corpus for CI and
  tool consumption.

## End-to-End Harness
- `tools/e2e/run_matrix.py` executes the CLI across overlays (demo & enterprise)
  and backends (local & http).
- Per-scenario reports are written to `reports/e2e/<id>/<overlay>/<backend>/`
  including command logs and invariant results.
- GAP-aware execution honours upstream limitations (exit code 12 / HTTP 501)
  without re-implementing missing functionality.

## Invariants & Metamorphic Checks
- Implemented in `tools/e2e/invariants.py` with the following guards:
  - `kev_policy`: KEV-tagged scenarios with fail-on-KEV policies must not pass
    the gate step.
  - `epss_monotonic`: Ensures risk scoring succeeds for EPSS-tagged cases when
    available.
  - `idempotence`: Execution fingerprints are cached to verify stability across
    reruns.
  - `manifest_integrity`: Evidence bundle commands must complete without error
    when available.

## Bug Gate & Patch Overlay
- Failing invariants trigger `tools/fixloop/triage_and_fix.py`, which prepares a
  `fix/<scenario-id>` branch, scaffolds a regression test, and creates a patch
  skeleton under `patches/fixops/`.
- Patch overlays are applied via `tools/patches/apply_patch.py`; reuse guardrails
  enforce source SHA references and a 50-line diff ceiling.
- All upstream modifications must be captured as patches; missing capabilities
  remain GAPs recorded in `artifacts/gaps.json`.

## CI Integration
- Scenario catalog validation ensures schema conformance.
- Matrix smoke tests execute a representative subset (≥200 scenarios) per run;
  full corpus runs can execute nightly.
- Bug gate fails CI on invariant violations and surfaces scenario IDs for triage.
- Reuse and documentation drift checks remain mandatory.
