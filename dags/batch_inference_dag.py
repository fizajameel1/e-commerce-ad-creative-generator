# batch_inference_dag.py
from __future__ import annotations
from datetime import datetime, timedelta
from pathlib import Path
import sys
import pandas as pd

# ---------- PROJECT ROOT (adjust if needed) ----------
PROJECT_ROOT = Path("/mnt/d/mlops/project/e-commerce-ad-creative-generator-fizajameel1")
pstr = str(PROJECT_ROOT)
if pstr not in sys.path:
    sys.path.insert(0, pstr)

from airflow import DAG
from airflow.operators.python import PythonOperator

def run_batch_inference(ds: str, **context):
    """
    Run batch inference for a small sample and write CSV outputs.
    This callable is instrumented with Prometheus metrics (metrics.py).
    """
    # ensure runtime path (worker process) sees project modules
    p = str(PROJECT_ROOT)
    if p not in sys.path:
        sys.path.insert(0, p)

    # import instrumentation after sys.path fix
    try:
        from monitoring.metrics import INFERENCE_COUNTER, INFERENCE_LATENCY
    except Exception:
        # If instrumentation missing, proceed but warn in logs
        INFERENCE_COUNTER = None
        INFERENCE_LATENCY = None
        print("[WARN] monitoring.metrics not available; metrics will be skipped.")

    # import project logic (inside callable)
    from inference.generator import load_model, generate_creative

    model_path = PROJECT_ROOT / "models" / "template_baseline.json"
    data_path = PROJECT_ROOT / "data" / "ingested" / "cleaned.csv"

    if not model_path.exists():
        raise FileNotFoundError(f"Missing model file: {model_path}")

    if not data_path.exists():
        raise FileNotFoundError(f"Missing cleaned CSV: {data_path}")

    # Run inference and instrument latency + status
    if INFERENCE_LATENCY:
        timer = INFERENCE_LATENCY.labels(dag="daily_batch_inference").time()
        timer.__enter__()  # start timing
    try:
        df = pd.read_csv(data_path).head(20)
        model = load_model(model_path)

        results = []
        for _, row in df.iterrows():
            creative = generate_creative(
                title=row.get("title", ""),
                description=row.get("description", ""),
                category=row.get("category", ""),
                model=model,
            )
            results.append({
                "id": row.get("id", ""),
                "title": row.get("title", ""),
                "description": row.get("description", ""),
                "category": row.get("category", ""),
                "creative": creative,
            })

        out_dir = PROJECT_ROOT / "data" / "batch_outputs" / ds
        out_dir.mkdir(parents=True, exist_ok=True)
        output = out_dir / "batch_creatives.csv"
        pd.DataFrame(results).to_csv(output, index=False)
        print(f"[Batch Inference] Saved: {output}")

        if INFERENCE_COUNTER:
            INFERENCE_COUNTER.labels(dag="daily_batch_inference", status="success").inc()
    except Exception as exc:
        if INFERENCE_COUNTER:
            INFERENCE_COUNTER.labels(dag="daily_batch_inference", status="failure").inc()
        raise
    finally:
        if INFERENCE_LATENCY:
            timer.__exit__(None, None, None)


with DAG(
    dag_id="daily_batch_inference",
    start_date=datetime(2024, 1, 1),
    schedule_interval="0 2 * * *",
    catchup=False,
    default_args={"owner": "fiza", "retries": 1, "retry_delay": timedelta(minutes=3)},
    tags=["inference", "batch"],
):
    PythonOperator(
        task_id="run_batch_inference",
        python_callable=run_batch_inference,
        op_kwargs={"ds": "{{ ds }}"},
    )
