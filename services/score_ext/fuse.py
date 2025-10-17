"""Helpers to compose baseline risk reports with Bayesian fusion outputs."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Mapping, MutableMapping

from .bayes import bayes_fuse

Component = Mapping[str, object]
RiskReport = Mapping[str, object]
NormalizedSbom = Mapping[str, object]


@dataclass(slots=True)
class _BayesInputs:
    cvss: float | None
    epss: float | None
    kev: bool
    version_lag_norm: float
    exposure_flags: Iterable[str] | None


def _component_key(component: Mapping[str, object]) -> str:
    purl = component.get("purl")
    if isinstance(purl, str) and purl:
        return purl
    name = component.get("name") or "component"
    version = component.get("version") or "unspecified"
    return f"{name}@{version}"


def _index_normalized_components(sbom: NormalizedSbom) -> MutableMapping[str, Mapping[str, object]]:
    index: MutableMapping[str, Mapping[str, object]] = {}
    for component in sbom.get("components", []):
        if isinstance(component, Mapping):
            index[_component_key(component)] = component
    return index


def _index_normalized_vulns(component: Mapping[str, object]) -> MutableMapping[str, Mapping[str, object]]:
    mapping: MutableMapping[str, Mapping[str, object]] = {}
    for vuln in component.get("vulnerabilities", []) or []:
        if not isinstance(vuln, Mapping):
            continue
        cve = (
            vuln.get("cve")
            or vuln.get("cve_id")
            or vuln.get("id")
            or vuln.get("vuln_id")
            or vuln.get("vulnerability_id")
        )
        if isinstance(cve, str) and cve:
            mapping[cve.upper()] = vuln
    return mapping


def _extract_cvss(vulnerability: Mapping[str, object]) -> float | None:
    candidates = [
        vulnerability.get("cvss"),
        vulnerability.get("cvss_v3"),
        vulnerability.get("cvss_v30"),
        vulnerability.get("cvss_v31"),
        vulnerability.get("cvss_score"),
        vulnerability.get("cvss_base_score"),
    ]
    for candidate in candidates:
        if isinstance(candidate, (int, float)):
            return float(candidate)
        if isinstance(candidate, str):
            try:
                return float(candidate)
            except ValueError:
                continue
        if isinstance(candidate, Mapping):
            for key in ("baseScore", "base_score", "cvss_v3_base_score"):
                value = candidate.get(key)
                if isinstance(value, (int, float)):
                    return float(value)
                if isinstance(value, str):
                    try:
                        return float(value)
                    except ValueError:
                        continue
    return None


def _collect_inputs(
    component: Mapping[str, object],
    normalized: Mapping[str, object] | None,
    scored_vuln: Mapping[str, object],
) -> _BayesInputs:
    version_lag_days = 0.0
    lag_value = scored_vuln.get("version_lag_days")
    if isinstance(lag_value, (int, float)):
        version_lag_days = max(0.0, float(lag_value))
    version_lag_norm = min(version_lag_days / 180.0, 1.0)
    epss = scored_vuln.get("epss")
    epss_value = float(epss) if isinstance(epss, (int, float)) else None
    kev = bool(scored_vuln.get("kev"))
    exposure_flags = component.get("exposure_flags")
    if isinstance(exposure_flags, Iterable) and not isinstance(exposure_flags, (str, bytes)):
        flags = [str(flag) for flag in exposure_flags]
    else:
        flags = None

    cvss = None
    if normalized is not None:
        indexed_vulns = _index_normalized_vulns(normalized)
        cve = scored_vuln.get("cve")
        if isinstance(cve, str):
            source_vuln = indexed_vulns.get(cve.upper())
            if source_vuln:
                cvss = _extract_cvss(source_vuln)
    return _BayesInputs(cvss=cvss, epss=epss_value, kev=kev, version_lag_norm=version_lag_norm, exposure_flags=flags)


def _merge_component(
    component: Mapping[str, object],
    normalized: Mapping[str, object] | None,
) -> Mapping[str, object]:
    vulnerabilities = []
    combined_probability = 0.0
    exposure_flags = component.get("exposure_flags") if isinstance(component, Mapping) else None
    for scored in component.get("vulnerabilities", []):
        if not isinstance(scored, Mapping):
            continue
        inputs = _collect_inputs(component, normalized, scored)
        probability = bayes_fuse(
            inputs.cvss,
            inputs.epss,
            inputs.kev,
            inputs.version_lag_norm,
            inputs.exposure_flags,
        )
        vulnerabilities.append(
            {
                "cve": scored.get("cve"),
                "probability": round(probability, 4),
                "inputs": {
                    "cvss": inputs.cvss,
                    "epss": inputs.epss,
                    "kev": inputs.kev,
                    "version_lag_norm": round(inputs.version_lag_norm, 4),
                    "exposure_flags": list(inputs.exposure_flags) if inputs.exposure_flags else [],
                },
            }
        )
        combined_probability = 1 - (1 - combined_probability) * (1 - probability)
    return {
        "id": component.get("id"),
        "slug": component.get("slug"),
        "name": component.get("name"),
        "baseline_risk": component.get("component_risk"),
        "exposure_flags": exposure_flags or [],
        "bayesian": {
            "component_probability": round(combined_probability, 4),
            "vulnerabilities": vulnerabilities,
        },
    }


def compute_bayesian_extension(
    normalized_sbom: NormalizedSbom,
    risk_report: RiskReport,
) -> Mapping[str, object]:
    """Compose a Bayesian fusion overlay on top of a baseline risk report."""

    normalized_index = _index_normalized_components(normalized_sbom)
    components = []
    for component in risk_report.get("components", []):
        if not isinstance(component, Mapping):
            continue
        source_component = normalized_index.get(_component_key(component))
        components.append(_merge_component(component, source_component))

    component_probabilities = [
        entry["bayesian"].get("component_probability", 0.0)
        for entry in components
        if isinstance(entry, Mapping)
    ]
    max_probability = max(component_probabilities, default=0.0)
    avg_probability = (
        sum(component_probabilities) / len(component_probabilities)
        if component_probabilities
        else 0.0
    )

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "components": components,
        "summary": {
            "component_count": len(components),
            "max_component_probability": round(max_probability, 4),
            "average_component_probability": round(avg_probability, 4),
        },
    }
    return {"risk_ext": payload}


__all__ = ["compute_bayesian_extension"]
