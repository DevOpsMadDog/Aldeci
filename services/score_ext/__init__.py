"""Add-on scoring extensions layered on top of baseline risk outputs."""
from __future__ import annotations

from .fuse import compute_bayesian_extension
from .bayes import bayes_fuse
from .markov import propagate_risk_markov

__all__ = [
    "bayes_fuse",
    "compute_bayesian_extension",
    "propagate_risk_markov",
]
