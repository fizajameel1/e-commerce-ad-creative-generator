from pathlib import Path
import json
from inference.generator import load_model, generate_creative

def test_template_baseline_end_to_end(tmp_path):
    # create a minimal model file
    model = {
        "version": "template-v1",
        "stats": {"n_examples": 1},
        "category_ctas": {"general": ["Shop now", "Buy today"]},
        "template_variants": ["{title} — {short_desc} {cta}."],
        "short_desc_max_words": 10
    }
    model_path = tmp_path / "template.json"
    model_path.write_text(json.dumps(model))

    m = load_model(model_path)
    out = generate_creative("Test Product", "This is a short description of the product.", "General", m)
    assert isinstance(out, str) and len(out) > 10
    assert "Test Product" in out or "test product" in out.lower()
