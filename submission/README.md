# Phase 3 Cornerstone Project Submission Pack

## Project

**Real-Time Financial Fraud Detection & Curtailment Platform**

**Sector:** Fintech / banking fraud prevention

**Audience features:**

1. Internal fraud-operations analytics: risk scoring, case search, and behavioral signals.
2. Automated transaction protection: policy decisions, simulated action dispatch, audit trail, and investigator override.

**Pathway fit:** Watson Orchestrate integration through the published OpenAPI skill contract, with the platform deployed as a containerized OpenShift application.

## Submission links

- Live TechZone environment: <https://fraud-platform-team8-fraud.apps.itz-i8rikv.infra01-lb.tok04.techzone.ibm.com/>
- Investigator portal: <https://fraud-platform-team8-fraud.apps.itz-i8rikv.infra01-lb.tok04.techzone.ibm.com/dashboard>
- Swagger API: <https://fraud-platform-team8-fraud.apps.itz-i8rikv.infra01-lb.tok04.techzone.ibm.com/docs>
- Health check: <https://fraud-platform-team8-fraud.apps.itz-i8rikv.infra01-lb.tok04.techzone.ibm.com/healthz>

## Included materials

- [DEMO_SCRIPT.md](DEMO_SCRIPT.md): timed 10–15 minute presentation and live-click sequence.
- [SLIDES.md](SLIDES.md): concise slide-ready deck content.
- [Phase3_Fraud_Platform_Presentation.pptx](Phase3_Fraud_Platform_Presentation.pptx): generated 10-slide presentation deck.
- [create_presentation.py](create_presentation.py): reproducible deck generator.
- [WALKTHROUGH.md](WALKTHROUGH.md): setup, local run, API walkthrough, and verification commands.
- [RUBRIC_EVIDENCE.md](RUBRIC_EVIDENCE.md): direct mapping from the grading criteria to project evidence.
- [demo_payloads.json](demo_payloads.json): reusable legitimate and suspicious transaction payloads.

## Verification completed

- `test_unified_gateway.py`: all checks passed.
- `test_e2e_pipeline.py`: all 8 integration checks passed.
- Live root control hub: HTTP 200 verified.

The included mule-ring payload is a sector-grounded investigation scenario, not a hard-coded expected label. The model is stateful and its probability can vary with the service history; always narrate the returned score/action shown by the live response. The policy matrix and manual override still provide a deterministic way to demonstrate investigator control.

The local virtual environment is intentionally excluded from version control. Reviewers can reproduce it by following `WALKTHROUGH.md`.

## Recording status

The live demo is deployed and the timed presenter script is complete. A narrated screen recording was not generated in this environment because no screen recorder, audio capture, or presentation renderer is installed. Record the live walkthrough using the supplied script and deck in PowerPoint, Teams, Zoom, or OBS.
