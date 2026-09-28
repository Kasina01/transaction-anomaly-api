# Slide-ready Presentation — 10 Slides

## 1. Real-Time Financial Fraud Detection & Curtailment

Fintech fraud prevention for internal fraud operations. Three tracks, one deployable control center.

## 2. The operational problem

Fraud signals arrive as isolated transactions. A useful response must combine real-time anomaly detection, historical case context, decisive action, and evidence for review.

## 3. Chosen sector and audience features

Sector: banking/fintech. Features: internal fraud-operations investigation and automated transaction protection with human override.

## 4. End-to-end architecture

Transaction → Data Science score → BI case enrichment → Product policy decision → simulated mitigation → audit trail.

## 5. Data Science track

HistGradientBoostingClassifier plus runtime features: Haversine distance, velocity, country change, rolling counts, spend ratio, shared IPs, and device reuse. Flag threshold: 90%.

## 6. Business Intelligence track

Flagged transactions search local KYC/SAR-style case notes. Keyword tagging separates distress/coercion signals from mule-ring/evasive behavior.

## 7. Product track

Policy outcomes: `AUTO_APPROVE`, `STEP_UP_MFA`, `BLOCK_TRANSACTION`, and `FREEZE_ACCOUNT`. Each outcome emits structured simulated actions and persists an audit event.

## 8. Live walkthrough

Normal payment → approve and settle. Suspicious mule scenario → score, matched case, mule signal, freeze, SAR/security actions. Investigator override → new auditable state.

## 9. Deployment and integration

Containerized OpenShift deployment with route, health probes, one public URL, Swagger, dashboard, and an OpenAPI 3 Watson Orchestrate skill contract.

## 10. Results and next steps

Both repository test suites pass. Next: register the skill in Watson Orchestrate, connect approved banking webhooks, add role-based access, and move audit storage to managed persistent storage.
