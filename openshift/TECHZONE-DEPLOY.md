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
5. In the console, click the user menu (top right) → **Copy login command** → **Display token**.
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
