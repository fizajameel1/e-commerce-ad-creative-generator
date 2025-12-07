from fastapi import FastAPI
from pathlib import Path
from inference.generator import load_model, generate_creative
from inference.schemas import GenerateRequest, GenerateResponse

app = FastAPI(
    title="Ad Creative Generator API",
    description="Generate ad creatives using a template-based baseline model.",
    version="1.0.0",
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
    """
    ensure_model_loaded()  # <== guarantees _model is loaded or raises clear error

    creatives = []
    for i in range(3):  # return 3 variations
        creative = generate_creative(
            title=request.title,
            description=request.description,
            category=request.category,
            model=_model,
            variant_idx=i,  # deterministic variant choice
        )
        creatives.append(creative)

    return GenerateResponse(creatives=creatives)
