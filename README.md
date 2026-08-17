# E-commerce Ad Creative Generator

An end to end MLOps pipeline that generates ad creative text (headline plus call to action) from a product title, description, and category. The project was built for the MLOps Fall 2025 course and covers the full lifecycle: data ingestion, a template based baseline model, experiment tracking, a serving API, batch inference through Airflow, containerization, and monitoring.

**Author:** Fiza Jameel
**Course:** MLOps, Fall 2025

## What it does

Given a product title, description, and category, the service returns three short ad creative variations built from a deterministic, category aware template model. It is intentionally lightweight (no GPU, no heavy ML libraries) so the focus stays on the MLOps pipeline around the model rather than the model itself.

Example request to the API:

```json
{
  "title": "Cozy Wool Sweater",
  "description": "Soft winter sweater, warm and stylish.",
  "category": "clothing"
}
```

Example response:

```json
{
  "creatives": [
    "Cozy Wool Sweater — Soft winter sweater, warm and stylish. Shop now.",
    "Soft winter sweater, warm and stylish. | Cozy Wool Sweater. Buy today.",
    "Cozy Wool Sweater: Soft winter sweater, warm and stylish. — Grab yours!"
  ]
}
```

## Project structure

```
.
├── dags/                      # Airflow DAGs
│   ├── batch_inference_dag.py     # daily batch inference over sample data
│   └── retraining_dag.py          # weekly ingestion + retrain, pushes model_version to Prometheus
├── data/
│   ├── sample_ads.csv             # sample product dataset
│   └── batch_outputs/             # dated batch inference outputs
├── docs/                      # phase write ups (ingestion, training, MLflow)
├── inference/
│   ├── api.py                     # FastAPI service: /generate, /health, /metrics
│   ├── generator.py                # loads model and builds ad creatives
│   └── schemas.py                  # request/response pydantic models
├── infra/
│   ├── k8s/                       # Deployment + Service manifests
│   └── monitoring/                # Prometheus + Grafana docker-compose and configs
├── models/
│   ├── template_baseline.json      # trained model artifact
│   └── metrics.json                # training run stats
├── monitoring/
│   ├── metrics.py                  # shared Prometheus metric definitions
│   └── metrics_server.py
├── src/
│   └── feature_store.py            # small parquet backed feature store
├── training/
│   ├── data_ingestion.py           # cleans raw CSV, builds features
│   └── train.py                    # builds the template model, logs to MLflow
├── tests/                     # pytest suite covering API, ingestion, training, metrics, MLflow
├── Dockerfile
└── requirements.txt
```

## How it works

1. **Ingestion** (`training/data_ingestion.py`): reads a raw product CSV, normalizes column names, drops rows missing a title or description, and writes a cleaned CSV plus a parquet feature file through `FeatureStore`.
2. **Training** (`training/train.py`): reads the cleaned CSV, computes basic stats (example count, average title and description length), builds a category to call-to-action mapping, and writes the template model as `models/template_baseline.json`. The run, its parameters, and metrics are logged to MLflow.
3. **Serving** (`inference/api.py`): a FastAPI app that lazy loads the model and exposes:
   - `POST /generate` — returns three ad creative variations for a given product
   - `GET /health` — reports whether the model is loaded
   - `GET /metrics` — Prometheus metrics in text format
4. **Batch inference and retraining** (`dags/`): an Airflow DAG runs batch inference daily over a sample of the cleaned data, and a second DAG re-runs ingestion and training weekly, pushing the new model version to a Prometheus Pushgateway.
5. **Monitoring** (`monitoring/`, `infra/monitoring/`): request counts and latency are tracked with `prometheus-client` and scraped by Prometheus, with Grafana provisioned to visualize them.
6. **Deployment** (`Dockerfile`, `infra/k8s/`): the API is containerized and runs as an unprivileged user on port 8000, with Kubernetes manifests for a single replica Deployment and LoadBalancer Service, including liveness and readiness probes on `/health`.

## Getting started

### Prerequisites

- Python 3.10 or 3.11
- pip

### Setup

```bash
python -m venv .venv
source .venv/bin/activate      # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run ingestion and training

```bash
python -m training.data_ingestion --input data/sample_ads.csv --output data/ingested
python -m training.train --cleaned-csv data/ingested/cleaned.csv --out-dir models
```

This produces `models/template_baseline.json` and `models/metrics.json`, and logs the run to a local MLflow tracking store (`mlruns/`). View it with:

```bash
mlflow ui
```

### Run the API locally

```bash
uvicorn inference.api:app --reload --port 8000
```

Then try it:

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"title": "Cozy Wool Sweater", "description": "Soft winter sweater, warm and stylish.", "category": "clothing"}'
```

### Run with Docker

```bash
docker build -t ad-creative-api .
docker run -p 8000:8000 ad-creative-api
```

### Run tests

```bash
pytest -q
```

## CI/CD

- `.github/workflows/ci.yml` runs lint (flake8) and the full pytest suite on every push and pull request to `main`, across Python 3.10 and 3.11.
- `.github/workflows/ci-cd.yml` runs tests and, on changes to the Dockerfile, inference code, or requirements, builds and pushes the API image to Docker Hub.

## Monitoring

Prometheus scrapes `/metrics` from the API and the Pushgateway used by the retraining DAG. Bring up the monitoring stack locally with:

```bash
docker compose -f infra/monitoring/docker-compose.monitoring.yml up
```

Grafana is pre-provisioned with the Prometheus datasource from `infra/monitoring/grafana_provisioning/`.

## Notes

- The current model is a deterministic, template based baseline rather than a trained neural network. This keeps the pipeline fast and reproducible while the surrounding MLOps infrastructure (ingestion, tracking, serving, orchestration, monitoring, deployment) is fully built out.
- Airflow DAGs currently reference an absolute local project path and a local Pushgateway address; update `PROJECT_ROOT` in `dags/batch_inference_dag.py` and `PUSHGATEWAY_ADDR` in `dags/retraining_dag.py` for your own environment.
