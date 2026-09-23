# Real-Time Fraud Detection Engine (Inference API)

**Author:** Kelly Ndeto Kasina  
**Context:** IBM Data Science Bootcamp Capstone (Data Science & Analysis Track)

## Overview
This repository houses the core anomaly detection pipeline and real-time inference API for our fintech capstone project. Designed to detect coordinated mule rings and multi-hop layering, the engine processes raw transaction payloads, engineers spatial and temporal features on the fly, and serves predictions via a serialized machine learning classifier.

This API acts as the centralized scoring endpoint, providing the high-conviction alerts required to trigger downstream Business Intelligence (Watson Discovery/NLU) and Product Development (Watson Orchestrate) workflows.

## Technical Architecture
* **Algorithm:** scikit-learn `HistGradientBoostingClassifier` (Tuned with strict L2 regularization and a 0.90 decision threshold to minimize false positives on highly imbalanced financial data).
* **API Framework:** FastAPI with dynamic, in-memory state tracking.
* **Data Foundation:** Mendeley Synthetic Banking Transaction Dataset.
* **Target Enterprise Infrastructure:** IBM TechZone / Red Hat OpenShift.

## Real-Time Feature Engineering
Standard transaction payloads are stateless. This API implements a tracking layer to transform incoming JSON requests into context-aware feature vectors by maintaining historical customer and network states:
* **Spatial Anomalies:** Calculates the Haversine distance between a customer's current and previous merchant coordinates.
* **Physical Velocity:** Computes `velocity_kmh` to identify impossible travel times (e.g., physical transactions spanning multiple countries within minutes).
* **Network Overlap:** Evaluates `customers_per_ip` and `devices_per_customer` to expose shared infrastructure indicative of coordinated mule rings.
* **Temporal Aggregations:** Computes rolling transaction frequencies (1-hour/24-hour windows) and cumulative spend ratios.

## Local Setup & Testing
To run the inference engine locally for integration testing:

```bash
# 1. Clone the repository
git clone [https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git)
cd YOUR_REPO_NAME

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the server
uvicorn main:app --reload

# Test using Swaagger UI
Navigate to http://127.0.0.1:8000/docs to access the interactive Swagger UI and submit test JSON payloads.