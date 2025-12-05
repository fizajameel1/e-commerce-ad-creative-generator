import shutil
from pathlib import Path
import pandas as pd
from training.data_ingestion import ingest
from src.feature_store import FeatureStore


def test_ingest_creates_files(tmp_path):
    # copy sample data to tmp
    repo_root = Path.cwd()
    sample = repo_root / "data" / "sample_ads.csv"
    assert sample.exists(), "sample_ads.csv must exist for the test"

    tmp_input = tmp_path / "sample_ads.csv"
    shutil.copy(sample, tmp_input)

    out_dir = tmp_path / "out"
    result = ingest(tmp_input, out_dir)

    # check cleaned file exists
    cleaned = Path(result["cleaned_csv"])
    assert cleaned.exists()
    df_clean = pd.read_csv(cleaned)
    # the sample had 6 rows with one missing description -> 5 rows after cleaning
    assert len(df_clean) == 5

    # check feature store parquet exists and can be loaded
    fs_path = Path(result["feature_store_path"])
    assert fs_path.exists()

    fs = FeatureStore(fs_path.parent)
    df_features = fs.load_features("ads_features")
    assert "title_len" in df_features.columns
    assert "desc_len" in df_features.columns
    assert len(df_features) == 5
