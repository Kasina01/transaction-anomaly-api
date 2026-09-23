# BI Investigation Layer

This is the Business Intelligence pathway's contribution. It sits on top of
API and adds a search + tagging layer over case documents.

## What it does

1. Takes a transaction, sends it to the classification API (`/predict`).
2. If the transaction is flagged as fraud, searches local case documents
   (`sample_cases/`) for anything related to that customer or device.
3. Tags any matched case text for distress language (possible coercion /
   social-engineering victim) or mule-ring language (evasiveness,
   inconsistent answers, rapid fund forwarding).
4. Returns the prediction plus any matched, tagged cases in one response.

## Setup

```bash
python -m venv venv
# Windows:
.\venv\Scripts\Activate.ps1
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

## Running it

This service calls the classification API, so **Kelly's API needs to be
running first**, on port 8000:

```bash
# In the transaction-anomaly-api folder:
uvicorn main:app --reload
```

Then, in this folder, run the BI service on a different port:

```bash
uvicorn main:app --reload --port 8001
```

Open http://127.0.0.1:8001/docs to test it via Swagger UI.

## Example request

```
POST /investigate

{
  "transaction_id": "TXN-9001",
  "timestamp": "2026-09-23T14:00:00",
  "customer_id": "CUST1042",
  "merchant_latitude": -1.286389,
  "merchant_longitude": 36.817223,
  "merchant_category": "electronics",
  "merchant_country": "KE",
  "transaction_type": "transfer",
  "amount": 45000,
  "ip_address": "197.232.14.5",
  "device_id": "DEV-77812"
}
```

## Sample case data

`sample_cases/` contains a few made-up case documents (KYC notes, dispute
chat logs, SAR narratives) keyed to fake customer IDs `CUST1042` and
`CUST2077`, used only to test the search/tagging logic locally.

## Folder structure

```
bi/
├── main.py              # FastAPI app, /investigate endpoint
├── case_search.py        # keyword search over case documents
├── sentiment_tags.py      # keyword-based distress/mule-ring tagging
├── sample_cases/          # sample case documents for local testing
├── requirements.txt
└── README.md
```