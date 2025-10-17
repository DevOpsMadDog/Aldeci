# Decision Science Extensions

The Phase 7 extension layers probabilistic reasoning on top of the existing
risk outputs without modifying the upstream scoring implementation. The add-on
lives under `services/score_ext/` and is completely optional – callers can opt
in via the new CLI/API surface or toggle the policy flag when evaluating gates.

## Bayesian fusion

`services/score_ext/bayes.py` implements a logistic model that fuses the
following inputs per vulnerability:

| Signal | Normalisation | Default Weight |
| --- | --- | --- |
| CVSS base score | `min(cvss, 10) / 10` | 2.75 |
| EPSS probability | as-is | 3.25 |
| KEV flag | 0 or 1 | 1.35 |
| Version lag | min(lag_days / 180, 1) | 1.10 |
| Exposure flags | min(unique_flags / 3, 1) | 0.90 |
| Bias | constant | -1.20 |

The probability is computed via a sigmoid:

```
p = sigmoid(w0 + w1 * cvss + w2 * epss + w3 * kev + w4 * lag + w5 * exposure)
```

Weights can be overridden in `config/weights.yml` under the `bayes_fuse` key.
The fusion is aggregated per component as `1 - Π (1 - p_i)` across its
vulnerabilities. Extended results are emitted as `risk_ext.json`.

## Markov propagation

`services/score_ext/markov.py` walks the dependency graph exported by
`services/graph` and computes a steady-state distribution using PageRank with
the Bayesian component probabilities as the personalization vector. Entry nodes
are inferred from exposure flags (e.g. `internet`) or can be supplied directly.
Outputs are stored in `risk_markov.json` with steady-state scores and the
highest-impact paths.

## Persona explanations and what-if analysis

`infra/llm_router_ext/barron_adapter.py` produces persona narratives based on
`risk_ext.json`. When the `BARRON_API_KEY` environment variable is present the
adapter records the provider as `barron`; otherwise it falls back to a
deterministic template. The module also exposes `simulate_what_if` for quick
Δ-risk simulations.

## Gate integration

`config/policy.yml` adds `use_extended_risk`. When the flag is `true` the gate
uses `risk_ext` metrics (max/average Bayesian probabilities) instead of the
baseline `max_risk_score`. Thresholds for the extended metrics can be set under
`risk_ext`.

## CLI & API surface

- `aldecI decision fuse` / `POST /v1/decision/fuse`
- `aldecI decision propagate` / `POST /v1/decision/propagate`
- `aldecI persona explain --risk-ext …` / `POST /v1/persona/explain_ext`

The baseline behaviour is unchanged; the extensions compose on demand.
