"""Spatial binning and seismic feature engineering module."""

import math
from typing import Optional
import numpy as np
import pandas as pd
from sismic_MLOps.config import (
    CELL_KM,
    GRID_COLS,
    GRID_MIN_LAT,
    GRID_MIN_LON,
    GRID_ROWS,
    MIN_MAGNITUDE_FEATURE,
    TARGET_MAGNITUDE,
)


def km_to_lat_degrees(km: float) -> float:
    """Approximate conversion from km to latitude degrees."""
    return km / 111.32


def km_to_lon_degrees(km: float, latitude: float) -> float:
    """Approximate conversion from km to longitude degrees given latitude."""
    return km / (111.32 * math.cos(math.radians(latitude)))


def assign_grid(df: pd.DataFrame) -> Tuple[pd.DataFrame, float, float]:
    """Map earthquake lat/lon to discrete 18x18 spatial grid cells."""
    df = df.copy()

    lat_step = km_to_lat_degrees(CELL_KM)
    center_lat = GRID_MIN_LAT + (GRID_ROWS * lat_step / 2)
    lon_step = km_to_lon_degrees(CELL_KM, center_lat)

    df["grid_y"] = ((df["latitude"] - GRID_MIN_LAT) / lat_step).astype(int)
    df["grid_x"] = ((df["longitude"] - GRID_MIN_LON) / lon_step).astype(int)

    # Filter strictly inside defined grid bounds
    inside = (
        (df["grid_y"] >= 0)
        & (df["grid_y"] < GRID_ROWS)
        & (df["grid_x"] >= 0)
        & (df["grid_x"] < GRID_COLS)
    )
    df = df[inside].copy()
    df["cell_id"] = df["grid_y"] * GRID_COLS + df["grid_x"]

    return df, lat_step, lon_step


def calculate_energy(magnitude: np.ndarray) -> np.ndarray:
    """Gutenberg-Richter relative seismic energy proxy: log10(E) ~= 1.5 * M."""
    return np.power(10.0, 1.5 * magnitude)


def calculate_b_value(magnitudes: np.ndarray) -> float:
    """Maximum likelihood b-value approximation."""
    mags = np.asarray(magnitudes, dtype=float)
    mags = mags[mags >= MIN_MAGNITUDE_FEATURE]

    if len(mags) < 5:
        return np.nan

    denominator = np.mean(mags) - MIN_MAGNITUDE_FEATURE
    return (np.log10(np.e) / denominator) if denominator > 0 else np.nan


def build_backtesting_dataset(
    df: pd.DataFrame,
    cutoff_dates: Optional[pd.DatetimeIndex] = None,
    forecast_horizon_years: int = 10,
) -> pd.DataFrame:
    """Build temporal snapshots for historical backtesting.

    No events after 'cutoff' are allowed in X features.
    Target (y) checks for M >= TARGET_MAGNITUDE in the target horizon window.
    """
    print("\nBuilding temporal backtesting dataset...")

    if cutoff_dates is None:
        cutoff_dates = pd.date_range(
            start="1994-12-31", end="2003-12-31", freq="YE", tz="UTC"
        )

    windows = {
        "1y": pd.DateOffset(years=1),
        "3y": pd.DateOffset(years=3),
        "5y": pd.DateOffset(years=5),
        "10y": pd.DateOffset(years=10),
        "20y": pd.DateOffset(years=20),
    }

    lat_step = km_to_lat_degrees(CELL_KM)
    rows = []

    for cutoff in cutoff_dates:
        historical = df[df["time"] <= cutoff].copy()

        future_start = cutoff + pd.Timedelta(days=1)
        future_end = cutoff + pd.DateOffset(years=forecast_horizon_years)

        future = df[
            (df["time"] >= future_start)
            & (df["time"] <= future_end)
            & (df["magnitude"] >= TARGET_MAGNITUDE)
        ].copy()

        for grid_y in range(GRID_ROWS):
            for grid_x in range(GRID_COLS):
                cell_id = grid_y * GRID_COLS + grid_x

                hist_cell = historical[
                    (historical["grid_y"] == grid_y)
                    & (historical["grid_x"] == grid_x)
                    & (historical["magnitude"] >= MIN_MAGNITUDE_FEATURE)
                ]
                future_cell = future[
                    (future["grid_y"] == grid_y)
                    & (future["grid_x"] == grid_x)
                ]

                center_lat = GRID_MIN_LAT + (grid_y + 0.5) * lat_step
                lon_step = km_to_lon_degrees(CELL_KM, center_lat)
                center_lon = GRID_MIN_LON + (grid_x + 0.5) * lon_step

                row = {
                    "forecast_date": cutoff,
                    "cell_id": cell_id,
                    "grid_x": grid_x,
                    "grid_y": grid_y,
                    "cell_lat": center_lat,
                    "cell_lon": center_lon,
                }

                # Historical Feature Extraction
                for w_name, offset in windows.items():
                    w_events = hist_cell[hist_cell["time"] > (cutoff - offset)]
                    mags = w_events["magnitude"].values
                    depths = w_events["depth"].values
                    prefix = f"eq_{w_name}"

                    row[f"{prefix}_count"] = len(w_events)
                    if len(w_events) > 0:
                        row[f"{prefix}_max_mag"] = np.max(mags)
                        row[f"{prefix}_mean_mag"] = np.mean(mags)
                        row[f"{prefix}_std_mag"] = (
                            np.std(mags) if len(mags) > 1 else 0.0
                        )
                        row[f"{prefix}_mean_depth"] = np.mean(depths)
                        row[f"{prefix}_std_depth"] = (
                            np.std(depths) if len(depths) > 1 else 0.0
                        )
                        row[f"{prefix}_energy"] = np.sum(calculate_energy(mags))
                        row[f"{prefix}_b_value"] = calculate_b_value(mags)
                    else:
                        for metric in [
                            "max_mag",
                            "mean_mag",
                            "std_mag",
                            "mean_depth",
                            "std_depth",
                            "energy",
                        ]:
                            row[f"{prefix}_{metric}"] = 0.0
                        row[f"{prefix}_b_value"] = np.nan

                # Lifetime cell stats
                row["eq_all_count"] = len(hist_cell)
                row["eq_all_max_mag"] = (
                    hist_cell["magnitude"].max() if len(hist_cell) > 0 else 0.0
                )
                row["eq_all_mean_mag"] = (
                    hist_cell["magnitude"].mean() if len(hist_cell) > 0 else 0.0
                )
                row["eq_all_mean_depth"] = (
                    hist_cell["depth"].mean() if len(hist_cell) > 0 else 0.0
                )
                row["eq_all_b_value"] = (
                    calculate_b_value(hist_cell["magnitude"].values)
                    if len(hist_cell) > 0
                    else np.nan
                )

                # Target Definition (y)
                row["n_m5_future"] = len(future_cell)
                row["has_m5_future"] = int(len(future_cell) > 0)
                row["max_m5_future"] = (
                    future_cell["magnitude"].max()
                    if len(future_cell) > 0
                    else 0.0
                )

                rows.append(row)

    backtest = (
        pd.DataFrame(rows)
        .sort_values(["forecast_date", "cell_id"])
        .reset_index(drop=True)
    )

    return backtest
    
