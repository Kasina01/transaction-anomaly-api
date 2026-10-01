import asyncio
import os
from unittest.mock import AsyncMock, Mock, patch

import pytest

from bi.ibm_services import discovery_search, watsonx_analyze
from bi.main import TransactionPayload, build_investigation


DISCOVERY_ENV = {
    "IBM_DISCOVERY_URL": "https://discovery.example",
    "IBM_DISCOVERY_APIKEY": "not-a-real-key",
    "IBM_DISCOVERY_PROJECT_ID": "project",
    "IBM_DISCOVERY_COLLECTION_ID": "collection",
}
WATSONX_ENV = {
    "IBM_WATSONX_URL": "https://watsonx.example",
    "IBM_WATSONX_APIKEY": "not-a-real-key",
    "IBM_WATSONX_PROJECT_ID": "project",
    "IBM_WATSONX_MODEL_ID": "model",
}


def payload():
    return TransactionPayload(transaction_id="T1", timestamp="2026-09-26T12:00:00", customer_id="CUST1042", merchant_latitude=-1.2, merchant_longitude=36.8, merchant_category="electronics", merchant_country="KE", transaction_type="transfer", amount=95000, ip_address="1.2.3.4", device_id="DEV-77812")


async def _test_discovery_response_mapping(monkeypatch):
    for key, value in DISCOVERY_ENV.items(): monkeypatch.setenv(key, value)
    response = Mock()
    response.json.return_value = {"results": [{"document_id": "D1", "filename": "case.txt", "text": "rapid forwarding"}]}
    response.raise_for_status = lambda: None
    client = AsyncMock(); client.post.return_value = response
    with patch("bi.ibm_services.httpx.AsyncClient") as factory:
        factory.return_value.__aenter__.return_value = client
        result = await discovery_search("CUST1042")
    assert result == [{"case_id": "D1", "file": "case.txt", "content": "rapid forwarding", "source": "watson_discovery"}]


async def _test_watsonx_response_handling(monkeypatch):
    for key, value in WATSONX_ENV.items(): monkeypatch.setenv(key, value)
    monkeypatch.setenv("IBM_WATSONX_TOKEN", "test-token")
    generation = Mock(); generation.json.return_value = {"results": [{"generated_text": "EXPLANATION: clear risk. MULE_BEHAVIOUR: multi-hop forwarding."}]}; generation.raise_for_status = lambda: None
    client = AsyncMock(); client.post.return_value = generation
    with patch("bi.ibm_services.httpx.AsyncClient") as factory:
        factory.return_value.__aenter__.return_value = client
        result = await watsonx_analyze("evidence")
    assert result["source"] == "watsonx_ai"
    assert result["explanation"] == "clear risk."
    assert result["mule_behavior_analysis"] == "multi-hop forwarding."


async def _test_local_fallback_when_discovery_unavailable(monkeypatch):
    monkeypatch.delenv("IBM_DISCOVERY_URL", raising=False)
    with patch("bi.main.search_cases", return_value=[{"case_id": "C1", "file": "local.txt", "content": "rapid forwarding"}]), patch("bi.main.watsonx_analyze", side_effect=RuntimeError("down")):
        result = await build_investigation(payload(), True, 0.99)
    assert result["search_source"] == "local_fallback"
    assert result["analysis_source"] == "local_fallback"
    assert result["service_source"] == "local_fallback"


async def _test_local_fallback_when_watsonx_unavailable(monkeypatch):
    with patch("bi.main.discovery_search", return_value=[{"case_id": "D1", "file": "remote.txt", "content": "same device"}]), patch("bi.main.watsonx_analyze", side_effect=RuntimeError("down")):
        result = await build_investigation(payload(), True, 0.99)
    assert result["search_source"] == "watson_discovery"
    assert result["analysis_source"] == "local_fallback"
    assert result["service_source"] == "watson_discovery"


async def _test_source_fields_not_run_when_not_flagged():
    result = await build_investigation(payload(), False, 0.1)
    assert result["search_source"] == result["analysis_source"] == result["service_source"] == "not_run"


def test_discovery_response_mapping(monkeypatch): asyncio.run(_test_discovery_response_mapping(monkeypatch))
def test_watsonx_response_handling(monkeypatch): asyncio.run(_test_watsonx_response_handling(monkeypatch))
def test_local_fallback_when_discovery_unavailable(monkeypatch): asyncio.run(_test_local_fallback_when_discovery_unavailable(monkeypatch))
def test_local_fallback_when_watsonx_unavailable(monkeypatch): asyncio.run(_test_local_fallback_when_watsonx_unavailable(monkeypatch))
def test_source_fields_not_run_when_not_flagged(): asyncio.run(_test_source_fields_not_run_when_not_flagged())




