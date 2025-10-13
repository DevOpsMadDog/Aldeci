from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.normalize.normalizers import InputNormalizer


def test_parse_cyclonedx_json_handles_missing_components():
    normalizer = InputNormalizer()

    document = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "metadata": {"timestamp": "2024-01-01T00:00:00Z"},
        "dependencies": [],
        "vulnerabilities": [{"id": "CVE-2023-123"}],
    }

    result = normalizer._parse_cyclonedx_json(document)

    assert result is not None
    assert result.format == "cyclonedx"
    assert result.components == []
    assert result.metadata["component_count"] == 0
    assert result.metadata["spec_version"] == "1.5"
    assert result.vulnerabilities == document["vulnerabilities"]
    assert result.relationships == []
    assert result.services == []
