"""
training/train.py

"Train" a template-based baseline model for ad creative generation.

This script:
- reads cleaned CSV (output of Phase 2 ingestion)
- computes a couple of lightweight stats (avg lengths, popular CTAs by category)
- writes a JSON artifact under models/template_baseline.json
- produces a small metrics JSON under models/metrics.json

This is intentionally simple (no ML) and deterministic so it runs on CPU everywhere.
"""

from pathlib import Path
import json
import argparse
import pandas as pd
from collections import Counter, defaultdict


DEFAULT_CTAS = [
    "Shop now",
    "Buy today",
    "Limited time offer",
    "Grab yours",
    "Order now",
    "Learn more",
    "Get it now"
]


def compute_category_ctas(df: pd.DataFrame, top_k: int = 3) -> dict:
    """
    Heuristic: pick CTAs based on category frequency (placeholder).
    Currently returns DEFAULT_CTAS truncated or rotated per category.
    """
    categories = df["category"].fillna("general").astype(str).str.lower()
    cat_counts = categories.value_counts().to_dict()
    cat_ctas = {}
    for cat in cat_counts.keys():
        # simple deterministic selection: rotate DEFAULT_CTAS by hash of category
        idx = abs(hash(cat)) % len(DEFAULT_CTAS)
        ctalist = DEFAULT_CTAS[idx:] + DEFAULT_CTAS[:idx]
        cat_ctas[cat] = ctalist[:top_k]
    return cat_ctas


def train_template_baseline(cleaned_csv_path: str | Path, out_dir: str | Path) -> dict:
    cleaned_csv_path = Path(cleaned_csv_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(cleaned_csv_path)
    # compute basic stats
    stats = {
        "n_examples": int(len(df)),
        "avg_title_len": float(df["title"].str.len().mean()) if "title" in df.columns else 0.0,
        "avg_desc_len": float(df["description"].str.len().mean()) if "description" in df.columns else 0.0,
    }

    # compute category-based CTAs
    cat_ctas = compute_category_ctas(df, top_k=3)

    model = {
        "version": "template-v1",
        "stats": stats,
        "category_ctas": cat_ctas,
        "template_variants": [
            "{title} — {short_desc} {cta}.",
            "{short_desc} | {title}. {cta}.",
            "{title}: {short_desc} — {cta}!",
            "{short_desc} ({title}) — {cta}."
        ],
        "short_desc_max_words": 20
    }

    model_path = out_dir / "template_baseline.json"
    metrics_path = out_dir / "metrics.json"

    with open(model_path, "w", encoding="utf-8") as f:
        json.dump(model, f, indent=2)

    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    return {"model_path": str(model_path), "metrics_path": str(metrics_path)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cleaned-csv",
        "-c",
        type=str,
        default="data/ingested/cleaned.csv",
        help="Path to cleaned CSV produced by ingestion"
    )
    parser.add_argument(
        "--out-dir",
        "-o",
        type=str,
        default="models",
        help="Directory to write model artifact"
    )
    args = parser.parse_args()

    result = train_template_baseline(args.cleaned_csv, args.out_dir)
    print("Training complete. Artifacts:")
    for k, v in result.items():
        print(f" - {k}: {v}")


if __name__ == "__main__":
    main()
