"""
gateway.py
Unified Single-URL Gateway for the Entire IBM Fraud Detection Platform.
Unifies all 3 tracks (Data Science, Business Intelligence, Product Development)
under a single host and port: http://127.0.0.1:8000

Features:
- Single Port: 8000
- Central Mission Hub UI at GET /
- Single Unified Swagger Documentation at GET /docs
- Full Investigator Portal at GET /dashboard
- Data Science Model Inference at POST /predict
- BI Case Investigation at POST /investigate
- Product Curtailment Pipeline at POST /curtail
- IBM Watson Orchestrate Skill Contract at GET /orchestrate-skill.json
"""

import sys
from pathlib import Path

# Add module paths so all components can be imported cleanly
ROOT_DIR = Path(__file__).parent
sys.path.extend([str(ROOT_DIR), str(ROOT_DIR / "bi"), str(ROOT_DIR / "product")])

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime
import pandas as pd
import joblib
import math
import json
import warnings
from sklearn.exceptions import InconsistentVersionWarning

# Suppress version warning for clean console output
warnings.filterwarnings("ignore", category=InconsistentVersionWarning)

# Import BI components
from case_search import search_cases
from sentiment_tags import tag_case_text

# Import Product components
from curtailment import CurtailmentDecisionEngine
import audit_store

# Initialize FastAPI App with grouped tags for Swagger
app = FastAPI(
    title="IBM Transaction Fraud Detection & Curtailment Platform",
    description="Unified Enterprise Platform combining Data Science Inference, Business Intelligence Investigation, and Automated Product Curtailment.",
    version="2.0.0",
    openapi_tags=[
        {"name": "Unified Control Center", "description": "Central entry point, dashboards, and Watson skill catalog."},
        {"name": "Tier 1: Data Science Track", "description": "Real-time spatial/velocity feature engineering & machine learning inference."},
        {"name": "Tier 2: Business Intelligence Track", "description": "KYC/SAR case document search and behavioral NLP sentiment tagging."},
        {"name": "Tier 3: Product Development Track", "description": "Automated policy decisioning, multi-channel curtailment, audit persistence, and overrides."},
    ]
)

# ---------------------------------------------------------
# Load ML Model & In-Memory State
# ---------------------------------------------------------
model = joblib.load(ROOT_DIR / "fraud_model.joblib")
expected_columns = joblib.load(ROOT_DIR / "model_columns.joblib")

customer_state: Dict[str, Any] = {}
ip_tracker: Dict[str, set] = {}
device_tracker: Dict[str, set] = {}

SKILL_FILE_PATH = ROOT_DIR / "product" / "orchestrate_skill.json"


# ---------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------
class TransactionPayload(BaseModel):
    transaction_id: str
    timestamp: str
    customer_id: str
    merchant_latitude: float
    merchant_longitude: float
    merchant_category: str
    merchant_country: str
    transaction_type: str
    amount: float
    ip_address: str
    device_id: str


class OverrideRequest(BaseModel):
    transaction_id: str
    new_action: str
    notes: str


# ---------------------------------------------------------
# Internal Helper Functions
# ---------------------------------------------------------
def calc_haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return R * (2 * math.asin(math.sqrt(a)))


def run_predict_internal(tx: TransactionPayload) -> Dict[str, Any]:
    """In-process execution of Data Science Tier 1 feature engineering & prediction."""
    current_time = pd.to_datetime(tx.timestamp)
    cid = tx.customer_id

    # Network State Tracking
    ip_tracker.setdefault(tx.ip_address, set()).add(cid)
    device_tracker.setdefault(cid, set()).add(tx.device_id)

    customers_per_ip = len(ip_tracker[tx.ip_address])
    devices_per_customer = len(device_tracker[cid])

    if cid in customer_state:
        prev = customer_state[cid]
        history = prev['history']

        time_diff = (current_time - prev['timestamp']).total_seconds()
        time_since_last_tx = max(time_diff, 0)

        distance_km = calc_haversine(
            tx.merchant_latitude, tx.merchant_longitude,
            prev['lat'], prev['lon']
        )

        hours = (time_since_last_tx / 3600) + 1e-5
        velocity_kmh = distance_km / hours
        country_changed = 1 if tx.merchant_country != prev['country'] else 0

        tx_count_1h = sum(1 for h in history if (current_time - h['time']).total_seconds() <= 3600)
        tx_count_24h = sum(1 for h in history if (current_time - h['time']).total_seconds() <= 86400)

        count_prev = len(history)
        total_spent = sum(h['amount'] for h in history)
        cum_avg_amount = total_spent / count_prev if count_prev > 0 else 0
        amount_ratio_to_avg = tx.amount / (cum_avg_amount + 1e-5)

        history.append({'time': current_time, 'amount': tx.amount})
        prev['history'] = [h for h in history if (current_time - h['time']).total_seconds() <= 86400]
    else:
        time_since_last_tx = 0.0
        distance_km = 0.0
        velocity_kmh = 0.0
        country_changed = 0
        tx_count_1h = 0
        tx_count_24h = 0
        amount_ratio_to_avg = 1.0

        customer_state[cid] = {'history': [{'time': current_time, 'amount': tx.amount}]}

    customer_state[cid].update({
        'timestamp': current_time,
        'lat': tx.merchant_latitude,
        'lon': tx.merchant_longitude,
        'country': tx.merchant_country
    })

    features = {
        'amount': tx.amount,
        'time_since_last_tx': time_since_last_tx,
        'distance_km': distance_km,
        'velocity_kmh': velocity_kmh,
        'customers_per_ip': customers_per_ip,
        'devices_per_customer': devices_per_customer,
        'tx_count_1h': tx_count_1h,
        'tx_count_24h': tx_count_24h,
        'amount_ratio_to_avg': amount_ratio_to_avg,
        'country_changed': country_changed,
        'merchant_category': tx.merchant_category,
        'transaction_type': tx.transaction_type
    }

    df = pd.DataFrame([features])
    df = pd.get_dummies(df, columns=['merchant_category', 'transaction_type'])
    df = df.reindex(columns=expected_columns, fill_value=0)

    prob = float(model.predict_proba(df)[:, 1][0])
    is_fraud = bool(prob >= 0.90)

    return {
        "transaction_id": tx.transaction_id,
        "fraud_probability": round(prob, 4),
        "flagged": is_fraud
    }


def run_investigate_internal(tx: TransactionPayload, flagged: bool, fraud_prob: float) -> Dict[str, Any]:
    """In-process execution of Tier 2 BI case retrieval & behavioral tagging."""
    matched_cases = []
    distress_signals = []
    mule_ring_signals = []

    if flagged:
        raw_matches = search_cases(customer_id=tx.customer_id, device_id=tx.device_id)
        for match in raw_matches:
            tags = tag_case_text(match["content"])
            distress_signals.extend(tags["distress_signals"])
            mule_ring_signals.extend(tags["mule_ring_signals"])
            matched_cases.append({
                "case_id": match["case_id"],
                "file": match["file"],
                "content": match["content"],
                "distress_signals": tags["distress_signals"],
                "mule_ring_signals": tags["mule_ring_signals"]
            })

    return {
        "transaction_id": tx.transaction_id,
        "fraud_probability": fraud_prob,
        "flagged": flagged,
        "matched_cases": matched_cases,
        "distress_signals": list(set(distress_signals)),
        "mule_ring_signals": list(set(mule_ring_signals))
    }


# ---------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------
@app.on_event("startup")
def on_startup():
    audit_store.init_db()


# ---------------------------------------------------------
# CENTRAL CONTROL HUB (GET /)
# ---------------------------------------------------------
@app.get("/", response_class=HTMLResponse, tags=["Unified Control Center"])
def central_hub():
    """Renders the Unified Mission Control Hub connecting all project components."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <title>IBM Fraud Detection & Curtailment Platform - Unified Hub</title>
      <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-950 text-slate-100 min-h-screen font-sans antialiased">
      
      <!-- Top Navigation -->
      <nav class="border-b border-slate-800 bg-slate-900/60 backdrop-blur sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div class="flex items-center space-x-3">
            <span class="px-2.5 py-1 text-xs font-bold rounded bg-indigo-600/30 text-indigo-400 border border-indigo-500/40">IBM Capstone</span>
            <span class="text-lg font-bold tracking-tight text-white">Unified Fraud Control Center</span>
            <span class="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 font-medium">Single Port: 8000</span>
          </div>
          <div class="flex items-center space-x-3 text-sm">
            <a href="/dashboard" class="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium transition shadow-sm">
              📊 Open Investigator Portal
            </a>
            <a href="/docs" class="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 font-medium transition">
              📖 API Docs (Swagger)
            </a>
          </div>
        </div>
      </nav>

      <!-- Main Content Container -->
      <main class="max-w-7xl mx-auto px-6 py-8 space-y-8">
        
        <!-- Welcome Hero -->
        <div class="bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-slate-800 rounded-2xl p-8 relative overflow-hidden">
          <div class="max-w-3xl space-y-3">
            <div class="inline-flex items-center space-x-2 text-xs font-semibold uppercase tracking-wider text-indigo-400">
              <span>● System Active</span>
              <span class="text-slate-600">|</span>
              <span>All 3 Tracks Unified</span>
            </div>
            <h1 class="text-3xl font-extrabold text-white tracking-tight">Real-Time Financial Fraud Detection & Curtailment Platform</h1>
            <p class="text-slate-400 text-sm leading-relaxed">
              Welcome to the centralized entry point. All microservices—Data Science Anomaly Scoring, Business Intelligence Investigation, and Product Automated Curtailment—are unified here under one port.
            </p>
          </div>
        </div>

        <!-- 3-Tier Pipeline Flow Cards -->
        <div>
          <h2 class="text-sm uppercase tracking-wider font-semibold text-slate-400 mb-4">Unified Pipeline Architecture</h2>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
            
            <!-- Tier 1 -->
            <div class="bg-slate-900/80 border border-slate-800 rounded-xl p-5 hover:border-indigo-500/50 transition">
              <div class="flex items-center justify-between mb-3">
                <span class="px-2 py-0.5 text-[11px] font-bold rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">Tier 1</span>
                <span class="text-xs text-slate-500 font-mono">POST /predict</span>
              </div>
              <h3 class="text-base font-bold text-white">Data Science Engine</h3>
              <p class="text-xs text-slate-400 mt-1.5 leading-relaxed">
                Trained <code class="text-slate-300">HistGradientBoostingClassifier</code> scoring transactions in real-time with Haversine velocity and IP/device clustering.
              </p>
              <div class="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
                <span class="text-slate-500">Threshold: &ge; 90%</span>
                <a href="/docs#/Tier%201:%20Data%20Science%20Track/predict_predict_post" class="text-indigo-400 hover:text-indigo-300 font-medium">Test in Docs &rarr;</a>
              </div>
            </div>

            <!-- Tier 2 -->
            <div class="bg-slate-900/80 border border-slate-800 rounded-xl p-5 hover:border-indigo-500/50 transition">
              <div class="flex items-center justify-between mb-3">
                <span class="px-2 py-0.5 text-[11px] font-bold rounded bg-amber-500/20 text-amber-400 border border-amber-500/30">Tier 2</span>
                <span class="text-xs text-slate-500 font-mono">POST /investigate</span>
              </div>
              <h3 class="text-base font-bold text-white">BI Investigation Layer</h3>
              <p class="text-xs text-slate-400 mt-1.5 leading-relaxed">
                Queries historical KYC & SAR case documents and extracts behavioral NLP markers (Distress vs. Money Mule Rings).
              </p>
              <div class="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
                <span class="text-slate-500">Case Match + NLP</span>
                <a href="/docs#/Tier%202:%20Business%20Intelligence%20Track/investigate_investigate_post" class="text-indigo-400 hover:text-indigo-300 font-medium">Test in Docs &rarr;</a>
              </div>
            </div>

            <!-- Tier 3 -->
            <div class="bg-slate-900/80 border border-slate-800 rounded-xl p-5 hover:border-indigo-500/50 transition">
              <div class="flex items-center justify-between mb-3">
                <span class="px-2 py-0.5 text-[11px] font-bold rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">Tier 3</span>
                <span class="text-xs text-slate-500 font-mono">POST /curtail</span>
              </div>
              <h3 class="text-base font-bold text-white">Product Curtailment</h3>
              <p class="text-xs text-slate-400 mt-1.5 leading-relaxed">
                Decision engine enforcing policy actions (<code class="text-slate-300">FREEZE</code>, <code class="text-slate-300">BLOCK</code>, <code class="text-slate-300">STEP-UP</code>) with multi-channel dispatch & audit logging.
              </p>
              <div class="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
                <span class="text-slate-500">Zero-Key Mitigations</span>
                <a href="/docs#/Tier%203:%20Product%20Development%20Track/curtail_transaction_curtail_post" class="text-indigo-400 hover:text-indigo-300 font-medium">Test in Docs &rarr;</a>
              </div>
            </div>

          </div>
        </div>

        <!-- Interactive Live Simulation Console -->
        <div class="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div class="flex items-center justify-between border-b border-slate-800 pb-4">
            <div>
              <h2 class="text-base font-bold text-white">Interactive End-to-End Simulation</h2>
              <p class="text-xs text-slate-400">Run a test transaction through all 3 tiers right now with one click.</p>
            </div>
            <div class="flex gap-2">
              <button onclick="runScenario('legit')" class="px-3 py-1.5 bg-emerald-950/40 hover:bg-emerald-900/50 text-emerald-300 border border-emerald-700/50 rounded-lg text-xs font-medium transition">
                Test Case 1: Legitimate ($35)
              </button>
              <button onclick="runScenario('mule')" class="px-3 py-1.5 bg-red-950/40 hover:bg-red-900/50 text-red-300 border border-red-700/50 rounded-lg text-xs font-medium transition">
                Test Case 2: Mule Ring ($95k)
              </button>
            </div>
          </div>

          <div id="sim-output" class="bg-slate-950 rounded-xl p-4 font-mono text-xs text-slate-400 border border-slate-800 min-h-[120px] whitespace-pre-wrap overflow-x-auto">Click one of the test buttons above to simulate a transaction...</div>
        </div>

        <!-- Quick Access Directory Grid -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 pt-2">
          <a href="/dashboard" class="p-4 bg-slate-900/40 border border-slate-800/80 rounded-xl hover:bg-slate-800/60 transition block">
            <span class="text-lg">📊</span>
            <div class="font-semibold text-white text-xs mt-2">Investigator Portal</div>
            <div class="text-[11px] text-slate-400">/dashboard</div>
          </a>
          <a href="/docs" class="p-4 bg-slate-900/40 border border-slate-800/80 rounded-xl hover:bg-slate-800/60 transition block">
            <span class="text-lg">📖</span>
            <div class="font-semibold text-white text-xs mt-2">Unified API Swagger</div>
            <div class="text-[11px] text-slate-400">/docs</div>
          </a>
          <a href="/audit-logs" class="p-4 bg-slate-900/40 border border-slate-800/80 rounded-xl hover:bg-slate-800/60 transition block">
            <span class="text-lg">📜</span>
            <div class="font-semibold text-white text-xs mt-2">Compliance Audit Log</div>
            <div class="text-[11px] text-slate-400">/audit-logs</div>
          </a>
          <a href="/orchestrate-skill.json" class="p-4 bg-slate-900/40 border border-slate-800/80 rounded-xl hover:bg-slate-800/60 transition block">
            <span class="text-lg">🤖</span>
            <div class="font-semibold text-white text-xs mt-2">Watson Skill Contract</div>
            <div class="text-[11px] text-slate-400">/orchestrate-skill.json</div>
          </a>
        </div>

      </main>

      <script>
        async function runScenario(type) {
          const out = document.getElementById('sim-output');
          out.textContent = 'Processing transaction across all 3 tiers...';
          
          let payload;
          const randId = 'TXN-' + Math.floor(1000 + Math.random() * 9000);

          if (type === 'legit') {
            payload = {
              transaction_id: randId,
              timestamp: new Date().toISOString(),
              customer_id: "CUST_LEGIT_01",
              merchant_latitude: 40.7128,
              merchant_longitude: -74.0060,
              merchant_category: "grocery",
              merchant_country: "US",
              transaction_type: "pos",
              amount: 35.50,
              ip_address: "192.168.1.5",
              device_id: "DEV-LEGIT-01"
            };
          } else {
            payload = {
              transaction_id: randId,
              timestamp: new Date().toISOString(),
              customer_id: "CUST1042",
              merchant_latitude: -1.286389,
              merchant_longitude: 36.817223,
              merchant_category: "electronics",
              merchant_country: "KE",
              transaction_type: "transfer",
              amount: 95000.00,
              ip_address: "197.232.14.5",
              device_id: "DEV-77812"
            };
          }

          try {
            const res = await fetch('/curtail', {
              method: 'POST',
              headers: {'Content-Type': 'application/json'},
              body: JSON.stringify(payload)
            });
            const data = await res.json();
            out.textContent = JSON.stringify(data, null, 2);
          } catch(e) {
            out.textContent = 'Error: ' + e;
          }
        }
      </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


# ---------------------------------------------------------
# TIER 1: DATA SCIENCE ENDPOINTS
# ---------------------------------------------------------
@app.post("/predict", tags=["Tier 1: Data Science Track"])
def predict(tx: TransactionPayload):
    """
    Tier 1 Data Science Endpoint:
    Processes raw transaction, engineers spatial/temporal features, and runs HistGradientBoostingClassifier.
    """
    try:
        return run_predict_internal(tx)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# TIER 2: BUSINESS INTELLIGENCE ENDPOINTS
# ---------------------------------------------------------
@app.post("/investigate", tags=["Tier 2: Business Intelligence Track"])
def investigate(payload: TransactionPayload):
    """
    Tier 2 Business Intelligence Endpoint:
    Scores the transaction, then queries historical KYC/SAR case notes and extracts distress/mule behavioral tags.
    """
    try:
        pred = run_predict_internal(payload)
        return run_investigate_internal(payload, pred["flagged"], pred["fraud_probability"])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# TIER 3: PRODUCT DEVELOPMENT & CURTAILMENT ENDPOINTS
# ---------------------------------------------------------
@app.post("/curtail", tags=["Tier 3: Product Development Track"])
def curtail_transaction(tx: TransactionPayload):
    """
    Tier 3 Product Curtailment Endpoint:
    Executes the full pipeline in-process:
    1. Runs Data Science ML Inference.
    2. Runs BI Investigation & behavioral tagging.
    3. Evaluates enterprise Curtailment Policy.
    4. Dispatches simulated multi-channel mitigations (Core Banking, Payment Gateway, SMS).
    5. Persists compliance record to SQLite audit store.
    """
    try:
        # Step 1: Data Science Inference
        pred = run_predict_internal(tx)
        fraud_prob = pred["fraud_probability"]
        flagged = pred["flagged"]

        # Step 2: BI Investigation
        bi_res = run_investigate_internal(tx, flagged, fraud_prob)
        distress_signals = bi_res["distress_signals"]
        mule_ring_signals = bi_res["mule_ring_signals"]

        # Step 3: Product Curtailment Decision Policy
        decision = CurtailmentDecisionEngine.evaluate(
            fraud_probability=fraud_prob,
            flagged=flagged,
            distress_signals=distress_signals,
            mule_ring_signals=mule_ring_signals
        )

        action = decision["action"]
        risk_tier = decision["risk_tier"]
        reason = decision["reason"]

        # Step 4: Dispatch Simulated Mitigations
        dispatched_actions = CurtailmentDecisionEngine.dispatch_simulated_actions(
            action=action,
            transaction_id=tx.transaction_id,
            customer_id=tx.customer_id,
            amount=tx.amount,
            reason=reason
        )

        # Step 5: Persist to Compliance Audit Log
        signals = {
            "distress_signals": distress_signals,
            "mule_ring_signals": mule_ring_signals,
            "matched_cases": [{"case_id": c["case_id"], "file": c["file"]} for c in bi_res["matched_cases"]]
        }

        audit_store.log_curtailment_event(
            transaction_id=tx.transaction_id,
            customer_id=tx.customer_id,
            amount=tx.amount,
            fraud_probability=fraud_prob,
            flagged=flagged,
            decision_action=action,
            reason=reason,
            signals=signals,
            dispatched_actions=dispatched_actions,
            status="EXECUTED"
        )

        return {
            "transaction_id": tx.transaction_id,
            "customer_id": tx.customer_id,
            "amount": tx.amount,
            "fraud_probability": round(fraud_prob, 4),
            "flagged": flagged,
            "decision_action": action,
            "risk_tier": risk_tier,
            "reason": reason,
            "signals": signals,
            "dispatched_actions": dispatched_actions,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/override", tags=["Tier 3: Product Development Track"])
def manual_override(req: OverrideRequest):
    """Investigator or Watson Orchestrate digital employee overrides an automated decision."""
    valid_actions = ["AUTO_APPROVE", "BLOCK_TRANSACTION", "FREEZE_ACCOUNT", "STEP_UP_MFA"]
    if req.new_action not in valid_actions:
        raise HTTPException(status_code=400, detail=f"Invalid action. Choose from: {valid_actions}")

    success = audit_store.override_event(
        transaction_id=req.transaction_id,
        new_action=req.new_action,
        notes=req.notes
    )

    if not success:
        raise HTTPException(status_code=404, detail="Transaction not found in audit logs.")

    return {
        "success": True,
        "transaction_id": req.transaction_id,
        "new_action": req.new_action,
        "message": f"Transaction {req.transaction_id} successfully overridden to {req.new_action}."
    }


@app.get("/audit-logs", tags=["Tier 3: Product Development Track"])
def get_audit_logs(limit: int = Query(default=30, ge=1, le=100)):
    """Returns recent audit events for compliance analysis."""
    return audit_store.get_audit_events(limit=limit)


@app.get("/stats", tags=["Tier 3: Product Development Track"])
def get_stats():
    """Aggregated operational metrics."""
    return audit_store.get_metrics()


@app.get("/orchestrate-skill.json", tags=["Unified Control Center"])
def get_watson_orchestrate_skill():
    """Serves the OpenAPI 3.0 skill definition for IBM Watson Orchestrate catalog import."""
    if SKILL_FILE_PATH.exists():
        with open(SKILL_FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return JSONResponse(status_code=404, content={"error": "Skill spec file not found."})


# ---------------------------------------------------------
# INVESTIGATOR DASHBOARD (GET /dashboard)
# ---------------------------------------------------------
@app.get("/dashboard", response_class=HTMLResponse, tags=["Unified Control Center"])
def get_dashboard():
    """Serves the interactive Product Investigator & Resolution Portal."""
    from product.main import get_dashboard as product_dashboard
    return product_dashboard()


if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 70)
    print("🚀 LAUNCHING UNIFIED FRAUD PLATFORM (SINGLE PORT: 8000)")
    print("=" * 70)
    print("• Central Control Hub:         http://127.0.0.1:8000/")
    print("• Investigator Portal:         http://127.0.0.1:8000/dashboard")
    print("• Unified API Swagger Docs:    http://127.0.0.1:8000/docs")
    print("• Watson Orchestrate Skill:    http://127.0.0.1:8000/orchestrate-skill.json")
    print("=" * 70 + "\n")
    uvicorn.run("gateway:app", host="127.0.0.1", port=8000, reload=True)
