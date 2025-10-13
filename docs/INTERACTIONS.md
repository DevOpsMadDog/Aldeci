# System Interactions

> These docs are generated from apps/registry/execution_map.py.
> Additional inputs: cli/aldecI.py and apps/api/app.py.

## evidence.bundle

**Availability:** ✅ Available

**What it does:** Assemble signed evidence bundles with policy evaluation results.

**Overlays:** demo, enterprise
**Outputs:** artifacts/evidence/<id>.zip, artifacts/evidence/<id>.yaml
**CLI Sample:** `aldecI evidence bundle --release <id> --out artifacts/evidence/<id>.zip --backend local --overlay demo`
**HTTP Sample:** `curl -sS -X POST http://127.0.0.1:8000/v1/evidence/bundle -H 'Content-Type: application/json' -d @payload.json`

**Function call chain:**

CLI `aldecI evidence bundle --release <id> --out artifacts/evidence/<id>.zip` -> Local backend `apps.runtime.local_handlers.handle_evidence_bundle` -> SDK `sdk.python.fixops_client.FixopsClient.evidence_bundle` -> FastAPI `apps.api.v1_evidence.bundle` -> Service `services.evidence.packager.load_policy` -> Service `services.evidence.packager.evaluate_policy` -> Service `services.evidence.packager.create_bundle` -> Infra `infra.signing.sign-artifact.sh`

## gate.check

**Availability:** ✅ Available

**What it does:** Evaluate policy gates against collected evidence.

**Overlays:** demo, enterprise
**Outputs:** artifacts/gate/report.json
**CLI Sample:** `aldecI gate --policy config/policy.yml --backend local --overlay demo`
**HTTP Sample:** `curl -sS -X POST http://127.0.0.1:8000/v1/gate/check -H 'Content-Type: application/json' -d @payload.json`

**Function call chain:**

CLI `aldecI gate --policy config/policy.yml` -> Local backend `apps.runtime.local_handlers.handle_gate_check` -> SDK `sdk.python.fixops_client.FixopsClient.gate_check` -> FastAPI `apps.api.v1_gate.check` -> Service `services.evidence.packager.evaluate_policy`

## graph.anomalies

**Availability:** ✅ Available

**What it does:** Detect release timeline anomalies across the provenance graph.

**Overlays:** demo, enterprise
**Outputs:** artifacts/graph/anomalies.json
**CLI Sample:** `aldecI graph anomalies --type version-drift --backend local --overlay demo`
**HTTP Sample:** `curl -sS -X GET http://127.0.0.1:8000/v1/graph/anomalies -H 'Content-Type: application/json' -d @payload.json`

**Function call chain:**

CLI `aldecI graph anomalies --type version-drift` -> Local backend `apps.runtime.local_handlers.handle_graph_anomalies` -> SDK `sdk.python.fixops_client.FixopsClient.graph_anomalies` -> FastAPI `apps.api.v1_graph.anomalies` -> Service `services.graph.graph.ProvenanceGraph.detect_version_anomalies` -> Service `services.graph.graph.build_graph_from_sources` -> Infra `telemetry.configure`

## graph.kev_in_last

**Availability:** ✅ Available

**What it does:** Identify components linked to KEV CVEs in the most recent releases.

**Overlays:** demo, enterprise
**Outputs:** artifacts/graph/kev_components.json
**CLI Sample:** `aldecI graph kev-in-last --releases <N> --backend local --overlay demo`
**HTTP Sample:** `curl -sS -X GET http://127.0.0.1:8000/v1/graph/kev-in-last -H 'Content-Type: application/json' -d @payload.json`

**Function call chain:**

CLI `aldecI graph kev-in-last --releases <N>` -> Local backend `apps.runtime.local_handlers.handle_graph_kev` -> SDK `sdk.python.fixops_client.FixopsClient.graph_kev` -> FastAPI `apps.api.v1_graph.kev_in_last` -> Service `services.graph.graph.ProvenanceGraph.components_with_kev` -> Service `services.graph.graph.build_graph_from_sources` -> Infra `telemetry.configure`

## graph.lineage

**Availability:** ✅ Available

**What it does:** Construct provenance graphs and return artefact lineage traversals.

**Overlays:** demo, enterprise
**Outputs:** artifacts/graph/lineage.json
**CLI Sample:** `aldecI graph lineage --artifact <id|path> --backend local --overlay demo`
**HTTP Sample:** `curl -sS -X GET http://127.0.0.1:8000/v1/graph/lineage -H 'Content-Type: application/json' -d @payload.json`

**Function call chain:**

CLI `aldecI graph lineage --artifact <id|path>` -> Local backend `apps.runtime.local_handlers.handle_graph_lineage` -> SDK `sdk.python.fixops_client.FixopsClient.graph_lineage` -> FastAPI `apps.api.v1_graph.lineage` -> Service `services.graph.graph.ProvenanceGraph.lineage` -> Service `services.graph.graph.build_graph_from_sources` -> Infra `telemetry.configure`

## ingest.sarif

**Availability:** ✅ Available

**What it does:** Parse SARIF logs, harmonise severities, and summarise findings.

**Overlays:** demo, enterprise
**Outputs:** artifacts/sarif/normalized.json
**CLI Sample:** `aldecI ingest sarif --in <sarif.json> --out artifacts/sarif/normalized.json --backend local --overlay demo`
**HTTP Sample:** `curl -sS -X POST http://127.0.0.1:8000/v1/ingest/sarif -H 'Content-Type: application/json' -d @payload.json`

**Function call chain:**

CLI `aldecI ingest sarif --in <sarif.json> --out artifacts/sarif/normalized.json` -> Local backend `apps.runtime.local_handlers.handle_ingest_sarif` -> SDK `sdk.python.fixops_client.FixopsClient.ingest_sarif` -> FastAPI `apps.api.v1_ingest.ingest_sarif` -> Service `services.normalize.normalizers.InputNormalizer.load_sarif`

## ingest.sbom

**Availability:** ✅ Available

**What it does:** Normalise CycloneDX/SPDX SBOM payloads to a canonical structure.

**Overlays:** demo, enterprise
**Outputs:** artifacts/sbom/normalized.json
**CLI Sample:** `aldecI ingest sbom --in <sbom.json> --out artifacts/sbom/normalized.json --backend local --overlay demo`
**HTTP Sample:** `curl -sS -X POST http://127.0.0.1:8000/v1/ingest/sbom -H 'Content-Type: application/json' -d @payload.json`

**Function call chain:**

CLI `aldecI ingest sbom --in <sbom.json> --out artifacts/sbom/normalized.json` -> Local backend `apps.runtime.local_handlers.handle_ingest_sbom` -> SDK `sdk.python.fixops_client.FixopsClient.ingest_sbom` -> FastAPI `apps.api.v1_ingest.ingest_sbom` -> Service `services.normalize.normalizers.InputNormalizer.load_sbom`

## persona.explain

**Availability:** ✅ Available

**What it does:** Generate risk narratives tailored for specific personas.

**Overlays:** demo, enterprise
**Outputs:** artifacts/persona/<role>.md
**CLI Sample:** `aldecI persona explain --role <role> --risk artifacts/risk.json --backend local --overlay demo`
**HTTP Sample:** `curl -sS -X POST http://127.0.0.1:8000/v1/persona/explain -H 'Content-Type: application/json' -d @payload.json`

**Function call chain:**

CLI `aldecI persona explain --role <role> --risk artifacts/risk.json` -> Local backend `apps.runtime.local_handlers.handle_persona_explain` -> SDK `sdk.python.fixops_client.FixopsClient.persona_explain` -> FastAPI `apps.api.v1_persona.explain` -> Service `services.explainability.ExplainabilityService.prime_baseline` -> Service `services.explainability.ExplainabilityService.explain` -> Service `services.explainability.ExplainabilityService.generate_narrative`

## provenance.attest

**Availability:** ✅ Available

**What it does:** Create SLSA v1 DSSE attestations for build artefacts.

**Overlays:** demo, enterprise
**Outputs:** artifacts/attestations/<id>.json
**CLI Sample:** `aldecI prov attest --artifact <path> --out artifacts/attestations/<id>.json --backend local --overlay demo`
**HTTP Sample:** `curl -sS -X POST http://127.0.0.1:8000/v1/provenance/attest -H 'Content-Type: application/json' -d @payload.json`

**Function call chain:**

CLI `aldecI prov attest --artifact <path> --out artifacts/attestations/<id>.json` -> Local backend `apps.runtime.local_handlers.handle_provenance_attest` -> SDK `sdk.python.fixops_client.FixopsClient.provenance_attest` -> FastAPI `apps.api.v1_prov.attest` -> Service `services.provenance.attestation.generate_attestation` -> Service `services.provenance.attestation.write_attestation` -> Infra `telemetry.configure`

## provenance.verify

**Availability:** ✅ Available

**What it does:** Validate attestations against artefact digests, builders, and metadata.

**Overlays:** demo, enterprise
**Outputs:** artifacts/attestations/verification.json
**CLI Sample:** `aldecI prov verify --artifact <path> --attestation <attestation.json> --backend local --overlay demo`
**HTTP Sample:** `curl -sS -X POST http://127.0.0.1:8000/v1/provenance/verify -H 'Content-Type: application/json' -d @payload.json`

**Function call chain:**

CLI `aldecI prov verify --artifact <path> --attestation <attestation.json>` -> Local backend `apps.runtime.local_handlers.handle_provenance_verify` -> SDK `sdk.python.fixops_client.FixopsClient.provenance_verify` -> FastAPI `apps.api.v1_prov.verify` -> Service `services.provenance.attestation.verify_attestation` -> Infra `telemetry.configure`

## risk.score

**Availability:** ✅ Available

**What it does:** Fuse EPSS, KEV, exposure, and version lag data into risk scores.

**Overlays:** demo, enterprise
**Outputs:** artifacts/risk.json
**CLI Sample:** `aldecI risk score --sbom artifacts/sbom/normalized.json --epss feeds/epss.csv --kev feeds/kev.json --out artifacts/risk.json --backend local --overlay demo`
**HTTP Sample:** `curl -sS -X POST http://127.0.0.1:8000/v1/risk/score -H 'Content-Type: application/json' -d @payload.json`

**Function call chain:**

CLI `aldecI risk score --sbom artifacts/sbom/normalized.json --epss feeds/epss.csv --kev feeds/kev.json --out artifacts/risk.json` -> Local backend `apps.runtime.local_handlers.handle_risk_score` -> SDK `sdk.python.fixops_client.FixopsClient.risk_score` -> FastAPI `apps.api.v1_risk.score` -> Service `services.risk.scoring.compute_risk_profile` -> Service `services.risk.scoring.write_risk_report` -> Infra `infra.feeds.epss.load_epss_scores` -> Infra `infra.feeds.kev.load_kev_catalog`

## stage.run

**Availability:** ✅ Available

**What it does:** Execute the upstream FixOps stage runner with overlay-aware storage.

**Overlays:** demo, enterprise
**Outputs:** artefacts/<app>/<run>/outputs/<stage>.json
**CLI Sample:** `aldecI stage run --stage <requirements|design|build|test|deploy|operate|decision> --backend local --overlay demo`
**HTTP Sample:** `curl -sS -X POST http://127.0.0.1:8000/v1/stage/run -H 'Content-Type: application/json' -d @payload.json`

**Function call chain:**

CLI `aldecI stage run --stage <requirements|design|build|test|deploy|operate|decision>` -> Local backend `apps.runtime.local_handlers.handle_stage_run` -> SDK `sdk.python.fixops_client.FixopsClient.stage_run` -> FastAPI `apps.api.v1_stage.run_stage` -> Service `core.stage_runner.StageRunner.run_stage` -> Service `services.run_registry.RunRegistry.ensure_run` -> Service `services.id_allocator.ensure_ids` -> Service `services.signing.sign_manifest` -> Service `services.signing.verify_manifest` -> Infra `config/settings.py`
