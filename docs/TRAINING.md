# Phase 3 — Baseline Template Model (Option A)

## Purpose
A CPU-friendly, deterministic baseline that generates ad creatives from `title`, `description`, and `category`.
This is template-based (no GPU, no heavy libraries). It produces a small JSON artifact that stands in for a "model" in later MLOps phases.

## Files
- `training/train.py` — trains/writes `models/template_baseline.json` and `models/metrics.json`
- `inference/generator.py` — loads model and generates creatives
- `tests/test_baseline.py` — unit test for generation

## How to run
1. Ensure Phase 2 outputs exist:
   - `data/ingested/cleaned.csv` should be present (run ingestion if needed).
2. Activate venv:
   ```bash
   source .venv/bin/activate
