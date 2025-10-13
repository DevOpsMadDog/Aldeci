"""Compatibility layer exposing upstream normalizers under the original import path."""
from services.normalize.normalizers import (  # noqa: F401
    InputNormalizer,
    NormalizedSARIF,
    NormalizedSBOM,
)

__all__ = ["InputNormalizer", "NormalizedSARIF", "NormalizedSBOM"]
