# Real-Time Fraud Detection Engine (Inference API)

**Author:** Kelly Ndeto Kasina  
**Context:** IBM Data Science Bootcamp Capstone (Data Science & Analysis Track)  
**Collaborations:** Business Intelligence Track & Product Development Track (Watson Orchestrate)

---

## Overview
This repository houses the core anomaly detection pipeline and real-time inference API for our fintech capstone project. Designed to detect coordinated mule rings and multi-hop layering, the engine processes raw transaction payloads, engineers spatial and temporal features on the fly, and serves predictions via a serialized machine learning classifier.

This API acts as the centralized scoring endpoint, providing the high-conviction alerts required to trigger downstream Business Intelligence (Watson Discovery/NLU) and Product Development (Watson Orchestrate) workflows.

---

## Technical Architecture
* **Algorithm:** scikit-learn `HistGradientBoostingClassifier` (Tuned with strict L2 regularization and a 0.90 decision threshold to minimize false positives on highly imbalanced financial data).
* **API Framework:** FastAPI with dynamic, in-memory state tracking.
* **Data Foundation:** Mendeley Synthetic Banking Transaction Dataset.
* **Target Enterprise Infrastructure:** IBM TechZone / Red Hat OpenShift.

---

## Real-Time Feature Engineering
Standard transaction payloads are stateless. This API implements a tracking layer to transform incoming JSON requests into context-aware feature vectors by maintaining historical customer and network states:
* **Spatial Anomalies:** Calculates the Haversine distance between a customer's current and previous merchant coordinates.
* **Physical Velocity:** Computes `velocity_kmh` to identify impossible travel times (e.g., physical transactions spanning multiple countries within minutes).
* **Network Overlap:** Evaluates `customers_per_ip` and `devices_per_customer` to expose shared infrastructure indicative of coordinated mule rings.
* **Temporal Aggregations:** Computes rolling transaction frequencies (1-hour/24-hour windows) and cumulative spend ratios.

---

## End-to-End Multi-Track Capstone Architecture

To fulfill the broader IBM Capstone ecosystem, the project operates as a coordinated 3-tier architecture:

```
┌────────────────────────────────────────────────────────┐
│               Incoming Transaction Payload             │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│  Tier 1: Data Science Inference API (Port 8000)        │
│  File: main.py                                         │
│  • HistGradientBoostingClassifier                      │
│  • Haversine velocity & spatial state tracking         │
│  • Outputs: fraud_probability, flagged                 │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│  Tier 2: Business Intelligence Investigation (Port 8001)│
│  Folder: bi/                                           │
│  • Keyword search over customer case files (KYC / SAR) │
│  • Behavioral sentiment tagging (Distress vs Mule ring)│
│  • Outputs: distress_signals, mule_ring_signals        │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│  Tier 3: Product Development & Curtailment (Port 8002) │
│  Folder: product/                                      │
│  • Policy Decision Engine (FREEZE / BLOCK / STEP-UP)   │
│  • Simulated Multi-Channel Action Dispatch (Zero-Key)  │
│  • SQLite Compliance Audit Trail (audit.db)            │
│  • Human-in-the-Loop Override Capability               │
│  • IBM Watson Orchestrate Skill Contract               │
│  • Interactive Investigator Web Portal (/dashboard)    │
└────────────────────────────────────────────────────────┘
```

---

## Track Breakdown

### 1. Data Science Track (`main.py` — Port 8000)
* Centralized machine learning scoring service.
* Evaluates transaction velocity, geo-distance, device clustering, and rolling spend.
* Returns `fraud_probability` and boolean `flagged` (threshold: $\ge 0.90$).

### 2. Business Intelligence Track (`bi/` — Port 8001)
* Deep investigation layer that enriches flagged transactions.
* Scans historical case files and SAR narratives in `bi/sample_cases/`.
* Tags incidents with behavioral markers:
  * **Distress Signals:** Identifies coerced customers / social engineering victims.
  * **Mule Ring Signals:** Identifies evasive behavior, rapid fund-forwarding, or shared device infrastructure.

### 3. Product Development Track (`product/` — Port 8002)
* **Automated Curtailment Engine:** Converts scores and signals into decisive business actions:
  * `FREEZE_ACCOUNT`: High-conviction fraud + mule-ring behavioral patterns.
  * `BLOCK_TRANSACTION`: High-conviction fraud + distress/coercion markers.
  * `STEP_UP_MFA`: Elevated anomaly score ($70\% \le \text{Score} < 90\%$) triggering biometric/OTP challenge.
  * `AUTO_APPROVE`: Risk within standard tolerances ($< 70\%$).
* **Zero-Key Simulated Webhooks:** Simulates real-world execution across Core Banking lockouts, Payment Gateway declines, and Regulatory SAR drafts without requiring external paid API keys.
* **Compliance Audit Persistence:** Tracks all events, timestamps, and manual overrides in a persistent SQLite database (`product/audit.db`).
* **Watson Orchestrate Skill:** Exposes an OpenAPI 3.0 skill definition (`orchestrate_skill.json`) for catalog registration into IBM Watson Orchestrate digital employee workflows.
* **Investigator Web Portal:** Real-time visual dashboard at [`http://127.0.0.1:8002/dashboard`](http://127.0.0.1:8002/dashboard).

---

## Repository Structure

```
transaction-anomaly-api/
│
├── main.py                     # Tier 1: Data Science FastAPI Inference Engine
├── fraud_model.joblib          # Trained HistGradientBoostingClassifier model
├── model_columns.joblib        # Feature schema headers
├── requirements.txt            # Data Science dependencies
│
├── bi/                         # Tier 2: Business Intelligence Track
│   ├── main.py                 # BI FastAPI investigation service (Port 8001)
│   ├── case_search.py          # Search logic over KYC/SAR case notes
│   ├── sentiment_tags.py       # Behavioral keyword tagging (Distress & Mule)
│   ├── sample_cases/           # Test case notes (CUST1042, CUST2077)
│   ├── requirements.txt
│   └── README.md
│
├── product/                    # Tier 3: Product Development Track
│   ├── main.py                 # Product Orchestration service & UI (Port 8002)
│   ├── curtailment.py          # Decision engine & simulated action dispatchers
│   ├── audit_store.py          # Persistent SQLite audit database manager
│   ├── audit.db                # SQLite compliance event database
│   ├── orchestrate_skill.json  # IBM Watson Orchestrate OpenAPI 3.0 skill spec
│   ├── requirements.txt
│   └── README.md
│
├── gateway.py                  # UNIFIED SINGLE-URL GATEWAY (Port 8000)
├── start_all_services.py       # One-command runner for the unified gateway
├── test_unified_gateway.py     # Automated test suite for the unified gateway
├── test_e2e_pipeline.py        # Microservices integration test suite
├── .gitignore
└── README.md                   # Main project documentation
```

---

## How to Run & Use the Project

### Prerequisites
* Python 3.10+
* Virtual environment (recommended)

```bash
# 1. Clone repository
git clone https://github.com/Kasina01/transaction-anomaly-api.git
cd transaction-anomaly-api

# 2. Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
pip install -r product/requirements.txt
```

---

### Option 1: The Unified Single-URL Gateway (Recommended)
Instead of juggling multiple ports and URLs, launch the **Unified Single-URL Gateway** on **Port 8000**:

```bash
python start_all_services.py
# or: uvicorn gateway:app --reload --port 8000
```

Everything connects through this **one single URL**:
* **Central Control Hub:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/) *(Interactive dashboard with live scenario runner)*
* **Investigator Portal:** [http://127.0.0.1:8000/dashboard](http://127.0.0.1:8000/dashboard) *(Real-time alert monitoring & overrides)*
* **Unified Swagger API Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) *(All 3 tracks in one interactive Swagger UI)*
* **Watson Orchestrate Skill Spec:** [http://127.0.0.1:8000/orchestrate-skill.json](http://127.0.0.1:8000/orchestrate-skill.json)
* **Compliance Audit Trail:** [http://127.0.0.1:8000/audit-logs](http://127.0.0.1:8000/audit-logs)

---

### Option 2: Run Microservices Individually
You can run each service in separate terminal windows:

```bash
# Terminal 1: Data Science Engine (Port 8000)
uvicorn main:app --reload --port 8000

# Terminal 2: BI Investigation Layer (Port 8001)
cd bi
uvicorn main:app --reload --port 8001

# Terminal 3: Product Curtailment & Portal (Port 8002)
cd product
uvicorn main:app --reload --port 8002
```

---

### Option 3: Run the Automated Verification Suite
To verify that all 3 services, models, decision rules, audit storage, and override endpoints are working end-to-end:

```bash
python test_e2e_pipeline.py
```

Expected result:
```
======================================================================
[SUCCESS] ALL 8 TESTS PASSED! THE ENTIRE 3-TIER SYSTEM WORKS AS EXPECTED.
======================================================================
```

---

## Sample Testing Payloads

### Test Case A: Standard Legitimate Transaction (`AUTO_APPROVE`)
```json
POST http://127.0.0.1:8002/curtail
{
  "transaction_id": "TXN-AUTO-01",
  "timestamp": "2026-09-25T10:00:00",
  "customer_id": "CUST_LEGIT_01",
  "merchant_latitude": 40.7128,
  "merchant_longitude": -74.0060,
  "merchant_category": "grocery",
  "merchant_country": "US",
  "transaction_type": "pos",
  "amount": 35.50,
  "ip_address": "192.168.1.5",
  "device_id": "DEV-LEGIT-01"
}
```
**Outcome:** Risk probability is low ($\approx 20\%$). Decision is `AUTO_APPROVE`. Dispatches payment settlement simulation.

---

### Test Case B: Suspicious Mule Ring Transaction (`FREEZE_ACCOUNT`)
```json
POST http://127.0.0.1:8002/curtail
{
  "transaction_id": "TXN-MULE-01",
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
```
**Outcome:** Risk probability exceeds threshold ($\ge 90\%$), matches mule ring behavioral patterns in `CUST1042_case1.txt`. Decision is `FREEZE_ACCOUNT`. Dispatches core banking lockout, logs SAR draft in queue, and records incident in `audit.db`.