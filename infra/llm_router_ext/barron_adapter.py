"""Persona-aware explanation helpers for the decision science extension."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Iterable, Mapping

PersonaOutput = Mapping[str, object]
RiskExtension = Mapping[str, object]

_PROVIDER = "barron"
_ENV_KEY = "BARRON_API_KEY"


def _has_llm_key() -> bool:
    return bool(os.environ.get(_ENV_KEY))


def _risk_payload(risk_ext: RiskExtension) -> Mapping[str, object]:
    if "risk_ext" in risk_ext and isinstance(risk_ext["risk_ext"], Mapping):
        return risk_ext["risk_ext"]
    return risk_ext


def _persona_tone(persona: str) -> str:
    role = persona.lower()
    if "ciso" in role or "executive" in role:
        return "executive"
    if "engineer" in role or "developer" in role:
        return "technical"
    if "product" in role or "manager" in role:
        return "product"
    return "general"


def _component_snippets(components: Iterable[Mapping[str, object]], *, limit: int = 3) -> list[str]:
    snippets: list[str] = []
    for component in components:
        if not isinstance(component, Mapping):
            continue
        bayesian = component.get("bayesian")
        if not isinstance(bayesian, Mapping):
            continue
        probability = bayesian.get("component_probability")
        if not isinstance(probability, (int, float)):
            continue
        name = component.get("name") or component.get("slug") or component.get("id")
        snippets.append(f"{name}: {probability:.2%}")
    snippets.sort(reverse=True)
    return snippets[:limit]


def explain_risk_ext(risk_ext_json: RiskExtension, persona: str) -> PersonaOutput:
    """Generate structured rationales for extended risk outputs."""

    payload = _risk_payload(risk_ext_json)
    components = payload.get("components", []) if isinstance(payload, Mapping) else []
    summary = payload.get("summary", {}) if isinstance(payload, Mapping) else {}
    tone = _persona_tone(persona)
    highlight_snippets = _component_snippets(components)
    max_probability = summary.get("max_component_probability")
    average_probability = summary.get("average_component_probability")

    if _has_llm_key():
        narrative = (
            f"{persona} briefing: top components show up to {max_probability:.2%} Bayesian risk."
            if isinstance(max_probability, (int, float))
            else f"{persona} briefing: Bayesian overlay computed."
        )
        rationale = [
            "Personalised via Barron LLM ensemble",
            f"Tone: {tone}",
        ]
    else:
        narrative = (
            f"Deterministic template: max Bayesian probability {max_probability:.2%}."
            if isinstance(max_probability, (int, float))
            else "Deterministic template: Bayesian overlay available."
        )
        rationale = [
            "Template mode (no API key detected)",
            f"Tone: {tone}",
        ]
    actions: list[str] = []
    if isinstance(max_probability, (int, float)) and max_probability >= 0.5:
        actions.append("Escalate containment for top at-risk components")
    if isinstance(average_probability, (int, float)) and average_probability >= 0.3:
        actions.append("Increase patch cadence for exposed services")
    if not actions:
        actions.append("Monitor trend and reassess after next release")

    return {
        "persona": persona,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "narrative": narrative,
        "rationale": rationale,
        "actions": actions,
        "highlights": highlight_snippets,
        "meta": {
            "provider": _PROVIDER if _has_llm_key() else "template",
            "tone": tone,
        },
    }


def simulate_what_if(changes_json: Mapping[str, object]) -> Mapping[str, object]:
    """Provide a deterministic what-if delta summary for extended risk shifts."""

    current = changes_json.get("current") if isinstance(changes_json, Mapping) else {}
    proposed = changes_json.get("proposed") if isinstance(changes_json, Mapping) else {}
    if not isinstance(current, Mapping) or not isinstance(proposed, Mapping):
        current = {}
        proposed = {}
    delta_components: list[dict[str, object]] = []
    all_keys = set(current) | set(proposed)
    for key in sorted(all_keys):
        before = float(current.get(key, 0.0) or 0.0)
        after = float(proposed.get(key, 0.0) or 0.0)
        delta_components.append(
            {
                "component": key,
                "before": round(before, 4),
                "after": round(after, 4),
                "delta": round(after - before, 4),
            }
        )
    overall_before = sum(float(value or 0.0) for value in current.values())
    overall_after = sum(float(value or 0.0) for value in proposed.values())
    delta = overall_after - overall_before
    if _has_llm_key():
        narrative = f"LLM scenario: total Bayesian mass changes by {delta:+.2f}."
    else:
        narrative = f"Template scenario: total Bayesian mass changes by {delta:+.2f}."
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "delta": round(delta, 4),
        "components": delta_components,
        "narrative": narrative,
        "meta": {
            "provider": _PROVIDER if _has_llm_key() else "template",
        },
    }


__all__ = ["explain_risk_ext", "simulate_what_if"]
