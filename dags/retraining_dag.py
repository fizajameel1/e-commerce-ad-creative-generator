"""
Weekly Retraining Pipeline for Ad Creative Generator (complete DAG file)

- Ingestion task -> returns cleaned CSV path (via XCom)
- Training task -> trains model, saves it, pushes model_version to Pushgateway

Notes:
- Requires a Pushgateway running and reachable at PUSHGATEWAY_ADDR (default 127.0.0.1:9091).
- Adjust the training.train.train_template_baseline return structure if needed.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import sys
import time
import traceback
from typing import Dict, Any

# ---- Project root: assume this file lives in <PROJECT_ROOT>/dags ----
THIS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = THIS_DIR.parent  # ../ (one level up from dags)

# Make sure project root is importable (so training.*, monitoring.* works)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from airflow import DAG
from airflow.operators.python import PythonOperator

# Prometheus Pushgateway client
from prometheus_client import CollectorRegistry, Gauge, pushadd_to_gateway


# Pushgateway address (adjust to your environment if needed)
PUSHGATEWAY_ADDR = "127.0.0.1:9091"  # or "host.docker.internal:9091" in some setups


def run_ingestion(**context) -> str:
    """
    Run training ingestion pipeline.
    Expects:
      - data/sample_ads.csv under the project root
    Produces:
      - cleaned CSV in data/ingested/
    Returns the cleaned CSV path for the next task via XCom.
    """
    try:
        # Lazy import the project function so DAG file parses even if modules are missing
        from training.data_ingestion import ingest  # type: ignore

        source = PROJECT_ROOT / "data" / "sample_ads.csv"
        out_dir = PROJECT_ROOT / "data" / "ingested"

        if not source.exists():
            raise FileNotFoundError(f"Training source data not found: {source}")

        result = ingest(source, out_dir)
        cleaned_csv = result.get("cleaned_csv") if isinstance(result, dict) else result
        cleaned_csv_str = str(cleaned_csv)

        print(f"[INGESTION] Cleaned CSV: {cleaned_csv_str}")
        return cleaned_csv_str
    except Exception as exc:
        print("[INGESTION] Failed:", exc)
        traceback.print_exc()
        raise


def run_training(cleaned_csv: str | None = None, **context) -> None:
    """
    Train the baseline template model.
    Reads cleaned CSV and writes a model under models/.
    Also pushes model_version to Prometheus Pushgateway.
    """
    try:
        if not cleaned_csv:
            # attempt to pull from xcom if not provided directly
            ti = context["ti"]
            cleaned_csv = ti.xcom_pull(task_ids="run_ingestion")

        if not cleaned_csv:
            raise ValueError("No cleaned_csv provided to run_training")

        cleaned_csv_path = str(cleaned_csv)
        print(f"[TRAINING] Using cleaned CSV: {cleaned_csv_path}")

        # Lazy import training function
        from training.train import train_template_baseline  # type: ignore

        model_dir = PROJECT_ROOT / "models"

        out = train_template_baseline(
            cleaned_csv_path,
            model_dir,
            mlflow_run_name="weekly_airflow_retrain",
        )

        # Determine model path and model_version from returned object
        model_path = None
        model_version_raw = None

        if isinstance(out, dict):
            model_path = out.get("model_path")
            # prefer an explicit model_version field if training returns it
            model_version_raw = out.get("model_version")
        else:
            # if train function returns a path string
            model_path = out

        print(f"[TRAINING] Training output: model_path={model_path}, model_version_raw={model_version_raw}")

        # Decide on a numeric model_version to publish
        model_version_num = None
        if model_version_raw is not None:
            try:
                model_version_num = float(model_version_raw)
            except Exception:
                # if it's not directly convertible, ignore and fallback
                model_version_num = None

        if model_version_num is None:
            # fallback: if model_path contains a timestamp or version extract it, else use time-based version
            try:
                if model_path:
                    # naive attempt: parse trailing digits from filename
                    name = str(model_path)
                    import re

                    m = re.search(r"(\d+\.\d+|\d+)$", name)
                    if m:
                        model_version_num = float(m.group(1))
                # final fallback: timestamp as version
                if model_version_num is None:
                    model_version_num = float(int(time.time()))
            except Exception:
                model_version_num = float(int(time.time()))

        # Push model_version to Pushgateway
        try:
            registry = CollectorRegistry()
            g = Gauge("model_version", "Numeric model version identifier", registry=registry)
            g.set(float(model_version_num))
            pushadd_to_gateway(PUSHGATEWAY_ADDR, job="weekly_model_retraining", registry=registry)
            print(f"[TRAINING] Pushed model_version={model_version_num} to Pushgateway at {PUSHGATEWAY_ADDR}")
        except Exception as e:
            print("[TRAINING] Failed to push model_version to Pushgateway:", e)
            traceback.print_exc()

        print(f"[TRAINING] New model saved: {model_path}")
    except Exception as exc:
        print("[TRAINING] Failed:", exc)
        traceback.print_exc()
        raise


default_args = {
    "owner": "fiza",
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
}

with DAG(
    dag_id="weekly_model_retraining",
    description="Weekly retraining workflow",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval="0 3 * * 1",  # every Monday 3:00 AM
    catchup=False,
    tags=["training", "ads", "retrain"],
) as dag:

    ingestion_task = PythonOperator(
        task_id="run_ingestion",
        python_callable=run_ingestion,
    )

    training_task = PythonOperator(
        task_id="run_training",
        python_callable=run_training,
        # if you prefer template XCom use this:
        op_kwargs={"cleaned_csv": "{{ ti.xcom_pull(task_ids='run_ingestion') }}"},
    )

    ingestion_task >> training_task
