"""End-to-end smoke tests across overlays and backends."""
from __future__ import annotations

import json
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Iterable

import pytest
import uvicorn

from apps.api.app import create_app


class UvicornThread:
    def __init__(self) -> None:
        self._server: uvicorn.Server | None = None
        self._thread: threading.Thread | None = None
        self.base_url: str | None = None

    def start(self) -> None:
        app = create_app()
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        host, port = sock.getsockname()
        sock.close()
        config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
        server = uvicorn.Server(config)
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        while not server.started:
            time.sleep(0.05)
        self._server = server
        self._thread = thread
        self.base_url = f"http://127.0.0.1:{port}"

    def stop(self) -> None:
        if self._server is not None:
            self._server.should_exit = True
        if self._thread is not None:
            self._thread.join(timeout=5)


@pytest.fixture
def sample_environment(tmp_path: Path) -> dict[str, Path]:
    artefacts_dir = tmp_path / "artifacts"
    artefacts_dir.mkdir()

    sbom_path = tmp_path / "sample_sbom.json"
    sbom_payload = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.4",
        "components": [
            {
                "name": "demo",
                "version": "1.0.0",
                "purl": "pkg:pypi/demo@1.0.0",
                "licenses": ["MIT"],
            }
        ],
    }
    sbom_path.write_text(json.dumps(sbom_payload), encoding="utf-8")

    sarif_path = tmp_path / "sample_sarif.json"
    sarif_payload = {
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [
            {
                "tool": {"driver": {"name": "DemoScanner"}},
                "results": [
                    {
                        "ruleId": "TST001",
                        "message": {"text": "Example finding"},
                        "level": "warning",
                    }
                ],
            }
        ],
    }
    sarif_path.write_text(json.dumps(sarif_payload), encoding="utf-8")

    normalized_sbom = tmp_path / "normalized_sbom.json"
    normalized_sbom.write_text(
        json.dumps(
            {
                "components": [
                    {
                        "name": "demo",
                        "slug": "demo",
                        "version": "1.0.0",
                        "vulnerabilities": [
                            {
                                "cve": "CVE-2023-0001",
                                "fix_version": "1.0.1",
                            }
                        ],
                        "exposure": "internet",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    epss_path = tmp_path / "epss.csv"
    epss_path.write_text("cve,epss\nCVE-2023-0001,0.9\n", encoding="utf-8")

    kev_path = tmp_path / "kev.json"
    kev_payload = {"vulnerabilities": [{"cveID": "CVE-2023-0001"}]}
    kev_path.write_text(json.dumps(kev_payload), encoding="utf-8")

    artifact_path = tmp_path / "artifact.bin"
    artifact_path.write_bytes(b"demo artifact contents")

    releases_path = tmp_path / "releases.json"
    releases_payload = {
        "releases": [
            {
                "tag": "v1.0.0",
                "date": "2024-01-01T00:00:00Z",
                "components": [{"slug": "demo", "version": "1.0.0"}],
            }
        ]
    }
    releases_path.write_text(json.dumps(releases_payload), encoding="utf-8")

    sbom_quality_json = tmp_path / "sbom_quality.json"
    sbom_quality_json.write_text(
        json.dumps(
            {
                "metrics": {
                    "coverage_percent": 100,
                    "license_coverage_percent": 100,
                }
            }
        ),
        encoding="utf-8",
    )
    sbom_quality_html = tmp_path / "sbom_quality.html"
    sbom_quality_html.write_text("<html><body>SBOM quality</body></html>", encoding="utf-8")

    repro_attestation = tmp_path / "repro_attestation.json"
    repro_attestation.write_text(json.dumps({"match": True}), encoding="utf-8")

    policy_path = tmp_path / "policy.json"
    policy_path.write_text(json.dumps({"rules": []}), encoding="utf-8")

    commits_json = tmp_path / "commits.json"
    commits_json.write_text(json.dumps([{"sha": "abc123", "message": "initial"}]), encoding="utf-8")

    return {
        "sbom": sbom_path,
        "sarif": sarif_path,
        "normalized_sbom": normalized_sbom,
        "epss": epss_path,
        "kev": kev_path,
        "artifact": artifact_path,
        "releases": releases_path,
        "sbom_quality_json": sbom_quality_json,
        "sbom_quality_html": sbom_quality_html,
        "repro_attestation": repro_attestation,
        "policy": policy_path,
        "commits": commits_json,
        "artifacts_dir": artefacts_dir,
    }


def _run_cli(
    args: Iterable[str],
    *,
    backend: str,
    overlay: str,
    base_url: str | None,
    cwd: Path,
) -> subprocess.CompletedProcess:
    command = [
        sys.executable,
        "-m",
        "cli.aldecI",
        "--backend",
        backend,
        "--overlay",
        overlay,
    ]
    if backend == "http" and base_url:
        command.extend(["--api-base-url", base_url])
    command.extend(args)
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True)


@pytest.mark.parametrize("overlay", ["demo", "enterprise"])
@pytest.mark.parametrize("backend", ["local", "http"])
def test_overlay_smoke(sample_environment: dict[str, Path], overlay: str, backend: str) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    server = UvicornThread() if backend == "http" else None
    base_url = None
    try:
        if server is not None:
            server.start()
            base_url = server.base_url
        # ingest sbom
        sbom_out = sample_environment["artifacts_dir"] / "sbom" / "normalized.json"
        result = _run_cli(
            [
                "ingest",
                "sbom",
                "--in",
                str(sample_environment["sbom"]),
                "--out",
                str(sbom_out),
            ],
            backend=backend,
            overlay=overlay,
            base_url=base_url,
            cwd=repo_root,
        )
        assert result.returncode == 0, result.stderr
        assert sbom_out.is_file()

        # ingest sarif
        sarif_out = sample_environment["artifacts_dir"] / "sarif" / "normalized.json"
        result = _run_cli(
            [
                "ingest",
                "sarif",
                "--in",
                str(sample_environment["sarif"]),
                "--out",
                str(sarif_out),
            ],
            backend=backend,
            overlay=overlay,
            base_url=base_url,
            cwd=repo_root,
        )
        assert result.returncode == 0, result.stderr
        assert sarif_out.is_file()

        # risk score
        risk_out = sample_environment["artifacts_dir"] / "risk.json"
        result = _run_cli(
            [
                "risk",
                "score",
                "--sbom",
                str(sample_environment["normalized_sbom"]),
                "--epss",
                str(sample_environment["epss"]),
                "--kev",
                str(sample_environment["kev"]),
                "--out",
                str(risk_out),
            ],
            backend=backend,
            overlay=overlay,
            base_url=base_url,
            cwd=repo_root,
        )
        assert result.returncode == 0, result.stderr
        assert risk_out.is_file()

        # provenance attest
        attestation_dir = sample_environment["artifacts_dir"] / "attestations"
        attestation_dir.mkdir(exist_ok=True)
        attestation_path = attestation_dir / "artifact.json"
        result = _run_cli(
            [
                "prov",
                "attest",
                "--artifact",
                str(sample_environment["artifact"]),
                "--out",
                str(attestation_path),
            ],
            backend=backend,
            overlay=overlay,
            base_url=base_url,
            cwd=repo_root,
        )
        assert result.returncode == 0, result.stderr
        assert attestation_path.is_file()

        # provenance verify
        result = _run_cli(
            [
                "prov",
                "verify",
                "--artifact",
                str(sample_environment["artifact"]),
                "--attestation",
                str(attestation_path),
            ],
            backend=backend,
            overlay=overlay,
            base_url=base_url,
            cwd=repo_root,
        )
        assert result.returncode == 0, result.stderr

        # graph lineage
        result = _run_cli(
            [
                "graph",
                "lineage",
                "--artifact",
                "artifact.bin",
                "--commits-json",
                str(sample_environment["commits"]),
                "--attestations-dir",
                str(attestation_dir),
                "--normalized-sbom",
                str(sample_environment["normalized_sbom"]),
                "--risk-report",
                str(risk_out),
                "--releases",
                str(sample_environment["releases"]),
            ],
            backend=backend,
            overlay=overlay,
            base_url=base_url,
            cwd=repo_root,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip(), "graph lineage should emit JSON"

        # graph kev-in-last
        result = _run_cli(
            [
                "graph",
                "kev-in-last",
                "--releases-window",
                "1",
                "--commits-json",
                str(sample_environment["commits"]),
                "--attestations-dir",
                str(attestation_dir),
                "--normalized-sbom",
                str(sample_environment["normalized_sbom"]),
                "--risk-report",
                str(risk_out),
                "--releases",
                str(sample_environment["releases"]),
            ],
            backend=backend,
            overlay=overlay,
            base_url=base_url,
            cwd=repo_root,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip(), "graph kev-in-last should emit JSON"

        # graph anomalies
        result = _run_cli(
            [
                "graph",
                "anomalies",
                "--commits-json",
                str(sample_environment["commits"]),
                "--attestations-dir",
                str(attestation_dir),
                "--normalized-sbom",
                str(sample_environment["normalized_sbom"]),
                "--risk-report",
                str(risk_out),
                "--releases",
                str(sample_environment["releases"]),
            ],
            backend=backend,
            overlay=overlay,
            base_url=base_url,
            cwd=repo_root,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip(), "graph anomalies should emit JSON"

        # evidence bundle
        bundle_path = sample_environment["artifacts_dir"] / "evidence" / "bundle.zip"
        bundle_path.parent.mkdir(parents=True, exist_ok=True)
        result = _run_cli(
            [
                "evidence",
                "bundle",
                "--release",
                "v1.0.0",
                "--normalized-sbom",
                str(sample_environment["normalized_sbom"]),
                "--sbom-quality-json",
                str(sample_environment["sbom_quality_json"]),
                "--sbom-quality-html",
                str(sample_environment["sbom_quality_html"]),
                "--risk-report",
                str(risk_out),
                "--repro-attestation",
                str(sample_environment["repro_attestation"]),
                "--provenance-dir",
                str(attestation_dir),
                "--out",
                str(bundle_path),
            ],
            backend=backend,
            overlay=overlay,
            base_url=base_url,
            cwd=repo_root,
        )
        assert result.returncode == 0, result.stderr
        assert bundle_path.is_file()
        manifest_path = bundle_path.with_suffix(".manifest.json")
        assert manifest_path.is_file()

        # stage run
        result = _run_cli(
            [
                "stage",
                "run",
                "--stage",
                "requirements",
            ],
            backend=backend,
            overlay=overlay,
            base_url=base_url,
            cwd=repo_root,
        )
        assert result.returncode == 0, result.stderr
        lines = [line for line in result.stdout.splitlines() if line.strip()]
        assert lines, "stage run should emit output"
        summary = json.loads(lines[-1])
        assert summary["stage"] == "requirements"
        stage_output = Path(summary["output_file"]) if "output_file" in summary else None
        if stage_output:
            assert stage_output.exists()

        # gate
        result = _run_cli(
            [
                "gate",
                "--policy",
                str(sample_environment["policy"]),
                "--risk-report",
                str(risk_out),
                "--provenance-dir",
                str(attestation_dir),
                "--repro-attestation",
                str(sample_environment["repro_attestation"]),
            ],
            backend=backend,
            overlay=overlay,
            base_url=base_url,
            cwd=repo_root,
        )
        assert result.returncode == 0, result.stderr
        assert "Gate evaluation" in result.stdout

        # persona explain
        result = _run_cli(
            [
                "persona",
                "explain",
                "--role",
                "ciso",
                "--risk",
                str(risk_out),
            ],
            backend=backend,
            overlay=overlay,
            base_url=base_url,
            cwd=repo_root,
        )
        assert result.returncode == 0, result.stderr
        assert "[ciso]" in result.stdout
    finally:
        if server is not None:
            server.stop()
