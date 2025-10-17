"""Bayesian-style fusion helpers for extended risk scoring."""
from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Mapping

import yaml

DEFAULT_WEIGHTS: Mapping[str, float] = {
    "bias": -1.2,
    "cvss": 2.75,
    "epss": 3.25,
    "kev": 1.35,
    "version_lag": 1.1,
    "exposure": 0.9,
}

_CONFIG_PATH = Path("config") / "weights.yml"


def _sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-value))


@lru_cache(maxsize=1)
def _load_overrides() -> Mapping[str, float]:
    if not _CONFIG_PATH.is_file():
        return {}
    with _CONFIG_PATH.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    if not isinstance(payload, Mapping):
        return {}
    weights = payload.get("bayes_fuse")
    if not isinstance(weights, Mapping):
        return {}
    filtered: dict[str, float] = {}
    for key, value in weights.items():
        try:
            filtered[str(key)] = float(value)
        except (TypeError, ValueError):
            continue
    return filtered


def _resolve_weight(name: str) -> float:
    overrides = _load_overrides()
    if name in overrides:
        return float(overrides[name])
    return float(DEFAULT_WEIGHTS.get(name, 0.0))


def _normalise_cvss(cvss_base: float | None) -> float:
    if cvss_base is None:
        return 0.0
    try:
        value = float(cvss_base)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(value, 10.0)) / 10.0


def _normalise_version_lag(version_lag: float | None) -> float:
    if version_lag is None:
        return 0.0
    try:
        value = float(version_lag)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(value, 1.0))


def _normalise_exposure(exposure_flags: float | int | Iterable[str] | None) -> float:
    if exposure_flags is None:
        return 0.0
    if isinstance(exposure_flags, (int, float)):
        value = float(exposure_flags)
        if value <= 1.0:
            return max(0.0, value)
        return min(value / 3.0, 1.0)
    if isinstance(exposure_flags, str):
        exposure_flags = [exposure_flags]
    if isinstance(exposure_flags, Iterable):
        unique = {str(flag).lower() for flag in exposure_flags if str(flag).strip()}
        count = len(unique)
        if not count:
            return 0.0
        return min(count / 3.0, 1.0)
    return 0.0


def bayes_fuse(
    cvss_base: float | None,
    epss_prob: float | None,
    kev_flag: bool | int | None,
    version_lag: float | None,
    exposure_flags: float | int | Iterable[str] | None,
) -> float:
    """Compute a logistic-style probability from heterogeneous risk signals."""

    cvss_component = _resolve_weight("cvss") * _normalise_cvss(cvss_base)
    epss_value = 0.0 if epss_prob is None else max(0.0, min(float(epss_prob), 1.0))
    epss_component = _resolve_weight("epss") * epss_value
    kev_value = 1.0 if bool(kev_flag) else 0.0
    kev_component = _resolve_weight("kev") * kev_value
    lag_component = _resolve_weight("version_lag") * _normalise_version_lag(version_lag)
    exposure_component = _resolve_weight("exposure") * _normalise_exposure(exposure_flags)
    bias = _resolve_weight("bias")

    signal = bias + cvss_component + epss_component + kev_component + lag_component + exposure_component
    probability = _sigmoid(signal)
    return max(0.0, min(probability, 1.0))


__all__ = ["bayes_fuse", "DEFAULT_WEIGHTS"]
