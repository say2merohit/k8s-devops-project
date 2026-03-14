from fastapi import FastAPI, HTTPException
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import time
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="K8s DevOps Demo API",
    description="A FastAPI app demonstrating full DevOps lifecycle on Kubernetes",
    version="1.0.0"
)

# --- Prometheus Metrics ---
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP Requests",
    ["method", "endpoint", "status"]
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP Request Latency",
    ["endpoint"]
)

# --- Middleware for metrics ---
@app.middleware("http")
async def metrics_middleware(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    REQUEST_LATENCY.labels(endpoint=request.url.path).observe(duration)
    return response


# --- Routes ---
@app.get("/")
async def root():
    return {
        "message": "Hello from FastAPI on Kubernetes!",
        "environment": os.getenv("APP_ENV", "development"),
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Kubernetes liveness probe endpoint"""
    return {"status": "healthy"}

@app.get("/ready")
async def readiness_check():
    """Kubernetes readiness probe endpoint"""
    return {"status": "ready"}

@app.get("/info")
async def info():
    """Returns app and environment info"""
    return {
        "app": "fastapi-k8s-demo",
        "version": "1.0.0",
        "environment": os.getenv("APP_ENV", "development"),
        "pod_name": os.getenv("POD_NAME", "unknown"),
        "namespace": os.getenv("POD_NAMESPACE", "unknown"),
    }

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    if item_id <= 0:
        raise HTTPException(status_code=400, detail="item_id must be positive")
    return {"item_id": item_id, "name": f"Item {item_id}", "available": True}

@app.post("/items")
async def create_item(name: str, price: float):
    if price < 0:
        raise HTTPException(status_code=422, detail="Price cannot be negative")
    return {"name": name, "price": price, "created": True}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
