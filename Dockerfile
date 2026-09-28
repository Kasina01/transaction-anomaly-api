# IBM Technology Zone / OpenShift (OCPv) runtime image
# Built on-cluster with: oc new-build --binary --strategy=docker
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    AUDIT_DB_PATH=/tmp/audit.db \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt ./requirements-ds.txt
COPY bi/requirements.txt ./requirements-bi.txt
COPY product/requirements.txt ./requirements-product.txt
RUN pip install --upgrade pip \
    && pip install -r requirements-ds.txt \
    && pip install -r requirements-bi.txt \
    && pip install -r requirements-product.txt

COPY . .

# OpenShift assigns a random non-root UID; keep the tree world-readable.
RUN chmod -R g=u /app /tmp

EXPOSE 8080

CMD ["sh", "-c", "uvicorn gateway:app --host 0.0.0.0 --port ${PORT:-8080}"]
