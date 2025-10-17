"""Markov-style propagation of component risk over dependency graphs."""
from __future__ import annotations

from datetime import datetime, timezone
from itertools import islice
from typing import Iterable, Mapping, MutableMapping, Sequence

import networkx as nx

ComponentScores = Mapping[str, Mapping[str, object]]
GraphPayload = Mapping[str, object]


def _component_lookup(risk_ext: Mapping[str, object]) -> ComponentScores:
    components: MutableMapping[str, Mapping[str, object]] = {}
    payload = risk_ext.get("risk_ext") if "risk_ext" in risk_ext else risk_ext
    if not isinstance(payload, Mapping):
        return components
    for component in payload.get("components", []):
        if not isinstance(component, Mapping):
            continue
        slug = component.get("slug")
        identifier = component.get("id")
        key = str(slug or identifier)
        if key:
            components[key] = component
            if slug and identifier:
                components[str(identifier)] = component
    return components


def _entry_nodes(components: ComponentScores) -> set[str]:
    entries: set[str] = set()
    for key, component in components.items():
        bayesian = component.get("bayesian") if isinstance(component, Mapping) else None
        exposure_flags = component.get("exposure_flags") if isinstance(component, Mapping) else None
        flags = set(str(flag).lower() for flag in exposure_flags or [])
        if "internet" in flags or "public" in flags:
            entries.add(str(component.get("slug") or key))
            continue
        if isinstance(bayesian, Mapping):
            probability = bayesian.get("component_probability")
            if isinstance(probability, (int, float)) and probability >= 0.4:
                entries.add(str(component.get("slug") or key))
    return entries


def _build_graph(payload: GraphPayload, components: ComponentScores) -> nx.DiGraph:
    graph = nx.DiGraph()
    nodes = payload.get("nodes", []) if isinstance(payload, Mapping) else []
    for node in nodes:
        if not isinstance(node, Mapping):
            continue
        node_id = node.get("id")
        if not node_id:
            continue
        key = str(node_id)
        if key in components:
            graph.add_node(key)
    edges = payload.get("edges", []) if isinstance(payload, Mapping) else []
    for edge in edges:
        if not isinstance(edge, Mapping):
            continue
        source = edge.get("source")
        target = edge.get("target")
        if not source or not target:
            continue
        source_key = str(source)
        target_key = str(target)
        if source_key in graph and target_key in graph:
            graph.add_edge(source_key, target_key)
    return graph


def _reachable_subgraph(graph: nx.DiGraph, entries: Iterable[str]) -> nx.DiGraph:
    if not entries:
        return graph.copy()
    reachable: set[str] = set()
    for entry in entries:
        if entry not in graph:
            continue
        reachable.add(entry)
        reachable.update(nx.descendants(graph, entry))
    if not reachable:
        return graph.copy()
    return graph.subgraph(reachable).copy()


def _personalization_vector(
    graph: nx.DiGraph, components: ComponentScores
) -> MutableMapping[str, float]:
    personalization: MutableMapping[str, float] = {}
    for node in graph.nodes:
        component = components.get(node)
        probability = 0.0
        if isinstance(component, Mapping):
            bayesian = component.get("bayesian")
            if isinstance(bayesian, Mapping):
                value = bayesian.get("component_probability")
                if isinstance(value, (int, float)):
                    probability = float(value)
        personalization[node] = probability
    total = sum(personalization.values())
    if total <= 0:
        count = len(personalization) or 1
        for node in personalization:
            personalization[node] = 1.0 / count
    else:
        for node in personalization:
            personalization[node] /= total
    return personalization


def _score_paths(
    graph: nx.DiGraph,
    entries: Sequence[str],
    scores: Mapping[str, float],
    *,
    limit: int,
) -> list[dict[str, object]]:
    highlights: list[dict[str, object]] = []
    top_targets = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    for target, score in islice(top_targets, limit):
        for entry in entries:
            if entry not in graph or target not in graph:
                continue
            if entry == target:
                highlights.append(
                    {
                        "source": entry,
                        "target": target,
                        "path": [entry],
                        "score": round(score, 4),
                    }
                )
                break
            try:
                path_iter = nx.shortest_simple_paths(graph, entry, target)
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                continue
            path = next(path_iter, None)
            if not path:
                continue
            highlights.append(
                {
                    "source": entry,
                    "target": target,
                    "path": path,
                    "score": round(score, 4),
                }
            )
            break
    return highlights


def _page_rank(
    graph: nx.DiGraph,
    personalization: Mapping[str, float],
    *,
    damping: float,
    max_iter: int = 50,
    tol: float = 1.0e-6,
) -> MutableMapping[str, float]:
    nodes = list(graph.nodes())
    if not nodes:
        return {}
    normalised = personalization.copy()
    total = sum(normalised.get(node, 0.0) for node in nodes)
    if total <= 0:
        weight = 1.0 / len(nodes)
        normalised = {node: weight for node in nodes}
    else:
        normalised = {node: normalised.get(node, 0.0) / total for node in nodes}
    rank = {node: 1.0 / len(nodes) for node in nodes}
    for _ in range(max_iter):
        new_rank = {node: (1.0 - damping) * normalised.get(node, 0.0) for node in nodes}
        dangling_sum = sum(rank[node] for node in nodes if graph.out_degree(node) == 0)
        for node in nodes:
            for predecessor in graph.predecessors(node):
                out_degree = graph.out_degree(predecessor)
                if out_degree:
                    new_rank[node] += damping * (rank[predecessor] / out_degree)
        if dangling_sum:
            for node in nodes:
                new_rank[node] += damping * dangling_sum * normalised.get(node, 0.0)
        diff = sum(abs(new_rank[node] - rank[node]) for node in nodes)
        rank = new_rank
        if diff < tol:
            break
    total_rank = sum(rank.values())
    if total_rank > 0:
        rank = {node: value / total_rank for node, value in rank.items()}
    return rank


def propagate_risk_markov(
    graph_payload: GraphPayload,
    risk_ext: Mapping[str, object],
    *,
    entry_nodes: Sequence[str] | None = None,
    top_k_paths: int = 5,
    damping: float = 0.85,
) -> Mapping[str, object]:
    """Propagate Bayesian component probabilities across the dependency graph."""

    components = _component_lookup(risk_ext)
    graph = _build_graph(graph_payload, components)
    if graph.number_of_nodes() == 0:
        return {
            "risk_markov": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "entry_nodes": [],
                "scores": [],
                "top_paths": [],
            }
        }
    entry_candidates = set(entry_nodes or [])
    if not entry_candidates:
        entry_candidates = _entry_nodes(components)
    reachable_graph = _reachable_subgraph(graph, entry_candidates)
    if reachable_graph.number_of_nodes() == 0:
        reachable_graph = graph
        entry_candidates = set(graph.nodes())
    personalization = _personalization_vector(reachable_graph, components)
    scores = _page_rank(reachable_graph, personalization, damping=damping)
    results = []
    for node, score in sorted(scores.items(), key=lambda item: item[1], reverse=True):
        component = components.get(node, {})
        bayesian = component.get("bayesian") if isinstance(component, Mapping) else {}
        results.append(
            {
                "node": node,
                "score": round(score, 4),
                "bayesian_probability": bayesian.get("component_probability"),
                "baseline_risk": component.get("baseline_risk"),
                "exposure_flags": component.get("exposure_flags", []),
            }
        )
    highlights = _score_paths(reachable_graph, list(entry_candidates), scores, limit=top_k_paths)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "entry_nodes": sorted(entry_candidates),
        "scores": results,
        "top_paths": highlights,
    }
    return {"risk_markov": payload}


__all__ = ["propagate_risk_markov"]
