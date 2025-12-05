"""
src/feature_store.py

A tiny file-backed feature store using parquet files.
"""

from pathlib import Path
import pandas as pd


class FeatureStore:
    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def path_for(self, name: str) -> Path:
        return self.base_dir / f"{name}.parquet"

    def save_features(self, df: pd.DataFrame, name: str) -> Path:
        path = self.path_for(name)
        # Use pyarrow engine for portability
        df.to_parquet(path, index=False, engine="pyarrow")
        return path

    def load_features(self, name: str) -> pd.DataFrame:
        path = self.path_for(name)
        if not path.exists():
            raise FileNotFoundError(f"Feature file not found: {path}")
        return pd.read_parquet(path, engine="pyarrow")
