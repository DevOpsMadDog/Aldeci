from services.score_ext.markov import propagate_risk_markov


RISK_EXT_FIXTURE = {
    "risk_ext": {
        "components": [
            {
                "id": "pkg:A",
                "slug": "pkg-a",
                "name": "A",
                "baseline_risk": 80.0,
                "exposure_flags": ["internet"],
                "bayesian": {"component_probability": 0.6},
            },
            {
                "id": "pkg:B",
                "slug": "pkg-b",
                "name": "B",
                "baseline_risk": 50.0,
                "exposure_flags": ["internal"],
                "bayesian": {"component_probability": 0.3},
            },
            {
                "id": "pkg:C",
                "slug": "pkg-c",
                "name": "C",
                "baseline_risk": 20.0,
                "exposure_flags": ["internal"],
                "bayesian": {"component_probability": 0.1},
            },
        ],
        "summary": {
            "component_count": 3,
            "max_component_probability": 0.6,
            "average_component_probability": 0.3333,
        },
    }
}


GRAPH_FIXTURE = {
    "nodes": [
        {"id": "pkg:A"},
        {"id": "pkg:B"},
        {"id": "pkg:C"},
    ],
    "edges": [
        {"source": "pkg:A", "target": "pkg:B"},
        {"source": "pkg:B", "target": "pkg:C"},
    ],
}


def test_markov_propagation_orders_nodes() -> None:
    result = propagate_risk_markov(
        GRAPH_FIXTURE,
        RISK_EXT_FIXTURE,
        entry_nodes=["pkg:A"],
        top_k_paths=2,
    )
    scores = result["risk_markov"]["scores"]
    score_map = {entry["node"]: entry["score"] for entry in scores}
    assert set(score_map) == {"pkg:A", "pkg:B", "pkg:C"}
    assert score_map["pkg:B"] >= score_map["pkg:C"]
    assert score_map["pkg:B"] >= score_map["pkg:A"]
    paths = result["risk_markov"]["top_paths"]
    assert any(path["target"] == "pkg:B" for path in paths)


def test_markov_auto_entry_uses_exposure() -> None:
    result = propagate_risk_markov(
        GRAPH_FIXTURE,
        RISK_EXT_FIXTURE,
        entry_nodes=None,
        top_k_paths=1,
    )
    assert "pkg:A" in result["risk_markov"]["entry_nodes"]
