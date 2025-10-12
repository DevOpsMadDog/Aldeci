"""Lightweight stub of the :mod:`sarif_om` dependency used by reused services."""
from __future__ import annotations

from typing import Any, Iterable, List, Mapping, MutableMapping


class SarifLog:
    """Minimal implementation required by FixOps normalisers.

    The real dependency provides a richer object model. The reused normalisers
    only rely on attribute access, so this lightweight container is sufficient
    for reuse-only glue code and testing.
    """

    def __init__(
        self,
        *,
        runs: Iterable[Mapping[str, Any]] | None = None,
        version: str = "2.1.0",
        schema_uri: str | None = None,
        properties: Mapping[str, Any] | None = None,
    ) -> None:
        self.runs: List[Mapping[str, Any]] = list(runs or [])
        self.version = version
        self.schema_uri = schema_uri
        self.properties: MutableMapping[str, Any] = dict(properties or {})


__all__ = ["SarifLog"]
