# Demo Playbook

This document tracks the configuration overlays available from day one.
Detailed workflows and screenshots will be populated once the upstream
FixOps components are imported.

## Demo Overlay

- Local-first storage under `./artifacts`.
- Relaxed enforcement to enable iterative testing.
- Provenance and signing services disabled by default to minimise setup.

## Enterprise Overlay

- Production-like storage backed by object stores.
- Strict enforcement tuned for gated releases.
- Provenance and signing enabled to trace artefacts end-to-end.

More guidance will be generated via automated docgen tooling after registries
are introduced in later phases.
