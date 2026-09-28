# Phase 3 Rubric Evidence Map

| Criterion | Evidence in this build | Reviewer action |
|---|---|---|
| Environment & provisioning (10%) | Live TechZone route, OpenShift deployment manifest, readiness/liveness probes, health endpoint | Open the live root and `/healthz`; inspect `openshift/deployment.yaml` |
| Technical build / pathway fit (30%) | Containerized FastAPI gateway, OpenShift route, Watson Orchestrate OpenAPI skill at `/orchestrate-skill.json` | Open `/docs` and the skill JSON; explain the catalog handoff |
| Sector grounding (20%) | Banking transaction schema, fraud probability, KYC/SAR-style case files, curtailment actions, compliance audit trail | Run the legitimate and mule-ring payloads |
| Audience feature implementation (20%) | Investigator dashboard, case search/tagging, policy matrix, action dispatch, stats, audit logs, manual override | Demonstrate `/dashboard`, `/investigate`, `/curtail`, `/override`, `/audit-logs` |
| Demo & presentation (15%) | Timed walkthrough and three-track presenter split in `DEMO_SCRIPT.md` | Follow the 10–15 minute sequence |
| Documentation / handoff (5%) | Root README, deployment guide, this submission pack, payloads, and test suites | Start with `submission/README.md` |

## Current evidence status

- Local unified gateway test: passed.
- Local three-service integration test: all 8 checks passed.
- Live deployed control hub: HTTP 200 verified.
- Live route access is environment-dependent; reviewers must be able to reach the TechZone reservation route.
- Watson Orchestrate registration is prepared by the OpenAPI contract but is not claimed as completed unless the team registers it in the target Orchestrate tenant.
