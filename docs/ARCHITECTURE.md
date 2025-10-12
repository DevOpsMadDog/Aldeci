# AlDeci Platform Architecture (Phase 0)

The AlDeci platform bootstraps a modular assurance pipeline that mirrors the
FixOps blueprint. The repository is organised around clear responsibility
boundaries:

- **Apps** deliver ingress and presentation layers. The API (FastAPI) and UI
  shells will later be backed by imported FixOps implementations.
- **Domain** will aggregate shared business concepts and validations imported
  from upstream to avoid drift.
- **Services** encapsulate capability slices such as SBOM normalisation,
  risk scoring, provenance analysis, reproducibility, graph analytics,
  evidence handling, and data normalisation pipelines.
- **Infra** captures integrations for feeds, signing, LLM routing, telemetry,
  and storage. Each sub-system will be wired through overlay-aware
  configuration once the upstream components are imported.
- **Tools** contain reproducible automation for importing upstream code,
  enforcing reuse guardrails, and generating documentation directly from the
  registered capabilities.

Two overlays (`demo` and `enterprise`) define default toggles that downstream
processes will load via the CLI and API when orchestrating workflows. Both
modes share the same binaries but differ in policy strictness and artifact
handling.

This document is intentionally concise. Detailed component inventories,
interaction diagrams, and API/CLI surface area maps will be generated
programmatically in later phases using the docgen toolchain and upstream
registries.
