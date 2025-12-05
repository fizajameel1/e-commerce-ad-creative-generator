"""
training/data_ingestion.py

Simple, reproducible ingestion pipeline for Phase 2.

Improvements:
- robust header normalization (lowercasing, alias mapping)
- reads CSV with utf-8-sig to avoid BOM problems
- safer dropping of rows with missing title/description
"""

from pathlib import Path
import pandas as pd
from src.feature_store import FeatureStore


def _normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    # lowercase + strip column names
    df = df.rename(columns=lambda c: c.strip().lower() if isinstance(c, str) else c)
    # map common aliases to canonical names
    col_map = {}
    if "name" in df.columns and "title" not in df.columns:
        col_map["name"] = "title"
    if "desc" in df.columns and "description" not in df.columns:
        col_map["desc"] = "description"
    # add other tiny aliases if needed
    for orig, canon in list(col_map.items()):
        if orig in df.columns:
            df = df.rename(columns={orig: canon})
    return df


def basic_cleaning(df: pd.DataFrame) -> pd.DataFrame:
    # Normalize column names (lowercase, strip, alias mapping)
    df = _normalize_column_names(df)

    # If someone passed a dataframe with a header row as data (rare), try to detect:
    # (we keep this simple — more checks could be added later)

    # Ensure title & description columns exist (fail early with readable error)
    if "title" not in df.columns or "description" not in df.columns:
        raise ValueError(
            "Input CSV must contain 'title' and 'description' columns (case-insensitive). "
            f"Found columns: {list(df.columns)}"
        )

    # Drop rows with no title or no description
    df = df.dropna(subset=["title", "description"]).copy()

    # Convert to string, strip whitespace
    df["title"] = df["title"].astype(str).str.strip()
    df["description"] = df["description"].astype(str).str.strip()

    # Drop rows where title or description became empty after stripping
    df = df[(df["title"] != "") & (df["description"] != "")].copy()

    # Lowercase category if present
    if "category" in df.columns:
        df["category"] = df["category"].astype(str).str.lower().str.strip()

    return df


def add_basic_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["title_len"] = df["title"].str.len()
    df["desc_len"] = df["description"].str.len()
    df["num_exclaims"] = df["description"].str.count("!").fillna(0).astype(int)
    # simple categorical -> freq encoding for small dataset
    if "category" in df.columns:
        freq = df["category"].value_counts().to_dict()
        df["category_freq"] = df["category"].map(freq).fillna(0).astype(int)
    return df


def ingest(input_csv: str | Path, output_dir: str | Path) -> dict:
    """
    Run ingestion pipeline.
    Saves:
      - output_dir/cleaned.csv
      - output_dir/feature_store/features.parquet
    Returns a dict with paths for verification.
    """
    input_csv = Path(input_csv)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Read with utf-8-sig to handle BOM; be explicit about engine for pandas
    df = pd.read_csv(input_csv, encoding="utf-8-sig")

    # Cleaning + features
    df_clean = basic_cleaning(df)
    df_features = add_basic_features(df_clean)

    # save cleaned CSV
    cleaned_path = output_dir / "cleaned.csv"
    df_clean.to_csv(cleaned_path, index=False)

    # use FeatureStore to save features
    fs_dir = output_dir / "feature_store"
    fs = FeatureStore(fs_dir)
    fs.save_features(df_features, name="ads_features")

    return {
        "cleaned_csv": str(cleaned_path),
        "feature_store_path": str(fs.path_for("ads_features")),
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Run ingestion pipeline.")
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default="data/sample_ads.csv",
        help="Path to input CSV",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="data/ingested",
        help="Directory to write cleaned data and features",
    )
    args = parser.parse_args()

    paths = ingest(args.input, args.output)
    print("Ingestion complete. Outputs:")
    for k, v in paths.items():
        print(f" - {k}: {v}")


if __name__ == "__main__":
    main()
