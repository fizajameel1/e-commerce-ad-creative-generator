from fastapi import FastAPI,Response
from pathlib import Path
from inference.generator import load_model, generate_creative
from inference.schemas import GenerateRequest, GenerateResponse
import time
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST


app = FastAPI(
    title="Ad Creative Generator API",
    description="Generate ad creatives using a template-based baseline model.",
    version="1.0.0",
)
REQUEST_COUNTER = Counter(
    "adgen_requests_total",
    "Total number of /generate requests",
    ["status"],  # success / error
)

REQUEST_LATENCY = Histogram(
    "adgen_request_latency_seconds",
    "Latency of /generate requests in seconds",
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0],
)

MODEL_PATH = Path("models/template_baseline.json")
_model: dict | None = None


def ensure_model_loaded() -> None:
    """Lazy-load the model if it is not already in memory."""
    global _model
    if _model is None:
        if not MODEL_PATH.exists():
            raise RuntimeError(f"Model not found at {MODEL_PATH}")
        _model = load_model(MODEL_PATH)


@app.on_event("startup")
def load_model_on_startup():
    # Try to load at startup; if it fails, we don't crash the app,
    # because ensure_model_loaded() will raise a clear error later.
    try:
        ensure_model_loaded()
    except RuntimeError as e:
        # Just log a warning; in tests/CI we still want the app to start.
        print(f"Warning during startup: {e}")


@app.get("/health")
async def health_check():
    try:
        ensure_model_loaded()
        loaded = True
    except RuntimeError:
        loaded = False
    return {"status": "ok", "model_loaded": loaded}


@app.post("/generate", response_model=GenerateResponse)
async def generate_ads(request: GenerateRequest):
    """
    Generate 3 creative variations using the template model.
    Also track request count and latency with Prometheus.
    """
    # make sure model is loaded (lazy load if needed)
    try:
        ensure_model_loaded()
    except RuntimeError:
        REQUEST_COUNTER.labels(status="error").inc()
        raise

    start = time.perf_counter()
    status_label = "success"

    try:
        creatives = []
        for i in range(3):
            creative = generate_creative(
                title=request.title,
                description=request.description,
                category=request.category,
                model=_model,
                variant_idx=i,
            )
            creatives.append(creative)
        return GenerateResponse(creatives=creatives)
    except Exception:
        status_label = "error"
        raise
    finally:
        duration = time.perf_counter() - start
        REQUEST_COUNTER.labels(status=status_label).inc()
        REQUEST_LATENCY.observe(duration)


@app.get("/metrics")
async def metrics():
    """
    Expose Prometheus metrics in the standard text format.
    Prometheus will scrape this endpoint.
    """
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)

