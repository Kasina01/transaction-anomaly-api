# IBM Technology Zone OpenShift deploy (Team 8)

This app is deployed on the **reserved TechZone OCPv cluster**, not on IBM Cloud.

IBM ID used for the reservation: `manaenjoshujulius@gmail.com`

## What reviewers open

After a successful deploy, the live route hosts the whole three-track demo:

- Control hub: `https://<route>/`
- Investigator portal: `https://<route>/dashboard`
- Swagger: `https://<route>/docs`
- BI investigate API: `POST https://<route>/investigate`
- Health: `https://<route>/healthz`

## Login (TechZone reservation only)

1. Open [IBM Technology Zone](https://techzone.ibm.com) and sign in.
2. Open the **OpenShift Cluster OCPv** reservation.
3. Copy the **OCP Console** URL at the bottom of the reservation.
4. Log in as `kube:admin` with the password shown on the reservation.
5. In the console, click the user menu (top right) â†’ **Copy login command** â†’ **Display token**.
6. Paste the `oc login --token=... --server=...` command into a local terminal (do **not** run `ibmcloud login`).

## CLI deploy (from this repo)

```powershell
oc whoami
oc new-project team8-fraud --display-name="Team 8 Fintech Fraud Platform"
oc new-build --name=fraud-platform --binary --strategy=docker
oc start-build fraud-platform --from-dir=. --follow --wait
oc apply -f openshift/deployment.yaml
oc get pods
oc get route fraud-platform
```

If `new-project` is denied, use an existing TechZone project you can write to:

```powershell
oc projects
oc project <your-project>
```

## Pathway mapping on the live route

| Pathway | Owner | Live surface |
| --- | --- | --- |
| Data Science | ndetokelly@gmail.com | `POST /predict` |
| Business Intelligence | manaenjulius@gmail.com | `POST /investigate`, case search + mule/distress tags |
| Product Development | edwardmanasseh@gmail.com | `POST /curtail`, `/dashboard`, Orchestrate skill |

## BI IBM services configuration

Watson NLU is unavailable and is not implemented or claimed. Only IBM services provisioned through the TechZone reservation may be configured; do not use IBM Cloud services outside that reservation. When configured, the BI layer uses Watson Discovery for case-document search and watsonx.ai for plain-language explanations and multi-hop mule/layering analysis. If either service is missing, unavailable, or returns an error, that step uses the labelled `local_fallback` implementation. If the transaction is not flagged, all source fields are `not_run`.

Create the optional Secret in the `team8-fraud` project without putting credentials in Git or command history. Use an interactive/managed secret workflow, then restart or redeploy the app:

```powershell
oc -n team8-fraud create secret generic ibm-bi-services --from-literal=IBM_DISCOVERY_URL=... --from-literal=IBM_DISCOVERY_APIKEY=... --from-literal=IBM_DISCOVERY_PROJECT_ID=... --from-literal=IBM_DISCOVERY_COLLECTION_ID=... --from-literal=IBM_WATSONX_URL=... --from-literal=IBM_WATSONX_IAM_URL=... --from-literal=IBM_WATSONX_APIKEY=... --from-literal=IBM_WATSONX_PROJECT_ID=... --from-literal=IBM_WATSONX_MODEL_ID=...
oc -n team8-fraud rollout latest dc/fraud-platform
```

The manifest references these keys as optional Secret values. Never commit the Secret, print its values, or include API keys in demo output. `/investigate` returns `search_source`, `analysis_source`, and `service_source`; these fields are the evidence for whether IBM services were actually used.
