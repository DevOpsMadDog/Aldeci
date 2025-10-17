from infra.llm_router_ext.barron_adapter import explain_risk_ext, simulate_what_if


RISK_EXT_PAYLOAD = {
    "risk_ext": {
        "components": [
            {
                "id": "pkg:A",
                "slug": "pkg-a",
                "name": "Component A",
                "exposure_flags": ["internet"],
                "bayesian": {"component_probability": 0.6},
            }
        ],
        "summary": {
            "component_count": 1,
            "max_component_probability": 0.6,
            "average_component_probability": 0.6,
        },
    }
}


def test_explain_ext_template_mode(monkeypatch) -> None:
    monkeypatch.delenv("BARRON_API_KEY", raising=False)
    result = explain_risk_ext(RISK_EXT_PAYLOAD, "CISO")
    assert result["meta"]["provider"] == "template"
    assert result["persona"] == "CISO"
    assert result["actions"]


def test_simulate_what_if_delta(monkeypatch) -> None:
    monkeypatch.setenv("BARRON_API_KEY", "test-key")
    result = simulate_what_if(
        {
            "current": {"pkg-a": 0.5},
            "proposed": {"pkg-a": 0.3},
        }
    )
    assert result["delta"] == -0.2
    assert result["components"][0]["delta"] == -0.2
    assert result["meta"]["provider"] == "barron"
    monkeypatch.delenv("BARRON_API_KEY", raising=False)
