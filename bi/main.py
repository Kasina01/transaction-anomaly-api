from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict
import httpx

from case_search import search_cases
from sentiment_tags import tag_case_text

app = FastAPI(title="BI Investigation Layer")

PREDICT_API_URL = "http://127.0.0.1:8000/predict"


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


@app.post("/investigate", response_model=InvestigationResult)
async def investigate(payload: TransactionPayload):
    # Step 1: call Kelly's classification API
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(
                PREDICT_API_URL, json=payload.model_dump(mode="json")
            )
            response.raise_for_status()
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Could not reach classification API at {PREDICT_API_URL}: {exc}",
            )
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Classification API returned an error: {exc.response.text}",
            )

    prediction = response.json()
    flagged = prediction.get("flagged", False)
    fraud_probability = prediction.get("fraud_probability", 0.0)

    matched_cases: List[CaseResult] = []

    # Step 2 + 3: only search and tag if the transaction was actually flagged
    if flagged:
        raw_matches = search_cases(
            customer_id=payload.customer_id, device_id=payload.device_id
        )
        for match in raw_matches:
            tags = tag_case_text(match["content"])
            matched_cases.append(
                CaseResult(
                    case_id=match["case_id"],
                    file=match["file"],
                    content=match["content"],
                    distress_signals=tags["distress_signals"],
                    mule_ring_signals=tags["mule_ring_signals"],
                )
            )

    return InvestigationResult(
        transaction_id=payload.transaction_id,
        fraud_probability=fraud_probability,
        flagged=flagged,
        matched_cases=matched_cases,
    )


@app.get("/")
def root():
    return {"status": "BI investigation layer is running. See /docs for the API."}