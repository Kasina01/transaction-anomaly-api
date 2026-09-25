# Product Development Track: Fraud Curtailment & Orchestration Layer

**Track:** IBM Data Science Bootcamp Capstone — Product Development & Watson Orchestrate Workflows  
**Component:** Automated Curtailment, Action Dispatch, Compliance Audit Trail, and Watson Orchestrate Integration  
**Port:** `8002`

---

## 1. Overview & Architectural Role

While the **Data Science Track** ([`main.py`](../main.py)) predicts anomaly probabilities and the **Business Intelligence Track** ([`bi/main.py`](../bi/main.py)) queries case narratives, this **Product Development module** closes the loop by turning insights into **enforceable, automated financial actions**.

```
┌─────────────────────────────────┐
│     Raw Incoming Transaction    │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│   Tier 1: Data Science API      │  Port 8000 (main.py)
│  (Velocity / Anomaly Scoring)   │  Output: fraud_probability, flagged
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│     Tier 2: BI Analysis API     │  Port 8001 (bi/main.py)
│   (Case Search & NLU Signals)   │  Output: distress_signals, mule_ring_signals
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│  Tier 3: Product Development    │  Port 8002 (product/main.py)
│   (Curtailment Decision Engine) │
├─────────────────────────────────┤
│ • FREEZE_ACCOUNT  (Mule rings)  │ ──► Core Banking Webhook (Simulated)
│ • BLOCK_TX        (Distress)    │ ──► SAR Regulatory Queue (Simulated)
│ • STEP_UP_MFA     (Suspicious)  │ ──► Push Biometric Challenge (Simulated)
│ • AUTO_APPROVE    (Normal)      │ ──► Settlement Gateway (Simulated)
├─────────────────────────────────┤
│ • SQLite Compliance Audit Log   │ ──► audit.db
│ • Watson Orchestrate Skill Spec │ ──► orchestrate_skill.json
│ • Investigator Review Dashboard │ ──► http://127.0.0.1:8002/dashboard
└─────────────────────────────────┘
```

---

## 2. Zero-Key Architecture

This entire module runs **100% locally with zero external API keys**:
* **Simulated Multi-Channel Webhooks:** Generates structured timestamps, reference IDs, and audit payloads for core banking lockouts, customer notifications, and regulatory SAR drafts without requiring Twilio or card processor credentials.
* **Local Audit Persistence:** Powered by Python's built-in `sqlite3` engine (`audit.db`).
* **Watson Orchestrate Compatibility:** Generates and serves the OpenAPI 3.0 specification (`orchestrate_skill.json`) for seamless catalog import into IBM Watson Orchestrate.

---

## 3. Decision Policy Matrix

| Condition | Action | Risk Tier | Automated Mitigations Dispatched |
| :--- | :---: | :---: | :--- |
| **Flagged + Mule Ring Signals** | `FREEZE_ACCOUNT` | CRITICAL | Core Banking Account Freeze, Regulatory SAR Draft, Security SMS. |
| **Flagged + Distress Signals** | `BLOCK_TRANSACTION` | HIGH_PRIORITY | Decline Authorization Code 59, Distress Support Advisory. |
| **Flagged ($\ge 90\%$ Score)** | `BLOCK_TRANSACTION` | HIGH | Payment Gateway Authorization Decline, Cardholder SMS Alert. |
| **$70\% \le \text{Score} < 90\%$** | `STEP_UP_MFA` | ELEVATED | Transaction placed on 10-min hold; Biometric Push Challenge. |
| **Score $< 70\%$** | `AUTO_APPROVE` | LOW | Immediate authorization and settlement. |

---

## 4. Key Endpoints

* **`POST /curtail`**: Ingests transaction, coordinates Tier 1 & Tier 2, executes curtailment, and logs to the audit database.
* **`POST /override`**: Allows a compliance investigator or Watson Orchestrate digital employee to manually change a decision (e.g. unfreezing a cleared account).
* **`GET /dashboard`**: Interactive Web Portal with real-time KPI metrics, audit feed, test injection, and one-click manual overrides.
* **`GET /audit-logs`**: Retrievable JSON log of all processed events for regulatory reporting.
* **`GET /stats`**: Aggregated counters (Total, Frozen, Blocked, Step-up, Approved, Overrides).
* **`GET /orchestrate-skill.json`**: Watson Orchestrate OpenAPI 3.0 skill definition.

---

## 5. Running the Service

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run the Product Service
```bash
uvicorn main:app --reload --port 8002
```

### Step 3: Access Interfaces
* **Investigator Dashboard:** [http://127.0.0.1:8002/dashboard](http://127.0.0.1:8002/dashboard)
* **Interactive Swagger UI:** [http://127.0.0.1:8002/docs](http://127.0.0.1:8002/docs)
* **Watson Orchestrate Skill Spec:** [http://127.0.0.1:8002/orchestrate-skill.json](http://127.0.0.1:8002/orchestrate-skill.json)
