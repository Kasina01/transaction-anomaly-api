"""Optional Watson Discovery and watsonx.ai adapters for BI investigations."""
import json
import os
from typing import Any, Dict, List, Optional
import httpx


def _env(name: str) -> str:
    return os.getenv(name, "").strip()


def discovery_configured() -> bool:
    return all(_env(n) for n in ("IBM_DISCOVERY_URL", "IBM_DISCOVERY_APIKEY", "IBM_DISCOVERY_PROJECT_ID", "IBM_DISCOVERY_COLLECTION_ID"))


def watsonx_configured() -> bool:
    return all(_env(n) for n in ("IBM_WATSONX_URL", "IBM_WATSONX_PROJECT_ID", "IBM_WATSONX_MODEL_ID")) and bool(_env("IBM_WATSONX_TOKEN") or (_env("IBM_WATSONX_APIKEY") and _env("IBM_WATSONX_IAM_URL")))


async def discovery_search(query: str) -> List[Dict[str, Any]]:
    if not discovery_configured():
        raise RuntimeError("Watson Discovery is not configured")
    url = f"{_env('IBM_DISCOVERY_URL').rstrip('/')}/v2/projects/{_env('IBM_DISCOVERY_PROJECT_ID')}/collections/{_env('IBM_DISCOVERY_COLLECTION_ID')}/query"
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(url, params={"version": _env("IBM_DISCOVERY_VERSION") or "2020-08-30"}, auth=("apikey", _env("IBM_DISCOVERY_APIKEY")), json={"natural_language_query": query, "count": 10})
        response.raise_for_status()
        data = response.json()
    return [{
        "case_id": item.get("case_id") or item.get("document_id") or item.get("id") or "DISCOVERY_RESULT",
        "file": item.get("file") or item.get("filename") or item.get("document_id") or "Watson Discovery",
        "content": item.get("text") or item.get("content") or item.get("body") or "",
        "source": "watson_discovery",
    } for item in data.get("results", [])]


async def _watsonx_token(client: httpx.AsyncClient) -> str:
    token = _env("IBM_WATSONX_TOKEN")
    if token:
        return token
    iam_url = _env("IBM_WATSONX_IAM_URL")
    if not iam_url:
        raise RuntimeError("No TechZone-provisioned watsonx.ai token or IAM endpoint configured")
    response = await client.post(iam_url, data={"grant_type": "urn:ibm:params:oauth:grant-type:apikey", "apikey": _env("IBM_WATSONX_APIKEY")}, headers={"Content-Type": "application/x-www-form-urlencoded"})
    response.raise_for_status()
    token = response.json().get("access_token")
    if not token:
        raise RuntimeError("IAM token response did not contain an access token")
    return token


def _generated_text(data: Dict[str, Any]) -> str:
    results = data.get("results") or []
    text = results[0].get("generated_text") if results and isinstance(results[0], dict) else None
    if not isinstance(text, str) or not text.strip():
        raise RuntimeError("watsonx.ai response contained no generated text")
    return text.strip()


async def watsonx_analyze(case_text: str, transaction_context: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    if not watsonx_configured():
        raise RuntimeError("watsonx.ai is not configured")
    prompt = ("You are a financial-crime investigator. Analyze the evidence below.\n"
              "Return exactly two labelled sections: EXPLANATION: a plain-language risk explanation. "
              "MULE_BEHAVIOUR: explain supported multi-hop mule-account/layering behaviour, including intermediary accounts, rapid forwarding, shared devices/IPs, or geographic hops. Say 'No evidence found' when unsupported; do not invent facts.\n\n"
              f"TRANSACTION_CONTEXT: {json.dumps(transaction_context or {}, sort_keys=True)}\nCASE_EVIDENCE:\n{case_text}")
    url = f"{_env('IBM_WATSONX_URL').rstrip('/')}/ml/v1/text/generation"
    async with httpx.AsyncClient(timeout=30.0) as client:
        token = await _watsonx_token(client)
        response = await client.post(url, params={"version": _env("IBM_WATSONX_VERSION") or "2024-03-14"}, headers={"Authorization": f"Bearer {token}"}, json={"model_id": _env("IBM_WATSONX_MODEL_ID"), "project_id": _env("IBM_WATSONX_PROJECT_ID"), "input": prompt, "parameters": {"max_new_tokens": 500, "temperature": 0.2}})
        response.raise_for_status()
        generated = _generated_text(response.json())
    explanation, mule = generated, generated
    if "MULE_BEHAVIOUR:" in generated:
        explanation, mule = generated.split("MULE_BEHAVIOUR:", 1)
        explanation = explanation.replace("EXPLANATION:", "").strip()
        mule = mule.strip()
    return {"explanation": explanation, "mule_behavior_analysis": mule, "source": "watsonx_ai"}
