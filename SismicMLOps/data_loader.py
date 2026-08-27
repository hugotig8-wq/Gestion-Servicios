"""Data ingestion and validation module for the seismic forecast pipeline."""

from typing import Tuple
import pandas as pd
from sismic_MLOps.config import (
    DATA_PATH,
    MIN_MAGNITUDE_FEATURE,
    TRAIN_END,
    TRAIN_START,
)


def find_column(df: pd.DataFrame, candidates: list[str], description: str) -> str:
    """Find a column in DataFrame matching candidate names (case-insensitive)."""
    normalized = {str(col).strip().lower(): col for col in df.columns}
    for candidate in candidates:
        candidate_norm = candidate.lower()
        if candidate_norm in normalized:
            return normalized[candidate_norm]

    raise ValueError(
        f"Could not identify {description}.\n"
        f"Expected one of: {candidates}\n"
        f"Available columns: {list(df.columns)}"
    )


def detect_columns(df: pd.DataFrame) -> dict[str, str]:
    """Map raw catalog column names to internal schema."""
    return {
        "time": find_column(
            df,
            ["time", "timestamp", "datetime", "date", "origin_time"],
            "timestamp",
        ),
        "latitude": find_column(df, ["latitude", "lat"], "latitude"),
        "longitude": find_column(df, ["longitude", "lon", "lng"], "longitude"),
        "magnitude": find_column(
            df, ["magnitude", "mag", "mw", "ml"], "magnitude"
        ),
        "depth": find_column(df, ["depth", "depth_km", "depthkm"], "depth"),
    }


def load_catalog() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load raw seismic catalog CSV and partition into full and training sets.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: (df_complete, df_train)
    """
    print(f"\nLoading seismic catalog: {DATA_PATH}")

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Catalog not found at {DATA_PATH}. "
            "Ensure earthquakes.csv is placed under data/raw/"
        )

    df = pd.read_csv(DATA_PATH)
    columns = detect_columns(df)

    # Standardize column naming
    df = df.rename(columns={v: k for k, v in columns.items()})

    # Cast types safely
    df["time"] = pd.to_datetime(df["time"], errors="coerce", utc=True)
    for col in ["latitude", "longitude", "magnitude", "depth"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop non-parseable records
    df = df.dropna(
        subset=["time", "latitude", "longitude", "magnitude", "depth"]
    ).copy()

    # Isolated train catalog up to cutoff
    df_train = df[
        (df["time"] >= TRAIN_START)
        & (df["time"] <= TRAIN_END)
        & (df["magnitude"] >= MIN_MAGNITUDE_FEATURE)
    ].copy()

    if len(df_train) == 0:
        raise RuntimeError("Zero training events remain after filtering.")

    return df, df_train
    
