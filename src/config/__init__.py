"""Compatibility shim for upstream FixOps imports."""
from config.settings import Settings, get_settings, resolve_allowed_origins

__all__ = ["Settings", "get_settings", "resolve_allowed_origins"]
