# API to CLI Mapping

> These docs are generated from apps/registry/execution_map.py.

| Capability | CLI Syntax | API Route | Services | Overlays | Outputs |
| --- | --- | --- | --- | --- | --- |
| epss | aldecI feeds epss --out data/feeds/epss.csv | POST /v1/feeds/epss | — | demo<br>enterprise | data/feeds/epss.csv |
| evidence.bundle | aldecI evidence bundle --config <bundle.yml> --out-dir evidence/ | POST /v1/evidence/bundle | services.evidence.packager.load_policy<br>services.evidence.packager.evaluate_policy<br>services.evidence.packager.create_bundle | demo<br>enterprise | evidence/bundles/<tag>.zip<br>evidence/bundles/MANIFEST.yaml |
| graph.anomalies (alias of graph.lineage) | aldecI graph anomalies --repo <path> | POST /v1/graph/anomalies | services.graph.graph.build_graph_from_sources<br>services.graph.graph.ProvenanceGraph.detect_version_anomalies | demo<br>enterprise | graph/anomalies.json |
| graph.kev_in_last (alias of graph.lineage) | aldecI graph kev-in-last --repo <path> --releases <n> | POST /v1/graph/kev-in-last | services.graph.graph.build_graph_from_sources<br>services.graph.graph.ProvenanceGraph.components_with_kev | demo<br>enterprise | graph/kev_components.json |
| graph.lineage | aldecI graph lineage --repo <path> --artifact <name> | POST /v1/graph/lineage | services.graph.graph.build_graph_from_sources<br>services.graph.graph.ProvenanceGraph.lineage | demo<br>enterprise | graph/lineage.json |
| kev | aldecI feeds kev --out data/feeds/kev.json | POST /v1/feeds/kev | — | demo<br>enterprise | data/feeds/kev.json |
| provenance.attest | aldecI provenance attest --artifact <path> --builder <id> --source <uri> --out <attestation.json> | POST /v1/provenance/attest | services.provenance.attestation.generate_attestation<br>services.provenance.attestation.write_attestation | demo<br>enterprise | attestations/<artifact>.json |
| provenance.verify (alias of provenance.attest) | aldecI provenance verify --artifact <path> --attestation <attestation.json> | POST /v1/provenance/verify | services.provenance.attestation.verify_attestation | demo<br>enterprise | verification_report.json |
| risk.score | aldecI risk score --sbom <normalized.json> --epss <epss.csv> --kev <kev.json> | POST /v1/risk/score | services.risk.scoring.compute_risk_profile<br>services.risk.scoring.write_risk_report | demo<br>enterprise | risk_report.json<br>risk_report.html |
| sarif.normalize | aldecI sarif normalize --input <sarif.json> | POST /v1/sarif/normalize | services.normalize.normalizers.InputNormalizer.load_sarif | demo<br>enterprise | normalized_sarif.json |
| sbom.normalize | aldecI sbom normalize --input <sbom.json> [--sbom-type auto] | POST /v1/sbom/normalize | services.normalize.normalizers.InputNormalizer.load_sbom | demo<br>enterprise | normalized_sbom.json |
