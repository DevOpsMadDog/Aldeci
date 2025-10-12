"""SBOM domain orchestration leveraging imported FixOps services."""

from __future__ import annotations

from typing import Any

from services.normalize.normalizers import InputNormalizer, NormalizedSBOM
from services.sbom.normalizer import NormalizedComponent

__all__ = [
    "InputNormalizer",
    "NormalizedSBOM",
    "NormalizedComponent",
    "normalize_sbom",
]


def normalize_sbom(raw: Any, *, sbom_type: str = "auto") -> NormalizedSBOM:
    """Normalise *raw* SBOM payloads via the upstream FixOps normalizer."""

    normalizer = InputNormalizer(sbom_type=sbom_type)
    return normalizer.load_sbom(raw)
