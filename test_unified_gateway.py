"""
test_unified_gateway.py
Tests the Unified Single-URL Gateway on port 8000.
Verifies that all 3 tracks are accessible through ONE URL.
"""

import sys
import subprocess
import time
import httpx
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).parent


def test_gateway():
    print("=" * 70)
    print("[*] TESTING UNIFIED SINGLE-URL GATEWAY (http://127.0.0.1:8000)")
    print("=" * 70)

    # Start gateway subprocess
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "gateway:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=str(ROOT_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    client = httpx.Client(timeout=30.0)

    try:
        # 1. Wait for gateway to become ready
        print("[*] Waiting for unified gateway to initialize...")
        ready = False
        for _ in range(15):
            try:
                res = client.get("http://127.0.0.1:8000/")
                if res.status_code == 200:
                    ready = True
                    print("  [PASS] Unified Gateway is LIVE at http://127.0.0.1:8000/")
                    break
            except Exception:
                time.sleep(1)

        assert ready, "[FAIL] Gateway failed to respond in time."

        # 2. Test Central Control Hub (GET /)
        res_hub = client.get("http://127.0.0.1:8000/")
        assert res_hub.status_code == 200
        assert "Unified Fraud Control Center" in res_hub.text
        print("  [PASS] Central Control Hub (GET /) loaded successfully.")

        # 3. Test Unified Swagger Docs (GET /docs)
        res_docs = client.get("http://127.0.0.1:8000/docs")
        assert res_docs.status_code == 200
        print("  [PASS] Unified Swagger Documentation (GET /docs) loaded.")

        # 4. Test Tier 1 Data Science Endpoint (POST /predict)
        sample_legit = {
            "transaction_id": "TXN-LEGIT-001",
            "timestamp": "2026-09-26T12:00:00",
            "customer_id": "CUST_LEGIT_001",
            "merchant_latitude": 40.7128,
            "merchant_longitude": -74.0060,
            "merchant_category": "grocery",
            "merchant_country": "US",
            "transaction_type": "pos",
            "amount": 35.50,
            "ip_address": "192.168.1.5",
            "device_id": "DEV-LEGIT-001"
        }
        res_pred = client.post("http://127.0.0.1:8000/predict", json=sample_legit)
        assert res_pred.status_code == 200
        p_data = res_pred.json()
        print(f"  [PASS] Tier 1 Model Inference (POST /predict): score={p_data['fraud_probability']}, flagged={p_data['flagged']}")

        # 5. Test Tier 2 BI Investigation Endpoint (POST /investigate)
        sample_mule = {
            "transaction_id": "TXN-MULE-001",
            "timestamp": "2026-09-26T12:05:00",
            "customer_id": "CUST1042",
            "merchant_latitude": -1.286389,
            "merchant_longitude": 36.817223,
            "merchant_category": "electronics",
            "merchant_country": "KE",
            "transaction_type": "transfer",
            "amount": 95000.00,
            "ip_address": "197.232.14.5",
            "device_id": "DEV-77812"
        }
        res_inv = client.post("http://127.0.0.1:8000/investigate", json=sample_mule)
        assert res_inv.status_code == 200
        inv_data = res_inv.json()
        print(f"  [PASS] Tier 2 BI Investigation (POST /investigate): flagged={inv_data['flagged']}, cases={len(inv_data['matched_cases'])}")

        # 6. Test Tier 3 Product Full Curtailment (POST /curtail)
        res_curt = client.post("http://127.0.0.1:8000/curtail", json=sample_mule)
        assert res_curt.status_code == 200
        curt_data = res_curt.json()
        print(f"  [PASS] Tier 3 Product Curtailment (POST /curtail): action={curt_data['decision_action']}, risk={curt_data['risk_tier']}")

        # 7. Test Investigator Dashboard (GET /dashboard)
        res_dash = client.get("http://127.0.0.1:8000/dashboard")
        assert res_dash.status_code == 200
        assert "Fraud Curtailment & Orchestration Portal" in res_dash.text
        print("  [PASS] Investigator Dashboard (GET /dashboard) loaded successfully.")

        # 8. Test Watson Skill Contract (GET /orchestrate-skill.json)
        res_skill = client.get("http://127.0.0.1:8000/orchestrate-skill.json")
        assert res_skill.status_code == 200
        print("  [PASS] Watson Orchestrate Skill Definition (GET /orchestrate-skill.json) loaded.")

        print("\n" + "=" * 70)
        print("[SUCCESS] ALL UNIFIED GATEWAY TESTS PASSED ON http://127.0.0.1:8000!")
        print("=" * 70)

    finally:
        print("\nShutting down gateway test process...")
        proc.terminate()
        proc.wait()
        print("Done.")


if __name__ == "__main__":
    test_gateway()
