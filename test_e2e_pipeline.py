"""
test_e2e_pipeline.py
Automated End-to-End Integration Test for all 3 IBM Capstone Microservices:
- Port 8000: Data Science Inference Engine (FastAPI)
- Port 8001: BI Investigation Layer (FastAPI)
- Port 8002: Product Curtailment & Orchestration API (FastAPI)
"""

import subprocess
import sys
import time
import httpx
from pathlib import Path

# Fix Windows console encoding
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).parent


def run_tests():
    print("=" * 70)
    print("[*] STARTING INTEGRATION TEST SUITE FOR ALL 3 SERVICES")
    print("=" * 70)

    processes = []
    try:
        # 1. Launch Tier 1: Data Science API (Port 8000)
        print("[>] Launching Tier 1: Data Science Engine (Port 8000)...")
        p1 = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--port", "8000"],
            cwd=str(ROOT_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        processes.append(p1)

        # 2. Launch Tier 2: BI Investigation Layer (Port 8001)
        print("[>] Launching Tier 2: BI Investigation Layer (Port 8001)...")
        p2 = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--port", "8001"],
            cwd=str(ROOT_DIR / "bi"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        processes.append(p2)

        # 3. Launch Tier 3: Product Curtailment API (Port 8002)
        print("[>] Launching Tier 3: Product Curtailment & UI (Port 8002)...")
        p3 = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--port", "8002"],
            cwd=str(ROOT_DIR / "product"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        processes.append(p3)

        # Wait for all services to become healthy
        print("\n[*] Waiting for all services to initialize...")
        endpoints = [
            ("Tier 1 Data Science", "http://127.0.0.1:8000/"),
            ("Tier 2 BI Investigation", "http://127.0.0.1:8001/"),
            ("Tier 3 Product Curtailment", "http://127.0.0.1:8002/")
        ]

        for name, url in endpoints:
            ready = False
            for attempt in range(15):
                try:
                    resp = httpx.get(url, timeout=2)
                    if resp.status_code == 200:
                        ready = True
                        print(f"  [PASS] {name} is READY at {url}")
                        break
                except Exception:
                    time.sleep(1)
            if not ready:
                raise RuntimeError(f"[FAIL] Failed to reach {name} at {url} within timeout.")

        print("\n" + "=" * 70)
        print("[*] RUNNING FUNCTIONAL PIPELINE TESTS")
        print("=" * 70)

        client = httpx.Client(timeout=60.0)

        # TEST 1: Tier 1 Direct Inference Test (/predict on Port 8000)
        print("\n[TEST 1] Testing Tier 1 ML Inference (/predict)...")
        sample_tx_1 = {
            "transaction_id": "TXN-AUTO-01",
            "timestamp": "2026-09-25T10:00:00",
            "customer_id": "CUST_TEST_01",
            "merchant_latitude": 40.7128,
            "merchant_longitude": -74.0060,
            "merchant_category": "grocery",
            "merchant_country": "US",
            "transaction_type": "pos",
            "amount": 42.50,
            "ip_address": "192.168.1.10",
            "device_id": "DEV-TEST-01"
        }
        res1 = client.post("http://127.0.0.1:8000/predict", json=sample_tx_1)
        assert res1.status_code == 200, f"Expected 200, got {res1.status_code}: {res1.text}"
        data1 = res1.json()
        print(f"  [PASS] Score: {data1.get('fraud_probability'):.4f}, Flagged: {data1.get('flagged')}")
        assert "fraud_probability" in data1 and "flagged" in data1

        # TEST 2: Tier 2 Direct BI Investigation Test (/investigate on Port 8001)
        print("\n[TEST 2] Testing Tier 2 BI Investigation (/investigate)...")
        sample_tx_bi = {
            "transaction_id": "TXN-BI-01",
            "timestamp": "2026-09-25T10:05:00",
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
        res2 = client.post("http://127.0.0.1:8001/investigate", json=sample_tx_bi)
        assert res2.status_code == 200, f"Expected 200, got {res2.status_code}: {res2.text}"
        data2 = res2.json()
        print(f"  [PASS] Flagged: {data2.get('flagged')}, Matched Cases: {len(data2.get('matched_cases', []))}")
        assert "matched_cases" in data2

        # TEST 3: Tier 3 Product Full Curtailment Pipeline (/curtail on Port 8002)
        print("\n[TEST 3] Testing Tier 3 End-to-End Curtailment (/curtail)...")
        res3 = client.post("http://127.0.0.1:8002/curtail", json=sample_tx_bi)
        assert res3.status_code == 200, f"Expected 200, got {res3.status_code}: {res3.text}"
        data3 = res3.json()
        print(f"  [PASS] Decision Action: {data3.get('decision_action')}")
        print(f"  [PASS] Risk Tier: {data3.get('risk_tier')}")
        print(f"  [PASS] Reason: {data3.get('reason')}")
        print(f"  [PASS] Dispatched Mitigations ({len(data3.get('dispatched_actions', []))} channels):")
        for d in data3.get('dispatched_actions', []):
            print(f"     - Channel [{d['channel']}]: {d['operation']} -> {d['status']}")
        assert data3.get("decision_action") in ["FREEZE_ACCOUNT", "BLOCK_TRANSACTION", "STEP_UP_MFA", "AUTO_APPROVE"]

        # TEST 4: Tier 3 Human / Digital Employee Override (/override on Port 8002)
        print("\n[TEST 4] Testing Investigator Manual Override (/override)...")
        override_payload = {
            "transaction_id": "TXN-BI-01",
            "new_action": "AUTO_APPROVE",
            "notes": "Verified customer identity through biometric call verification."
        }
        res4 = client.post("http://127.0.0.1:8002/override", json=override_payload)
        assert res4.status_code == 200, f"Expected 200, got {res4.status_code}: {res4.text}"
        data4 = res4.json()
        print(f"  [PASS] Override Result: {data4.get('message')}")
        assert data4.get("success") is True

        # TEST 5: Compliance Audit Trail (/audit-logs on Port 8002)
        print("\n[TEST 5] Testing Compliance Audit Persistence (/audit-logs)...")
        res5 = client.get("http://127.0.0.1:8002/audit-logs")
        assert res5.status_code == 200
        logs = res5.json()
        print(f"  [PASS] Audited Events in SQLite: {len(logs)} records found.")
        assert len(logs) > 0
        latest_event = logs[0]
        print(f"  [PASS] Latest Event Status: {latest_event['status']} (Action: {latest_event['decision_action']})")
        assert latest_event['status'] == "OVERRIDDEN"

        # TEST 6: Operational KPIs (/stats on Port 8002)
        print("\n[TEST 6] Testing Operational Stats (/stats)...")
        res6 = client.get("http://127.0.0.1:8002/stats")
        assert res6.status_code == 200
        stats = res6.json()
        print(f"  [PASS] Metrics: Total={stats['total_transactions']}, Overridden={stats['manual_overrides']}")
        assert stats["total_transactions"] >= 1

        # TEST 7: Watson Orchestrate Skill Definition (/orchestrate-skill.json)
        print("\n[TEST 7] Testing Watson Orchestrate Skill Spec (/orchestrate-skill.json)...")
        res7 = client.get("http://127.0.0.1:8002/orchestrate-skill.json")
        assert res7.status_code == 200
        skill_spec = res7.json()
        print(f"  [PASS] OpenAPI Title: '{skill_spec['info']['title']}' (version {skill_spec['openapi']})")
        assert "paths" in skill_spec and "/curtail" in skill_spec["paths"]

        # TEST 8: Investigator Web Dashboard (/dashboard on Port 8002)
        print("\n[TEST 8] Testing Investigator Web Dashboard UI (/dashboard)...")
        res8 = client.get("http://127.0.0.1:8002/dashboard")
        assert res8.status_code == 200
        assert "Fraud Curtailment & Orchestration Portal" in res8.text
        print("  [PASS] Web Portal HTML loaded successfully (200 OK).")

        print("\n" + "=" * 70)
        print("[SUCCESS] ALL 8 TESTS PASSED! THE ENTIRE 3-TIER SYSTEM WORKS AS EXPECTED.")
        print("=" * 70)

    finally:
        print("\nShutting down test server processes...")
        for p in processes:
            p.terminate()
            p.wait()
        print("Test processes terminated cleanly.")


if __name__ == "__main__":
    run_tests()
