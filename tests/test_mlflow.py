from pathlib import Path
import shutil
import json
import os
from training.train import train_template_baseline

def test_mlflow_run_and_artifacts(tmp_path, monkeypatch):
    # ensure mlruns isolated for test
    mlruns_dir = tmp_path / "mlruns"
    monkeypatch.setenv("MLFLOW_TRACKING_URI", f"file:{mlruns_dir}")

    # create a tiny CSV to feed training function
    csv = tmp_path / "cleaned.csv"
    csv.write_text("id,title,description,category\n1,Sample,Short desc,general\n")

    out_dir = tmp_path / "models"
    out = train_template_baseline(str(csv), out_dir)

    # artifacts exist on disk
    assert Path(out["model_path"]).exists()
    assert Path(out["metrics_path"]).exists()

    # check mlruns dir exists and contains a run
    assert mlruns_dir.exists()
    # there should be at least one run folder under mlruns_dir
    experiments = list(mlruns_dir.iterdir())
    assert len(experiments) >= 1
    # Check that at least one run id directory exists under experiments
    found_run = False
    for exp in experiments:
        if any(exp.iterdir()):
            found_run = True
            break
    assert found_run is True
