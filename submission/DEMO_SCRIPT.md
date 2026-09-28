# Live Demo Script — 10 to 15 Minutes

## 0:00–1:00 — Problem and promise

“A bank needs to distinguish a normal payment from coordinated mule activity quickly enough to stop loss, while giving investigators explainable evidence and preserving an audit trail. This build connects three tracks: model scoring, BI investigation, and automated product action.”

Show the live control hub: `https://fraud-platform-team8-fraud.apps.itz-i8rikv.infra01-lb.tok04.techzone.ibm.com/`.

## 1:00–2:30 — Sector and audience

State the sector as fintech/banking fraud prevention. The primary audience is an internal fraud-operations team. The two demonstrated features are:

- risk and case investigation for a flagged transaction;
- automated protection with an investigator override and compliance audit evidence.

Point out the three pipeline cards on the hub and the single-port design.

## 2:30–4:00 — Architecture

Open `/docs` and explain the flow:

1. `POST /predict` engineers velocity, geo-distance, rolling frequency, spend ratio, IP overlap, and device overlap, then returns a fraud probability.
2. `POST /investigate` searches KYC/SAR case files and tags distress or mule-ring signals.
3. `POST /curtail` applies the policy matrix, dispatches simulated mitigations, and writes an audit event.

The same flow is available through separate local services on ports 8000/8001/8002, while the deployed demo exposes one reviewer-friendly URL.

## 4:00–6:00 — Normal transaction

Use the first payload in `demo_payloads.json` with `POST /curtail` in Swagger. Narrate the expected result:

- low risk;
- `AUTO_APPROVE`;
- simulated settlement dispatch;
- audit event recorded.

Use `/stats` or `/audit-logs` to show that the event is persisted.

## 6:00–9:00 — Suspicious transaction and BI enrichment

Use the `TXN-MULE-01` payload in `demo_payloads.json`. Explain that the customer/device identifiers match the sample case material. The model is stateful, so narrate the probability and action actually returned rather than promising a fixed label. If it is flagged, show the enriched case path; if it is not, explain that the low-risk branch correctly avoids unnecessary investigation. Show the response fields:

- `fraud_probability` and `flagged`;
- `matched_cases`;
- `mule_ring_signals` and `distress_signals`;
- the resulting product action and dispatched channels.

Use `/dashboard` to show the alert feed and KPI counters.

## 9:00–11:00 — Human-in-the-loop control

Use `POST /override` for the transaction ID returned by either scenario. Explain that a cleared case can be manually changed by an investigator, with notes. Refresh `/audit-logs` and show the `OVERRIDDEN` event. This demonstrates the human-in-the-loop control even when the model chooses `AUTO_APPROVE`.

## 11:00–12:30 — Watson Orchestrate handoff

Open `/orchestrate-skill.json`. Explain that the OpenAPI 3 contract exposes the curtailment action as a catalog-ready skill. The skill lets an orchestrated digital employee call the same policy endpoint and receive structured action/audit results.

## 12:30–14:00 — Operations and close

Open `/healthz` and `/docs`. Mention the OpenShift deployment configuration, readiness/liveness probes, route, and `/tmp/audit.db` runtime location. Close with the next step: connect the OpenAPI skill to Watson Orchestrate and replace simulated dispatchers with approved banking and notification integrations.

## Presenter handoff

- Data Science: feature engineering, model score, threshold, and `/predict`.
- Business Intelligence: case search, behavioral tags, and `/investigate`.
- Product Development: policy engine, dispatch, dashboard, override, audit, and Orchestrate skill.
