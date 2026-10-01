# BI Investigation Layer

The BI service is the Business Intelligence pathway implementation for the fintech internal fraud-analytics case study.

## TechZone IBM services

This service uses only IBM services provisioned through the TechZone reservation:

- Watson Discovery for case-document search.
- watsonx.ai for plain-language investigation explanations and multi-hop mule-account/layering analysis.
- Watson NLU is unavailable and is not implemented or claimed.

The OpenShift application does not use `ibmcloud login` or IBM Cloud services outside the reservation. watsonx.ai uses either a reservation-provided `IBM_WATSONX_TOKEN` or an explicitly configured reservation-provided `IBM_WATSONX_IAM_URL`; there is no external IAM endpoint default.

## Configuration

Create OpenShift Secret `ibm-bi-services` in project `team8-fraud` with values obtained from the Ready TechZone watsonx/Discovery reservation. Never commit or print values:

- `IBM_DISCOVERY_URL`, `IBM_DISCOVERY_APIKEY`, `IBM_DISCOVERY_PROJECT_ID`, `IBM_DISCOVERY_COLLECTION_ID`
- `IBM_WATSONX_URL`, `IBM_WATSONX_TOKEN` or `IBM_WATSONX_APIKEY` plus `IBM_WATSONX_IAM_URL`, `IBM_WATSONX_PROJECT_ID`, `IBM_WATSONX_MODEL_ID`

The deployment manifest references these values from the Secret. Missing configuration, service errors, and invalid responses use the explicit local fallback.

## Investigation provenance

`POST /investigate` returns `search_source`, `analysis_source`, and `service_source`:

- `watson_discovery`: Discovery returned the case search results.
- `watsonx_ai`: watsonx.ai returned the analysis.
- `local_fallback`: local case search or keyword tagging handled an unavailable/unconfigured service.
- `not_run`: the transaction was not flagged, so investigation was skipped.

IBM integrations must only be claimed when a real deployed response returns the corresponding source values.