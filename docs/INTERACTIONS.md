# System Interactions

> These docs are generated from apps/registry/execution_map.py.

## epss

**What it does:** Download and cache the latest EPSS probability scores.

**Flow:** CLI `aldecI feeds epss --out data/feeds/epss.csv` → API `POST /v1/feeds/epss` → Infra `infra.feeds.epss.update_epss_feed` → Infra `infra.feeds.epss.load_epss_scores` → Outputs data/feeds/epss.csv

**Sample CLI**

```bash
aldecI feeds epss --out data/feeds/epss.csv
```

**Sample cURL**

```bash
curl -X POST https://api.example.com/v1/feeds/epss \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{"payload": "..."}'
```

## evidence.bundle

**What it does:** Assemble signed evidence bundles with policy evaluation results.

**Flow:** CLI `aldecI evidence bundle --config <bundle.yml> --out-dir evidence/` → API `POST /v1/evidence/bundle` → Service `services.evidence.packager.load_policy` → Service `services.evidence.packager.evaluate_policy` → Service `services.evidence.packager.create_bundle` → Infra `infra.signing.sign-artifact.sh` → Outputs evidence/bundles/<tag>.zip, evidence/bundles/MANIFEST.yaml

**Sample CLI**

```bash
aldecI evidence bundle --config <bundle.yml> --out-dir evidence/
```

**Sample cURL**

```bash
curl -X POST https://api.example.com/v1/evidence/bundle \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{"payload": "..."}'
```

## graph.anomalies (alias of graph.lineage)

**What it does:** Detect release timeline anomalies across the provenance graph.

**Flow:** CLI `aldecI graph anomalies --repo <path>` → API `POST /v1/graph/anomalies` → Service `services.graph.graph.build_graph_from_sources` → Service `services.graph.graph.ProvenanceGraph.detect_version_anomalies` → Infra `telemetry.configure` → Outputs graph/anomalies.json

**Sample CLI**

```bash
aldecI graph anomalies --repo <path>
```

**Sample cURL**

```bash
curl -X POST https://api.example.com/v1/graph/anomalies \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{"payload": "..."}'
```

## graph.kev_in_last (alias of graph.lineage)

**What it does:** Identify components linked to KEV CVEs in the most recent releases.

**Flow:** CLI `aldecI graph kev-in-last --repo <path> --releases <n>` → API `POST /v1/graph/kev-in-last` → Service `services.graph.graph.build_graph_from_sources` → Service `services.graph.graph.ProvenanceGraph.components_with_kev` → Infra `telemetry.configure` → Outputs graph/kev_components.json

**Sample CLI**

```bash
aldecI graph kev-in-last --repo <path> --releases <n>
```

**Sample cURL**

```bash
curl -X POST https://api.example.com/v1/graph/kev-in-last \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{"payload": "..."}'
```

## graph.lineage

**What it does:** Construct provenance graphs and return artefact lineage traversals.

**Flow:** CLI `aldecI graph lineage --repo <path> --artifact <name>` → API `POST /v1/graph/lineage` → Service `services.graph.graph.build_graph_from_sources` → Service `services.graph.graph.ProvenanceGraph.lineage` → Infra `telemetry.configure` → Outputs graph/lineage.json

**Sample CLI**

```bash
aldecI graph lineage --repo <path> --artifact <name>
```

**Sample cURL**

```bash
curl -X POST https://api.example.com/v1/graph/lineage \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{"payload": "..."}'
```

## kev

**What it does:** Fetch and normalise the CISA Known Exploited Vulnerabilities catalogue.

**Flow:** CLI `aldecI feeds kev --out data/feeds/kev.json` → API `POST /v1/feeds/kev` → Infra `infra.feeds.kev.update_kev_feed` → Infra `infra.feeds.kev.load_kev_catalog` → Outputs data/feeds/kev.json

**Sample CLI**

```bash
aldecI feeds kev --out data/feeds/kev.json
```

**Sample cURL**

```bash
curl -X POST https://api.example.com/v1/feeds/kev \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{"payload": "..."}'
```

## provenance.attest

**What it does:** Create SLSA v1 DSSE attestations for build artefacts.

**Flow:** CLI `aldecI provenance attest --artifact <path> --builder <id> --source <uri> --out <attestation.json>` → API `POST /v1/provenance/attest` → Service `domain.provenance.generate_attestation` → Service `services.provenance.attestation.generate_attestation` → Service `services.provenance.attestation.write_attestation` → Infra `telemetry.configure` → Outputs attestations/<artifact>.json

**Sample CLI**

```bash
aldecI provenance attest --artifact <path> --builder <id> --source <uri> --out <attestation.json>
```

**Sample cURL**

```bash
curl -X POST https://api.example.com/v1/provenance/attest \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{"payload": "..."}'
```

## provenance.verify (alias of provenance.attest)

**What it does:** Validate attestations against artefact digests, builders, and metadata.

**Flow:** CLI `aldecI provenance verify --artifact <path> --attestation <attestation.json>` → API `POST /v1/provenance/verify` → Service `domain.provenance.verify_attestation` → Service `services.provenance.attestation.verify_attestation` → Infra `telemetry.configure` → Outputs verification_report.json

**Sample CLI**

```bash
aldecI provenance verify --artifact <path> --attestation <attestation.json>
```

**Sample cURL**

```bash
curl -X POST https://api.example.com/v1/provenance/verify \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{"payload": "..."}'
```

## risk.score

**What it does:** Fuse EPSS, KEV, exposure, and version lag data into risk scores.

**Flow:** CLI `aldecI risk score --sbom <normalized.json> --epss <epss.csv> --kev <kev.json>` → API `POST /v1/risk/score` → Service `services.risk.scoring.compute_risk_profile` → Service `services.risk.scoring.write_risk_report` → Infra `infra.feeds.epss.load_epss_scores` → Infra `infra.feeds.kev.load_kev_catalog` → Outputs risk_report.json, risk_report.html

**Sample CLI**

```bash
aldecI risk score --sbom <normalized.json> --epss <epss.csv> --kev <kev.json>
```

**Sample cURL**

```bash
curl -X POST https://api.example.com/v1/risk/score \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{"payload": "..."}'
```

## sarif.normalize

**What it does:** Parse SARIF logs, harmonise severities, and summarise findings.

**Flow:** CLI `aldecI sarif normalize --input <sarif.json>` → API `POST /v1/sarif/normalize` → Service `domain.sarif.normalize_sarif` → Service `services.normalize.normalizers.InputNormalizer.load_sarif` → Outputs normalized_sarif.json

**Sample CLI**

```bash
aldecI sarif normalize --input <sarif.json>
```

**Sample cURL**

```bash
curl -X POST https://api.example.com/v1/sarif/normalize \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{"payload": "..."}'
```

## sbom.normalize

**What it does:** Normalise CycloneDX/SPDX SBOM payloads to a canonical structure.

**Flow:** CLI `aldecI sbom normalize --input <sbom.json> [--sbom-type auto]` → API `POST /v1/sbom/normalize` → Service `domain.sbom.normalize_sbom` → Service `services.normalize.normalizers.InputNormalizer.load_sbom` → Outputs normalized_sbom.json

**Sample CLI**

```bash
aldecI sbom normalize --input <sbom.json> [--sbom-type auto]
```

**Sample cURL**

```bash
curl -X POST https://api.example.com/v1/sbom/normalize \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{"payload": "..."}'
```
