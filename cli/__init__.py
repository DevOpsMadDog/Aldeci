"""Typer-based command line interface package for Aldeci."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - import only for type checking
    from .aldecI import app as _app

__all__ = ["app"]


def __getattr__(name: str) -> Any:
    """Lazily expose the Typer application to avoid eager imports during ``python -m``."""

    if name == "app":
        from .aldecI import app as typer_app

        return typer_app
    raise AttributeError(f"module 'cli' has no attribute {name!r}")
