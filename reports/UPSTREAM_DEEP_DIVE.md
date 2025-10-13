# Upstream Deep Dive

Generated from tools/importer/mine_docs.py and tools/importer/map_features.py.

| Feature | Mentions | Candidate Symbols | Candidate Files | Confidence |
| --- | --- | --- | --- | --- |
| cosign | 17 | — | — | 0.50 |
| epss | 25 | core/exploit_signals.py.load_latest_epss_feed<br>tests/test_feeds_enrichment.py.test_enrich_findings_populates_epss_and_kev<br>tests/test_processing_layer_fallbacks.py.test_markov_builder_fallback_uses_epss_and_kev_bias | — | 0.86 |
| evidence | 117 | core/cli.py._copy_evidence<br>core/cli.py._handle_get_evidence<br>core/evidence.py.EvidenceHub<br>core/evidence.py._atomic_write<br>core/feature_matrix.py._evidence_metrics<br>core/overlay_runtime.py._normalise_evidence_limits<br>tests/test_cli_commands.py.test_get_evidence_command_copies_bundle<br>tests/test_enterprise_paths.py.test_evidence_encrypted_when_overlay_requests_it<br>tests/test_evidence.py.test_evidence_hub_persists_manifest_and_checksum<br>tests/test_evidence_bundle.py._write_json | core/evidence.py<br>tests/test_evidence.py<br>tests/test_evidence_bundle.py<br>tests/test_evidence_export.py<br>tests/test_evidence_retrieval_fastpath.py | 1.00 |
| graph | 57 | apps/api/knowledge_graph.py.KnowledgeGraphService<br>scripts/deep_review.py.build_callgraph<br>scripts/deep_review.py.build_import_graph<br>scripts/deep_review.py.write_callgraph<br>scripts/deep_review.py.write_import_graph<br>scripts/generate_index.py.build_import_graph<br>scripts/graph_worker.py._optional_path<br>scripts/graph_worker.py.main<br>tests/test_enterprise_paths.py.test_pipeline_exposes_knowledge_graph<br>tests/test_graph_worker.py.test_graph_worker_main_single_cycle | apps/api/knowledge_graph.py<br>scripts/graph_worker.py<br>tests/test_graph_worker.py<br>tests/test_knowledge_graph.py | 1.00 |
| kev | 39 | core/exploit_signals.py.load_latest_kev_feed<br>tests/test_feeds_enrichment.py.test_enrich_findings_populates_epss_and_kev<br>tests/test_policy_kevs.py._BaseSettings<br>tests/test_policy_kevs.py._execute_with_session<br>tests/test_policy_kevs.py.run_with_session<br>tests/test_policy_kevs.py.test_kevs_allow_with_active_waiver<br>tests/test_policy_kevs.py.test_kevs_block_without_waiver<br>tests/test_processing_layer_fallbacks.py.test_markov_builder_fallback_uses_epss_and_kev_bias | tests/test_policy_kevs.py | 1.00 |
| provenance | 79 | — | — | 0.50 |
| sarif | 20 | apps/api/normalizers.py.NormalizedSARIF<br>apps/api/normalizers.py.SarifFinding<br>apps/api/normalizers.py._convert_snyk_payload_to_sarif<br>tests/test_new_backend_processing.py.test_sarif_analyzer_clusters_and_scores<br>tests/test_normalizers.py._build_sarif_document<br>tests/test_normalizers.py.test_load_sarif_converts_snyk_payload_without_converter<br>tests/test_normalizers.py.test_load_sarif_logs_actionable_error_without_converter<br>tests/test_normalizers.py.test_load_sarif_uses_embedded_payload_when_converter_missing | — | 1.00 |
| sbom | 92 | apps/api/normalizers.py.NormalizedSBOM<br>apps/api/normalizers.py.SBOMComponent<br>apps/api/normalizers.py._resolve_sbom_parser_state<br>tests/test_pipeline_matching.py.test_provider_specific_sbom_parser_enables_pipeline<br>tests/test_sbom_quality.py._sample_sboms<br>tests/test_sbom_quality.py._write_sbom<br>tests/test_sbom_quality.py.test_build_and_write_quality_outputs<br>tests/test_sbom_quality.py.test_normalize_sboms_merges_components<br>tests/test_sbom_quality.py.test_quality_report_metrics<br>tests/test_sbom_quality.py.test_render_html_report | tests/test_sbom_quality.py | 1.00 |
| slsa | 25 | — | — | 0.50 |
| ssvc | 2 | tests/test_business_context.py.test_load_business_context_ssvc_yaml<br>tests/test_design_context_injector.py.test_calculate_priors_matches_ssvc_outcomes | — | 0.44 |

## Missing in Upstream

- cosign
- provenance
- slsa
