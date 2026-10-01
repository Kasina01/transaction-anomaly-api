import os
from datetime import datetime
from typing import List, Dict, Any
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
try:
    from .case_search import search_cases
    from .sentiment_tags import tag_case_text
    from .ibm_services import discovery_search, watsonx_analyze
except ImportError:
    from case_search import search_cases
    from sentiment_tags import tag_case_text
    from ibm_services import discovery_search, watsonx_analyze

app = FastAPI(title="BI Investigation Layer", description="Watson Discovery search and watsonx.ai analysis. Watson NLU is unavailable; local tagging is the fallback.")
PREDICT_API_URL = os.getenv("PREDICT_API_URL", "http://127.0.0.1:8000/predict")

class TransactionPayload(BaseModel):
    transaction_id: str
    timestamp: datetime
    customer_id: str
    merchant_latitude: float
    merchant_longitude: float
    merchant_category: str
    merchant_country: str
    transaction_type: str
    amount: float
    ip_address: str
    device_id: str

class CaseResult(BaseModel):
    case_id: str
    file: str
    content: str
    distress_signals: List[str]
    mule_ring_signals: List[str]

class InvestigationResult(BaseModel):
    transaction_id: str
    fraud_probability: float
    flagged: bool
    matched_cases: List[CaseResult]
    explanation: str = ""
    mule_behavior_analysis: str = ""
    search_source: str
    analysis_source: str
    service_source: str


def _service_source(search_source: str, analysis_source: str) -> str:
    sources = [s for s in (search_source, analysis_source) if s not in ("not_run", "local_fallback")]
    return "+".join(sources) if sources else ("local_fallback" if "local_fallback" in (search_source, analysis_source) else "not_run")


async def build_investigation(payload: TransactionPayload, flagged: bool, fraud_probability: float) -> Dict[str, Any]:
    result = {"transaction_id": payload.transaction_id, "fraud_probability": fraud_probability, "flagged": flagged, "matched_cases": [], "explanation": "", "mule_behavior_analysis": "", "search_source": "not_run", "analysis_source": "not_run", "service_source": "not_run"}
    if not flagged:
        return result
    query = f"customer_id {payload.customer_id} device_id {payload.device_id} transaction {payload.transaction_id}"
    try:
        raw_matches = await discovery_search(query)
        result["search_source"] = "watson_discovery"
    except Exception:
        raw_matches = search_cases(customer_id=payload.customer_id, device_id=payload.device_id)
        result["search_source"] = "local_fallback"
    combined = []
    for match in raw_matches:
        tags = tag_case_text(match.get("content", ""))
        result["matched_cases"].append({"case_id": match.get("case_id", "UNKNOWN"), "file": match.get("file", ""), "content": match.get("content", ""), "distress_signals": tags["distress_signals"], "mule_ring_signals": tags["mule_ring_signals"]})
        combined.append(match.get("content", ""))
    try:
        analysis = await watsonx_analyze("\n\n".join(combined), payload.model_dump(mode="json"))
        result.update({"explanation": analysis["explanation"], "mule_behavior_analysis": analysis["mule_behavior_analysis"], "analysis_source": "watsonx_ai"})
    except Exception:
        result["explanation"] = "Local fallback: matched case documents were reviewed with keyword signals."
        result["mule_behavior_analysis"] = "Local fallback: mule-ring keyword signals are shown in the matched cases."
        result["analysis_source"] = "local_fallback"
    result["service_source"] = _service_source(result["search_source"], result["analysis_source"])
    return result


@app.post("/investigate", response_model=InvestigationResult)
async def investigate(payload: TransactionPayload):
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(PREDICT_API_URL, json=payload.model_dump(mode="json"))
            response.raise_for_status()
        except (httpx.RequestError, httpx.HTTPStatusError) as exc:
            raise HTTPException(status_code=502, detail=f"Classification API unavailable: {exc}")
    prediction = response.json()
    return await build_investigation(payload, prediction.get("flagged", False), prediction.get("fraud_probability", 0.0))


@app.get("/")
def root():
    return {"status": "BI investigation layer is running. Watson NLU is unavailable; watsonx.ai is used for text analysis when configured."}
