"""SARIF domain orchestration built on imported FixOps services."""

from __future__ import annotations

from typing import Any

from services.normalize.normalizers import InputNormalizer, NormalizedSARIF, SarifFinding

__all__ = [
    "InputNormalizer",
    "NormalizedSARIF",
    "SarifFinding",
    "normalize_sarif",
]


def normalize_sarif(raw: Any) -> NormalizedSARIF:
    """Normalise *raw* SARIF payloads using the upstream FixOps normalizer."""

    normalizer = InputNormalizer()
    return normalizer.load_sarif(raw)
