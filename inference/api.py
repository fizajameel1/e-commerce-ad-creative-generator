from fastapi import FastAPI
from pathlib import Path
from inference.generator import load_model, generate_creative
from inference.schemas import GenerateRequest, GenerateResponse

app = FastAPI(
    title="Ad Creative Generator API",
    description="Generate ad creatives using a template-based baseline model.",
    version="1.0.0",
)

# Load model at startup
MODEL_PATH = Path("models/template_baseline.json")
_model = None


@app.on_event("startup")
def load_model_on_startup():
    global _model
    if MODEL_PATH.exists():
        _model = load_model(MODEL_PATH)
    else:
        raise FileNotFoundError(f"Model not found at {MODEL_PATH}")


@app.get("/health")
async def health_check():
    return {"status": "ok", "model_loaded": _model is not None}


@app.post("/generate", response_model=GenerateResponse)
async def generate_ads(request: GenerateRequest):
    """
    Generate 3 creative variations using the template model.
    """
    if _model is None:
        raise RuntimeError("Model not loaded")

    creatives = []
    for i in range(3):  # return 3 variations
        creative = generate_creative(
            title=request.title,
            description=request.description,
            category=request.category,
            model=_model,
            variant_idx=i  # choose variant deterministically
        )
        creatives.append(creative)

    return GenerateResponse(creatives=creatives)
