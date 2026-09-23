from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import joblib
from datetime import datetime
import math

app = FastAPI(title="Transaction Fraud Detection API")

# Load artifacts
model = joblib.load("fraud_model.joblib")
expected_columns = joblib.load("model_columns.joblib")

# In-memory stores for rolling state 
customer_state = {}
ip_tracker = {}
device_tracker = {}

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

def calc_haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return R * (2 * math.asin(math.sqrt(a)))

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Transaction Fraud Detection API is running. Go to /docs to test."}

@app.post("/predict")
def predict(tx: TransactionPayload):
    try:
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
            
            # Temporal & Spatial
            time_diff = (current_time - prev['timestamp']).total_seconds()
            time_since_last_tx = max(time_diff, 0)
            
            distance_km = calc_haversine(
                tx.merchant_latitude, tx.merchant_longitude, 
                prev['lat'], prev['lon']
            )
            
            # Velocity & Country Hopping
            hours = (time_since_last_tx / 3600) + 1e-5
            velocity_kmh = distance_km / hours
            country_changed = 1 if tx.merchant_country != prev['country'] else 0
            
            # Rolling Windows
            tx_count_1h = sum(1 for h in history if (current_time - h['time']).total_seconds() <= 3600)
            tx_count_24h = sum(1 for h in history if (current_time - h['time']).total_seconds() <= 86400)
            
            count_prev = len(history)
            total_spent = sum(h['amount'] for h in history)
            cum_avg_amount = total_spent / count_prev if count_prev > 0 else 0
            amount_ratio_to_avg = tx.amount / (cum_avg_amount + 1e-5)

            # Append current tx and clear old memory (>24h)
            history.append({'time': current_time, 'amount': tx.amount})
            prev['history'] = [h for h in history if (current_time - h['time']).total_seconds() <= 86400]
            
        else:
            # First transaction
            time_since_last_tx = 0.0
            distance_km = 0.0
            velocity_kmh = 0.0
            country_changed = 0
            tx_count_1h = 0
            tx_count_24h = 0
            amount_ratio_to_avg = 1.0
            
            customer_state[cid] = {'history': [{'time': current_time, 'amount': tx.amount}]}

        # Update core state
        customer_state[cid].update({
            'timestamp': current_time,
            'lat': tx.merchant_latitude,
            'lon': tx.merchant_longitude,
            'country': tx.merchant_country
        })

        # Feature Assembly
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

        # Format for Inference
        df = pd.DataFrame([features])
        df = pd.get_dummies(df, columns=['merchant_category', 'transaction_type'])
        df = df.reindex(columns=expected_columns, fill_value=0)

        # Execute Engine
        prob = model.predict_proba(df)[:, 1][0]
        is_fraud = 1 if prob >= 0.90 else 0

        return {
            "transaction_id": tx.transaction_id,
            "fraud_probability": float(prob),
            "flagged": bool(is_fraud)
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))