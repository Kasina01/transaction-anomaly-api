# Reproducible Working Walkthrough

## Local setup

```powershell
cd C:\Users\ManenJ\Projects\transaction-anomaly-api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r product\requirements.txt
pip install -r bi\requirements.txt
```

## Run the unified demo

```powershell
python start_all_services.py
```

Open:

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/dashboard`
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/healthz`

The recommended demo surface is the unified gateway. It keeps all three tracks behind one URL and avoids requiring the reviewer to coordinate three terminals.

## Run the verification suites

In a second terminal:

```powershell
cd C:\Users\ManenJ\Projects\transaction-anomaly-api
.\.venv\Scripts\Activate.ps1
python test_unified_gateway.py
python test_e2e_pipeline.py
```

Expected results are an all-tests-passed message from the unified suite and 8 passed checks from the three-service suite.

## API walkthrough

Use `submission/demo_payloads.json` in Swagger or with a REST client:

```powershell
$base = 'http://127.0.0.1:8000'
$payload = Get-Content .\submission\demo_payloads.json | ConvertFrom-Json
Invoke-RestMethod "$base/curtail" -Method Post -ContentType 'application/json' -Body ($payload.legitimate | ConvertTo-Json)
Invoke-RestMethod "$base/curtail" -Method Post -ContentType 'application/json' -Body ($payload.mule_ring | ConvertTo-Json)
Invoke-RestMethod "$base/stats"
Invoke-RestMethod "$base/audit-logs"
```

The model uses in-memory transaction history, so the returned risk score/action is the source of truth for the run. For a manual override, use the transaction ID returned by either call with `POST /override` and a body such as:

```json
{
  "transaction_id": "TXN-MULE-01",
  "new_action": "AUTO_APPROVE",
  "notes": "Investigator cleared the alert after KYC review"
}
```

## OpenShift handoff

The deployment instructions are in `openshift/TECHZONE-DEPLOY.md` and the manifests are in `openshift/deployment.yaml`. The reviewer-facing route should expose `/`, `/dashboard`, `/docs`, `/investigate`, `/curtail`, and `/healthz`.
