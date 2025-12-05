"""
training/train.py

Template baseline with MLflow logging.

This script:
- reads cleaned CSV (output of Phase 2 ingestion)
- computes lightweight stats and template model
- writes JSON artifacts under out_dir
- logs params, metrics and artifacts to MLflow (local mlruns/)
"""

from pathlib import Path
import json
import argparse
import pandas as pd
from collections import Counter
import mlflow
import mlflow.exceptions

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
    categories = df["category"].fillna("general").astype(str).str.lower()
    cat_counts = categories.value_counts().to_dict()
    cat_ctas = {}
    for cat in cat_counts.keys():
        idx = abs(hash(cat)) % len(DEFAULT_CTAS)
        ctalist = DEFAULT_CTAS[idx:] + DEFAULT_CTAS[:idx]
        cat_ctas[cat] = ctalist[:top_k]
    return cat_ctas


def train_template_baseline(cleaned_csv_path: str | Path, out_dir: str | Path, mlflow_run_name: str | None = None) -> dict:
    cleaned_csv_path = Path(cleaned_csv_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(cleaned_csv_path)

    stats = {
        "n_examples": int(len(df)),
        "avg_title_len": float(df["title"].str.len().mean()) if "title" in df.columns else 0.0,
        "avg_desc_len": float(df["description"].str.len().mean()) if "description" in df.columns else 0.0,
    }

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

    # MLflow logging
    # You can override MLFLOW_TRACKING_URI via env var before running if needed.
    try:
        mlflow.set_experiment("ad-creative-generator")
        with mlflow.start_run(run_name=mlflow_run_name or "template-baseline"):
            # Log parameters
            mlflow.log_param("model_version", model["version"])
            mlflow.log_param("n_template_variants", len(model["template_variants"]))
            mlflow.log_param("short_desc_max_words", model["short_desc_max_words"])

            # Log metrics
            mlflow.log_metric("n_examples", stats["n_examples"])
            mlflow.log_metric("avg_title_len", stats["avg_title_len"])
            mlflow.log_metric("avg_desc_len", stats["avg_desc_len"])

            # Log artifacts (model + metrics JSON)
            mlflow.log_artifact(str(model_path), artifact_path="model_artifact")
            mlflow.log_artifact(str(metrics_path), artifact_path="model_artifact")

            # Add a tag to make the artifact discoverable
            mlflow.set_tag("artifact_path", str(model_path))
            run_id = mlflow.active_run().info.run_id
    except mlflow.exceptions.MlflowException as e:
        # If MLflow is not reachable or fails, still return artifact paths (non-fatal)
        run_id = None
        print("Warning: MLflow logging failed or is unavailable:", str(e))

    return {"model_path": str(model_path), "metrics_path": str(metrics_path), "mlflow_run_id": run_id}


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
    parser.add_argument(
        "--run-name",
        type=str,
        default=None,
        help="Optional MLflow run name"
    )
    args = parser.parse_args()

    result = train_template_baseline(args.cleaned_csv, args.out_dir, args.run_name)
    print("Training complete. Artifacts:")
    for k, v in result.items():
        print(f" - {k}: {v}")


if __name__ == "__main__":
    main()
