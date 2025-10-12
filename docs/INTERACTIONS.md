# System Interactions

> These docs are generated from apps/registry/execution_map.py.
> Additional inputs: cli/aldecI.py and apps/api/app.py.

## evidence.bundle

**What it does:** Assemble signed evidence bundles with policy evaluation results.

**Function call chain:**

CLI `aldecI evidence bundle` -> Local backend `apps.runtime.local_handlers.handle_evidence_bundle` -> HTTP client `sdk.python.fixops_client.FixopsClient.evidence_bundle` -> API `apps.api.v1_evidence.bundle` -> Service `services.evidence.packager.load_policy` -> Service `services.evidence.packager.evaluate_policy` -> Service `services.evidence.packager.create_bundle` -> Infra `infra.signing.sign-artifact.sh`

## gate.check

**What it does:** Evaluate policy gates against collected evidence.

> GAP: Policy gate evaluation not included in reuse artefacts.

## graph.anomalies

**What it does:** Detect release timeline anomalies across the provenance graph.

**Function call chain:**

CLI `aldecI graph anomalies` -> Local backend `apps.runtime.local_handlers.handle_graph_anomalies` -> HTTP client `sdk.python.fixops_client.FixopsClient.graph_anomalies` -> API `apps.api.v1_graph.anomalies` -> Service `services.graph.graph.ProvenanceGraph.detect_version_anomalies` -> Service `services.graph.graph.build_graph_from_sources` -> Infra `telemetry.configure`

## graph.kev_in_last

**What it does:** Identify components linked to KEV CVEs in the most recent releases.

**Function call chain:**

CLI `aldecI graph kev-in-last` -> Local backend `apps.runtime.local_handlers.handle_graph_kev` -> HTTP client `sdk.python.fixops_client.FixopsClient.graph_kev` -> API `apps.api.v1_graph.kev_in_last` -> Service `services.graph.graph.ProvenanceGraph.components_with_kev` -> Service `services.graph.graph.build_graph_from_sources` -> Infra `telemetry.configure`

## graph.lineage

**What it does:** Construct provenance graphs and return artefact lineage traversals.

**Function call chain:**

CLI `aldecI graph lineage` -> Local backend `apps.runtime.local_handlers.handle_graph_lineage` -> HTTP client `sdk.python.fixops_client.FixopsClient.graph_lineage` -> API `apps.api.v1_graph.lineage` -> Service `services.graph.graph.ProvenanceGraph.lineage` -> Service `services.graph.graph.build_graph_from_sources` -> Infra `telemetry.configure`

## ingest.sarif

**What it does:** Parse SARIF logs, harmonise severities, and summarise findings.

**Function call chain:**

CLI `aldecI ingest sarif` -> Local backend `apps.runtime.local_handlers.handle_ingest_sarif` -> HTTP client `sdk.python.fixops_client.FixopsClient.ingest_sarif` -> API `apps.api.v1_ingest.ingest_sarif` -> Service `services.normalize.normalizers.InputNormalizer.load_sarif`

## ingest.sbom

**What it does:** Normalise CycloneDX/SPDX SBOM payloads to a canonical structure.

**Function call chain:**

CLI `aldecI ingest sbom` -> Local backend `apps.runtime.local_handlers.handle_ingest_sbom` -> HTTP client `sdk.python.fixops_client.FixopsClient.ingest_sbom` -> API `apps.api.v1_ingest.ingest_sbom` -> Service `services.normalize.normalizers.InputNormalizer.load_sbom`

## persona.explain

**What it does:** Generate risk narratives tailored for specific personas.

> GAP: Persona explanation models are not part of the reuse snapshot.

## provenance.attest

**What it does:** Create SLSA v1 DSSE attestations for build artefacts.

**Function call chain:**

CLI `aldecI prov attest` -> Local backend `apps.runtime.local_handlers.handle_provenance_attest` -> HTTP client `sdk.python.fixops_client.FixopsClient.provenance_attest` -> API `apps.api.v1_prov.attest` -> Service `services.provenance.attestation.generate_attestation` -> Service `services.provenance.attestation.write_attestation` -> Infra `telemetry.configure`

## provenance.verify

**What it does:** Validate attestations against artefact digests, builders, and metadata.

**Function call chain:**

CLI `aldecI prov verify` -> Local backend `apps.runtime.local_handlers.handle_provenance_verify` -> HTTP client `sdk.python.fixops_client.FixopsClient.provenance_verify` -> API `apps.api.v1_prov.verify` -> Service `services.provenance.attestation.verify_attestation` -> Infra `telemetry.configure`

## risk.score

**What it does:** Fuse EPSS, KEV, exposure, and version lag data into risk scores.

**Function call chain:**

CLI `aldecI risk score` -> Local backend `apps.runtime.local_handlers.handle_risk_score` -> HTTP client `sdk.python.fixops_client.FixopsClient.risk_score` -> API `apps.api.v1_risk.score` -> Service `services.risk.scoring.compute_risk_profile` -> Service `services.risk.scoring.write_risk_report` -> Infra `infra.feeds.epss.load_epss_scores` -> Infra `infra.feeds.kev.load_kev_catalog`

## stage.run

**What it does:** Execute a FixOps SDLC stage runbook.

> GAP: Upstream stage runner not available in reuse bundle.
