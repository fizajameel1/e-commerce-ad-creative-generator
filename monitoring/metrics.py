from prometheus_client import Counter, Histogram, Gauge, Info

# inference metrics
INFERENCE_COUNTER = Counter(
    "batch_inference_requests_total",
    "Total batch inference requests",
    ["dag", "status"]
)

INFERENCE_LATENCY = Histogram(
    "batch_inference_latency_seconds",
    "Batch inference latency (seconds)",
    ["dag"]
)

# training metrics
TRAINING_COUNTER = Counter(
    "training_runs_total",
    "Number of training runs",
    ["dag", "status"]
)

TRAINING_DURATION = Histogram(
    "training_duration_seconds",
    "Training run duration seconds",
    ["dag"]
)

# model metadata
MODEL_INFO = Info("model_info", "Model metadata")
MODEL_VERSION = Gauge("model_version", "Numeric model version identifier")

def set_model_info(version: str, extra: dict = None):
    MODEL_INFO.info({"version": version, **(extra or {})})
    try:
        MODEL_VERSION.set(float(version))
    except Exception:
        pass