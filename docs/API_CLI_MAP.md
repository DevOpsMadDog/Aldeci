# API to CLI Mapping

> These docs are generated from apps/registry/execution_map.py.
> Additional inputs: cli/aldecI.py and apps/api/app.py.

| Capability | Availability | CLI Command | CLI Options | API Route | Handler | Outputs |
| --- | --- | --- | --- | --- | --- | --- |
| evidence.bundle | ✅ Available | `Usage: evidence bundle [OPTIONS]` | --release<br>--normalized-sbom<br>--sbom-quality-json<br>--sbom-quality-html<br>--risk-report<br>--repro-attestation<br>--provenance-dir<br>--extra-dir<br>--policy<br>--sign-key<br>--out (default: artifacts/evidence/bundle.zip) | POST /v1/evidence/bundle | apps.api.v1_evidence.bundle | artifacts/evidence/<id>.zip<br>artifacts/evidence/<id>.yaml |
| gate.check | ❌ GAP: Policy gate evaluation not included in reuse artefacts. | `Usage: gate [OPTIONS]` | --policy | POST /v1/gate/check | apps.api.v1_gate.check | artifacts/gate/report.json |
| graph.anomalies | ✅ Available | `Usage: graph anomalies [OPTIONS]` | --commits<br>--commits-json<br>--attestations-dir<br>--attestations-json<br>--normalized-sbom<br>--risk-report<br>--releases | GET /v1/graph/anomalies | apps.api.v1_graph.anomalies | artifacts/graph/anomalies.json |
| graph.kev_in_last | ✅ Available | `Usage: graph kev-in-last [OPTIONS]` | --releases-window (default: 1)<br>--commits<br>--commits-json<br>--attestations-dir<br>--attestations-json<br>--normalized-sbom<br>--risk-report<br>--releases | GET /v1/graph/kev-in-last | apps.api.v1_graph.kev_in_last | artifacts/graph/kev_components.json |
| graph.lineage | ✅ Available | `Usage: graph lineage [OPTIONS]` | --artifact<br>--commits<br>--commits-json<br>--attestations-dir<br>--attestations-json<br>--normalized-sbom<br>--risk-report<br>--releases | GET /v1/graph/lineage | apps.api.v1_graph.lineage | artifacts/graph/lineage.json |
| ingest.sarif | ✅ Available | `Usage: ingest sarif [OPTIONS]` | --in<br>--out (default: artifacts/sarif/normalized.json) | POST /v1/ingest/sarif | apps.api.v1_ingest.ingest_sarif | artifacts/sarif/normalized.json |
| ingest.sbom | ✅ Available | `Usage: ingest sbom [OPTIONS]` | --in<br>--out (default: artifacts/sbom/normalized.json)<br>--sbom-type (default: auto) | POST /v1/ingest/sbom | apps.api.v1_ingest.ingest_sbom | artifacts/sbom/normalized.json |
| persona.explain | ❌ GAP: Persona explanation models are not part of the reuse snapshot. | `Usage: persona explain [OPTIONS]` | --role<br>--risk | POST /v1/persona/explain | apps.api.v1_persona.explain | artifacts/persona/<role>.md |
| provenance.attest | ✅ Available | `Usage: prov attest [OPTIONS]` | --artifact<br>--out (default: artifacts/attestations/attestation.json)<br>--builder (default: aldecI/builders/default)<br>--source (default: https://example.com/repo)<br>--build-type (default: https://fixops.dev/attestation/default) | POST /v1/provenance/attest | apps.api.v1_prov.attest | artifacts/attestations/<id>.json |
| provenance.verify | ✅ Available | `Usage: prov verify [OPTIONS]` | --artifact<br>--attestation<br>--builder<br>--source<br>--build-type | POST /v1/provenance/verify | apps.api.v1_prov.verify | artifacts/attestations/verification.json |
| risk.score | ✅ Available | `Usage: risk score [OPTIONS]` | --sbom<br>--epss<br>--kev<br>--out (default: artifacts/risk.json) | POST /v1/risk/score | apps.api.v1_risk.score | artifacts/risk.json |
| stage.run | ❌ GAP: Upstream stage runner not available in reuse bundle. | `Usage: stage run [OPTIONS]` | --stage | POST /v1/stage/run | apps.api.v1_stage.run_stage | artifacts/stage/<stage>.json |
