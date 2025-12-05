# Phase 2 — Data Ingestion & Feature Store

## Purpose
This module ingests raw CSV advertising data, performs simple cleaning and feature engineering,
and writes cleaned data + feature artifacts for downstream training and serving.

## Files added
- `training/data_ingestion.py` — ingestion pipeline and CLI entrypoint
- `src/feature_store.py` — small file-backed feature store using parquet
- `data/sample_ads.csv` — sample dataset
- `tests/test_ingestion.py` — pytest tests
- `data/ingested/` — default local output when running the CLI

## How to run (local)
1. Activate your venv:
   ```bash
   source .venv/bin/activate
