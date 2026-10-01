# Live Demo Script â€” 10 to 15 Minutes

## 0:00â€“1:00 â€” Problem and promise

â€œA bank needs to distinguish a normal payment from coordinated mule activity quickly enough to stop loss, while giving investigators explainable evidence and preserving an audit trail. This build connects three tracks: model scoring, BI investigation, and automated product action.â€

Show the live control hub: `https://fraud-platform-team8-fraud.apps.itz-i8rikv.infra01-lb.tok04.techzone.ibm.com/`.

## 1:00â€“2:30 â€” Sector and audience

State the sector as fintech/banking fraud prevention. The primary audience is an internal fraud-operations team. The two demonstrated features are:

- risk and case investigation for a flagged transaction;
- automated protection with an investigator override and compliance audit evidence.

Point out the three pipeline cards on the hub and the single-port design.

## 2:30â€“4:00 â€” Architecture

Open `/docs` and explain the flow:

1. `POST /predict` engineers velocity, geo-distance, rolling frequency, spend ratio, IP overlap, and device overlap, then returns a fraud probability.
2. `POST /investigate` searches KYC/SAR case files and tags distress or mule-ring signals.
3. `POST /curtail` applies the policy matrix, dispatches simulated mitigations, and writes an audit event.

The same flow is available through separate local services on ports 8000/8001/8002, while the deployed demo exposes one reviewer-friendly URL.

## 4:00â€“6:00 â€” Normal transaction

Use the first payload in `demo_payloads.json` with `POST /curtail` in Swagger. Narrate the expected result:

- low risk;
- `AUTO_APPROVE`;
- simulated settlement dispatch;
- audit event recorded.

Use `/stats` or `/audit-logs` to show that the event is persisted.

## 6:00â€“9:00 â€” Suspicious transaction and BI enrichment

Use the `TXN-MULE-01` payload in `demo_payloads.json`. Explain that the customer/device identifiers match the sample case material. The model is stateful, so narrate the probability and action actually returned rather than promising a fixed label. If it is flagged, show the enriched case path; if it is not, explain that the low-risk branch correctly avoids unnecessary investigation. Show the response fields:

- `fraud_probability` and `flagged`;
- `matched_cases`;
- `mule_ring_signals` and `distress_signals`;
- the resulting product action and dispatched channels.

Use `/dashboard` to show the alert feed and KPI counters.

## 9:00â€“11:00 â€” Human-in-the-loop control

Use `POST /override` for the transaction ID returned by either scenario. Explain that a cleared case can be manually changed by an investigator, with notes. Refresh `/audit-logs` and show the `OVERRIDDEN` event. This demonstrates the human-in-the-loop control even when the model chooses `AUTO_APPROVE`.

## 11:00â€“12:30 â€” Watson Orchestrate handoff

Open `/orchestrate-skill.json`. Explain that the OpenAPI 3 contract exposes the curtailment action as a catalog-ready skill. The skill lets an orchestrated digital employee call the same policy endpoint and receive structured action/audit results.

## 12:30â€“14:00 â€” Operations and close

Open `/healthz` and `/docs`. Mention the OpenShift deployment configuration, readiness/liveness probes, route, and `/tmp/audit.db` runtime location. Close with the next step: connect the OpenAPI skill to Watson Orchestrate and replace simulated dispatchers with approved banking and notification integrations.

## Presenter handoff

- Data Science: feature engineering, model score, threshold, and `/predict`.
- Business Intelligence: case search, behavioral tags, and `/investigate`.
- Product Development: policy engine, dispatch, dashboard, override, audit, and Orchestrate skill.

## BI video script (exact narration and screen actions)

1. Open the live route and select `/docs`. Say: “This is the Team 8 internal fraud-operations platform. Watson NLU is unavailable, so it is not claimed here. Watson Discovery is the configured case-document search adapter, and watsonx.ai provides the plain-language and multi-hop mule-account analysis when credentials are configured.”
2. Open `POST /investigate`, paste the suspicious transaction payload, and execute it. Say: “The endpoint first scores the transaction. Investigation runs only when it is flagged.”
3. In the response, point to `search_source`, `analysis_source`, and `service_source`. Say: “These provenance fields are the live proof of which services ran. `watson_discovery` means the case search came from Discovery, `watsonx_ai` means the explanation came from watsonx.ai, and `local_fallback` means the safe local search or keyword tagging path handled an unavailable or unconfigured IBM service. `not_run` means the transaction was not flagged.”
4. Point to `matched_cases`. Say: “These are the returned case documents. The distress and mule-ring signals are shown per case.” Point to `explanation` and `mule_behavior_analysis`. Say: “This is the plain-language risk explanation and the multi-hop layering analysis. The model is instructed not to invent evidence.”
5. If the live response shows `local_fallback`, say exactly: “IBM integration is not live-configured in this deployment; the application is demonstrating its tested fallback path, so I am not claiming Discovery or watsonx.ai is working live.” If it shows IBM sources, say: “The deployed application returned these IBM source values on this real request.”
6. Execute `POST /curtail` with the same payload. Say: “The same BI implementation feeds the unified gateway and the product decision. I will now show the resulting action.” Open `/audit-logs` and `/dashboard` to show the decision and audit trail.
7. Finish on `/healthz` and `/docs`. Say: “The deployment is in the TechZone `team8-fraud` project. All service credentials are supplied only through OpenShift Secret environment variables and are never hard-coded or displayed.”
