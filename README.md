# E-commerce Ad Creative Generator — MLOps Project

**Student:** FIZA JAMEEL  
**Course:** MLOps Fall 2025  
**Repo goal:** Implement an end-to-end MLOps pipeline for a text-based ad creative generator, following the project rubric. Work will be done in phases; this repo contains scaffolding for Phase 1.

## Phase 1 — Repo scaffolding
This commit adds a standardized repo layout, CI stub, basic dev requirements, and contributor notes.

## Project structure
- `src/` — application and library code (inference service, utilities)
- `training/` — training scripts, notebooks, datasets (small samples)
- `inference/` — model serving code & model-loading helpers
- `infra/` — k8s manifests, helm charts, docker-compose
- `dags/` — Airflow DAGs
- `tests/` — unit & integration tests
- `docs/` — design docs, architecture diagrams, runbook

## How to run CI locally (basic)
1. Install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
