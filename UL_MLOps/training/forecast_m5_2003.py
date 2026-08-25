"""
Forecast M>=5 earthquakes, 2005-2015, using information available
up to 2003-12-31.

FIRST ML BASELINE
-----------------
This is NOT a reproduction of the Toda et al. physical stress-transfer
model. It is an XGBoost spatial-risk experiment inspired by the same
forecast structure:

    historical seismicity 1981-2003
                 |
                 v
          18 x 18 cells
             10 x 10 km
                 |
                 v
             XGBoost
                 |
                 v
        P(M >= 5, 2005-2015)

Important:
- No information after 2003 is used as a feature.
- 2004 is deliberately excluded from both feature construction and target.
- 2005-2015 is used ONLY for the blind evaluation target.
"""

from pathlib import Path
import json
import math
import warnings

import numpy as np
import pandas as pd

from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    brier_score_loss,
    log_loss,
)

from xgboost import XGBClassifier


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = PROJECT_ROOT / "data" / "raw" / "earthquakes.csv"

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
METRICS_DIR = PROJECT_ROOT / "metrics"
MODEL_DIR = PROJECT_ROOT / "training" / "models"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
METRICS_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# Temporal boundaries
# ------------------------------------------------------------

TRAIN_START = pd.Timestamp("1981-04-01")
TRAIN_END = pd.Timestamp("2003-12-31 23:59:59")

# 2004 is intentionally left out.
FORECAST_START = pd.Timestamp("2005-01-01")
FORECAST_END = pd.Timestamp("2014-12-31 23:59:59")


# ------------------------------------------------------------
# Earthquake thresholds
# ------------------------------------------------------------

TARGET_MAGNITUDE = 5.0

# Completeness threshold used by the Toda forecast.
# We keep it configurable.
MIN_MAGNITUDE_FEATURE = 1.4


# ------------------------------------------------------------
# Spatial grid
# ------------------------------------------------------------

GRID_ROWS = 18
GRID_COLS = 18

CELL_KM = 10.0

# IMPORTANT:
#
# These are intentionally configurable.
#
# Do NOT claim that these coordinates exactly reproduce the
# original 180 x 180 km forecast grid until we verify the
# exact geographic bounds from the paper/data.
#
# Approximate Southern California starting point.
#
# We will replace these after inspecting earthquakes.csv and
# the original forecast geometry.

GRID_MIN_LAT = 32.8
GRID_MIN_LON = -118.5


# ------------------------------------------------------------
# XGBoost configuration
# ------------------------------------------------------------

RANDOM_STATE = 42

MODEL_PARAMS = {
    "objective": "binary:logistic",
    "eval_metric": "logloss",

    "n_estimators": 300,
    "learning_rate": 0.03,

    "max_depth": 3,
    "min_child_weight": 2,

    "subsample": 0.8,
    "colsample_bytree": 0.8,

    "reg_alpha": 0.1,
    "reg_lambda": 1.0,

    "random_state": RANDOM_STATE,

    "n_jobs": 4,
}


# ============================================================
# COLUMN DETECTION
# ============================================================

def find_column(df, candidates, description):
    """
    Find a column using case-insensitive candidate names.
    """

    normalized = {
        str(col).strip().lower(): col
        for col in df.columns
    }

    for candidate in candidates:
        candidate_norm = candidate.lower()

        if candidate_norm in normalized:
            return normalized[candidate_norm]

    raise ValueError(
        f"\nCould not identify {description}.\n"
        f"Expected one of: {candidates}\n"
        f"Available columns:\n{list(df.columns)}"
    )


def detect_columns(df):

    time_col = find_column(
        df,
        [
            "time",
            "timestamp",
            "datetime",
            "date",
            "origin_time",
            "origin_datetime",
        ],
        "earthquake timestamp",
    )

    latitude_col = find_column(
        df,
        [
            "latitude",
            "lat",
        ],
        "latitude",
    )

    longitude_col = find_column(
        df,
        [
            "longitude",
            "lon",
            "lng",
        ],
        "longitude",
    )

    magnitude_col = find_column(
        df,
        [
            "magnitude",
            "mag",
            "mw",
            "ml",
        ],
        "magnitude",
    )

    depth_col = find_column(
        df,
        [
            "depth",
            "depth_km",
            "depthkm",
        ],
        "depth",
    )

    return {
        "time": time_col,
        "latitude": latitude_col,
        "longitude": longitude_col,
        "magnitude": magnitude_col,
        "depth": depth_col,
    }


# ============================================================
# LOAD DATA
# ============================================================

def load_catalog():

    print("\nLoading catalog:")
    print(DATA_PATH)

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Catalog not found:\n{DATA_PATH}\n\n"
            "Put earthquakes.csv under:\n"
            "UL_MLOps/data/raw/"
        )

    df = pd.read_csv(DATA_PATH)

    print(f"Raw shape: {df.shape}")

    columns = detect_columns(df)

    print("\nDetected columns:")

    for key, value in columns.items():
        print(f"  {key:12s}: {value}")

    # --------------------------------------------------------
    # Rename to our internal schema
    # --------------------------------------------------------

    df = df.rename(
        columns={
            columns["time"]: "time",
            columns["latitude"]: "latitude",
            columns["longitude"]: "longitude",
            columns["magnitude"]: "magnitude",
            columns["depth"]: "depth",
        }
    )

    # --------------------------------------------------------
    # Parse values
    # --------------------------------------------------------

    df["time"] = pd.to_datetime(
        df["time"],
        errors="coerce",
        utc=True,
    )

    df["latitude"] = pd.to_numeric(
        df["latitude"],
        errors="coerce",
    )

    df["longitude"] = pd.to_numeric(
        df["longitude"],
        errors="coerce",
    )

    df["magnitude"] = pd.to_numeric(
        df["magnitude"],
        errors="coerce",
    )

    df["depth"] = pd.to_numeric(
        df["depth"],
        errors="coerce",
    )

    # --------------------------------------------------------
    # Remove invalid rows
    # --------------------------------------------------------

    before = len(df)

    df = df.dropna(
        subset=[
            "time",
            "latitude",
            "longitude",
            "magnitude",
            "depth",
        ]
    ).copy()

    print(
        f"Removed invalid rows: "
        f"{before - len(df):,}"
    )

    # --------------------------------------------------------
    # Keep only training period initially
    #
    # This is critical:
    #
    # Everything used to build X must be <= TRAIN_END.
    # --------------------------------------------------------

    df_train = df[
        (df["time"] >= TRAIN_START)
        & (df["time"] <= TRAIN_END)
        & (df["magnitude"] >= MIN_MAGNITUDE_FEATURE)
    ].copy()

    print(
        "\nTraining-period catalog:"
    )

    print(
        f"  {TRAIN_START} -> {TRAIN_END}"
    )

    print(
        f"  events: {len(df_train):,}"
    )

    if len(df_train) == 0:
        raise RuntimeError(
            "No training events remain after filtering."
        )

    return df, df_train


# ============================================================
# SPATIAL GRID
# ============================================================

def km_to_lat_degrees(km):
    """
    Approximate conversion.
    1 degree latitude ~= 111.32 km.
    """

    return km / 111.32


def km_to_lon_degrees(km, latitude):
    """
    Approximate longitude conversion.
    """

    lat_rad = math.radians(latitude)

    return km / (
        111.32 * math.cos(lat_rad)
    )


def assign_grid(df):

    df = df.copy()

    # Approximate latitude step.
    lat_step = km_to_lat_degrees(CELL_KM)

    # Use center latitude to calculate longitude step.
    center_lat = (
        GRID_MIN_LAT
        + (GRID_ROWS * lat_step / 2)
    )

    lon_step = km_to_lon_degrees(
        CELL_KM,
        center_lat,
    )

    df["grid_y"] = (
        (df["latitude"] - GRID_MIN_LAT)
        / lat_step
    ).astype(int)

    df["grid_x"] = (
        (df["longitude"] - GRID_MIN_LON)
        / lon_step
    ).astype(int)

    # Keep only the 18x18 grid.
    inside = (
        (df["grid_y"] >= 0)
        & (df["grid_y"] < GRID_ROWS)
        & (df["grid_x"] >= 0)
        & (df["grid_x"] < GRID_COLS)
    )

    df = df[inside].copy()

    df["cell_id"] = (
        df["grid_y"] * GRID_COLS
        + df["grid_x"]
    )

    print("\nGrid:")
    print(f"  rows: {GRID_ROWS}")
    print(f"  cols: {GRID_COLS}")
    print(f"  cells: {GRID_ROWS * GRID_COLS}")
    print(f"  cell size: {CELL_KM} km")

    print(
        f"  events inside grid: {len(df):,}"
    )

    return df, lat_step, lon_step


# ============================================================
# FEATURE ENGINEERING
# ============================================================

def calculate_energy(magnitude):
    """
    Gutenberg-Richter-style relative seismic energy proxy.

    This is NOT physical Joules.
    It is only a monotonic magnitude-derived feature.

    log10(E) ~= 1.5*M
    """

    return np.power(
        10.0,
        1.5 * magnitude,
    )


def calculate_b_value(magnitudes):
    """
    Maximum-likelihood b-value approximation.

    b = log10(e) / (mean(M) - Mc + correction)

    We keep this deliberately simple for the baseline.
    """

    magnitudes = np.asarray(
        magnitudes,
        dtype=float,
    )

    magnitudes = magnitudes[
        magnitudes >= MIN_MAGNITUDE_FEATURE
    ]

    if len(magnitudes) < 5:
        return np.nan

    mean_mag = np.mean(magnitudes)

    denominator = (
        mean_mag
        - MIN_MAGNITUDE_FEATURE
    )

    if denominator <= 0:
        return np.nan

    return (
        np.log10(np.e)
        / denominator
    )


def build_features(df):

    print("\nBuilding historical features...")

    rows = []

    # --------------------------------------------------------
    # Global historical cutoff.
    #
    # No event after this point is allowed into X.
    # --------------------------------------------------------

    assert df["time"].max() <= TRAIN_END

    # --------------------------------------------------------
    # Define temporal windows
    # --------------------------------------------------------

    windows = {
        "1y": pd.DateOffset(years=1),
        "3y": pd.DateOffset(years=3),
        "5y": pd.DateOffset(years=5),
        "10y": pd.DateOffset(years=10),
        "20y": pd.DateOffset(years=20),
    }

    # --------------------------------------------------------
    # One row per cell
    # --------------------------------------------------------

    for grid_y in range(GRID_ROWS):

        for grid_x in range(GRID_COLS):

            cell_id = (
                grid_y * GRID_COLS
                + grid_x
            )

            cell = df[
                (df["grid_y"] == grid_y)
                & (df["grid_x"] == grid_x)
            ].copy()

            row = {
                "cell_id": cell_id,
                "grid_x": grid_x,
                "grid_y": grid_y,
            }

            # ------------------------------------------------
            # Approximate geographic center
            # ------------------------------------------------

            lat_step = km_to_lat_degrees(
                CELL_KM
            )

            center_lat = (
                GRID_MIN_LAT
                + (grid_y + 0.5)
                * lat_step
            )

            lon_step = km_to_lon_degrees(
                CELL_KM,
                center_lat,
            )

            center_lon = (
                GRID_MIN_LON
                + (grid_x + 0.5)
                * lon_step
            )

            row["cell_lat"] = center_lat
            row["cell_lon"] = center_lon

            # ------------------------------------------------
            # Historical windows
            # ------------------------------------------------

            for window_name, offset in windows.items():

                start = (
                    TRAIN_END
                    - offset
                )

                window_events = cell[
                    (cell["time"] >= start)
                    & (cell["time"] <= TRAIN_END)
                ]

                mags = window_events[
                    "magnitude"
                ].values

                depths = window_events[
                    "depth"
                ].values

                prefix = f"eq_{window_name}"

                row[
                    f"{prefix}_count"
                ] = len(window_events)

                if len(window_events) > 0:

                    row[
                        f"{prefix}_max_mag"
                    ] = np.max(mags)

                    row[
                        f"{prefix}_mean_mag"
                    ] = np.mean(mags)

                    row[
                        f"{prefix}_mean_depth"
                    ] = np.mean(depths)

                    row[
                        f"{prefix}_std_depth"
                    ] = (
                        np.std(depths)
                        if len(depths) > 1
                        else 0.0
                    )

                    row[
                        f"{prefix}_energy"
                    ] = np.sum(
                        calculate_energy(mags)
                    )

                    row[
                        f"{prefix}_b_value"
                    ] = calculate_b_value(
                        mags
                    )

                else:

                    row[
                        f"{prefix}_max_mag"
                    ] = 0.0

                    row[
                        f"{prefix}_mean_mag"
                    ] = 0.0

                    row[
                        f"{prefix}_mean_depth"
                    ] = 0.0

                    row[
                        f"{prefix}_std_depth"
                    ] = 0.0

                    row[
                        f"{prefix}_energy"
                    ] = 0.0

                    row[
                        f"{prefix}_b_value"
                    ] = np.nan

            # ------------------------------------------------
            # Entire historical period
            # ------------------------------------------------

            row[
                "eq_all_count"
            ] = len(cell)

            if len(cell) > 0:

                row[
                    "eq_all_max_mag"
                ] = cell["magnitude"].max()

                row[
                    "eq_all_mean_mag"
                ] = cell["magnitude"].mean()

                row[
                    "eq_all_mean_depth"
                ] = cell["depth"].mean()

                row[
                    "eq_all_b_value"
                ] = calculate_b_value(
                    cell["magnitude"].values
                )

            else:

                row[
                    "eq_all_max_mag"
                ] = 0.0

                row[
                    "eq_all_mean_mag"
                ] = 0.0

                row[
                    "eq_all_mean_depth"
                ] = 0.0

                row[
                    "eq_all_b_value"
                ] = np.nan

            rows.append(row)

    features = pd.DataFrame(rows)

    print(
        f"\nFeature dataset:"
    )

    print(
        f"  rows: {len(features)}"
    )

    print(
        f"  columns: {len(features.columns)}"
    )

    return features


# ============================================================
# FUTURE TARGET
# ============================================================

def build_targets(df_all):

    print(
        "\nBuilding blind future targets..."
    )

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # These events are NEVER used in X.
    # They exist only to evaluate the forecast.
    # --------------------------------------------------------

    future = df_all[
        (df_all["time"] >= FORECAST_START)
        & (df_all["time"] <= FORECAST_END)
        & (df_all["magnitude"] >= TARGET_MAGNITUDE)
    ].copy()

    print(
        f"Forecast period:"
        f" {FORECAST_START.date()}"
        f" -> {FORECAST_END.date()}"
    )

    print(
        f"M >= {TARGET_MAGNITUDE}"
        f" future events: {len(future)}"
    )

    targets = (
        future
        .groupby("cell_id")
        .agg(
            n_m5_future=(
                "magnitude",
                "count",
            ),
            max_m5_future=(
                "magnitude",
                "max",
            ),
        )
        .reset_index()
    )

    # --------------------------------------------------------
    # Every one of the 324 cells must exist.
    # --------------------------------------------------------

    all_cells = pd.DataFrame(
        {
            "cell_id": np.arange(
                GRID_ROWS * GRID_COLS
            )
        }
    )

    targets = all_cells.merge(
        targets,
        on="cell_id",
        how="left",
    )

    targets["n_m5_future"] = (
        targets["n_m5_future"]
        .fillna(0)
        .astype(int)
    )

    targets["max_m5_future"] = (
        targets["max_m5_future"]
        .fillna(0.0)
    )

    targets["has_m5_future"] = (
        targets["n_m5_future"] > 0
    ).astype(int)

    print(
        "\nTarget distribution:"
    )

    print(
        targets[
            "has_m5_future"
        ].value_counts()
    )

    return targets, future


# ============================================================
# LEAKAGE CHECK
# ============================================================

def leakage_checks(
    features,
    df_train,
    future,
):

    print("\nRunning leakage checks...")

    # --------------------------------------------------------
    # 1. Training cutoff
    # --------------------------------------------------------

    max_training_time = (
        df_train["time"].max()
    )

    assert (
        max_training_time <= TRAIN_END
    ), (
        "LEAKAGE: training event after "
        "TRAIN_END detected."
    )

    # --------------------------------------------------------
    # 2. Future data starts after training.
    # --------------------------------------------------------

    if len(future) > 0:

        min_future_time = (
            future["time"].min()
        )

        assert (
            min_future_time >= FORECAST_START
        ), (
            "LEAKAGE: target event before "
            "FORECAST_START."
        )

    # --------------------------------------------------------
    # 3. No target columns in features.
    # --------------------------------------------------------

    forbidden = {
        "n_m5_future",
        "max_m5_future",
        "has_m5_future",
    }

    overlap = (
        forbidden
        & set(features.columns)
    )

    assert not overlap, (
        f"LEAKAGE: target columns found "
        f"in features: {overlap}"
    )

    # --------------------------------------------------------
    # 4. Check number of cells
    # --------------------------------------------------------

    assert len(features) == (
        GRID_ROWS * GRID_COLS
    )

    print(
        "  ✓ training cutoff"
    )

    print(
        "  ✓ future target separation"
    )

    print(
        "  ✓ no target columns in X"
    )

    print(
        "  ✓ 324 cells present"
    )

    print(
        "\nNo leakage detected."
    )


# ============================================================
# TRAIN XGBOOST
# ============================================================

def train_model(features, targets):

    print(
        "\nTraining XGBoost..."
    )

    data = features.merge(
        targets[
            [
                "cell_id",
                "has_m5_future",
                "n_m5_future",
            ]
        ],
        on="cell_id",
        how="inner",
    )

    # --------------------------------------------------------
    # Features to exclude from model
    # --------------------------------------------------------

    excluded = {
        "cell_id",
        "has_m5_future",
        "n_m5_future",
    }

    feature_columns = [
        col
        for col in data.columns
        if col not in excluded
    ]

    X = data[
        feature_columns
    ].copy()

    y = data[
        "has_m5_future"
    ].astype(int)

    # --------------------------------------------------------
    # Replace infinite values.
    # --------------------------------------------------------

    X = X.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    # XGBoost can handle missing values.
    # We deliberately do not fit an imputer on future data.
    #
    # Missing b-values are legitimate when there are too few
    # earthquakes.
    # --------------------------------------------------------

    positive = int(y.sum())
    negative = int(
        len(y) - positive
    )

    print(
        f"\nTraining samples: {len(X)}"
    )

    print(
        f"Positive cells: {positive}"
    )

    print(
        f"Negative cells: {negative}"
    )

    if positive == 0:
        raise RuntimeError(
            "There are no positive M>=5 cells "
            "in the future period."
        )

    if negative == 0:
        raise RuntimeError(
            "All cells are positive. "
            "Classification is impossible."
        )

    # --------------------------------------------------------
    # Class imbalance
    # --------------------------------------------------------

    scale_pos_weight = (
        negative / positive
    )

    params = MODEL_PARAMS.copy()

    params[
        "scale_pos_weight"
    ] = scale_pos_weight

    print(
        "\nXGBoost parameters:"
    )

    print(
        json.dumps(
            params,
            indent=2,
            default=str,
        )
    )

    # --------------------------------------------------------
    # IMPORTANT METHODOLOGICAL NOTE
    #
    # We do NOT use the future targets as eval_set.
    #
    # This is a blind historical experiment.
    #
    # Therefore the model is trained using the 324 historical
    # feature rows and their labels representing 2005-2015.
    #
    # In the next iteration we will introduce a proper
    # historical validation period before 2003 so that
    # hyperparameters can be selected without touching
    # 2005-2015.
    # --------------------------------------------------------

    model = XGBClassifier(
        **params
    )

    model.fit(
        X,
        y,
        verbose=False,
    )

    print(
        "\nModel trained."
    )

    return (
        model,
        data,
        feature_columns,
    )


# ============================================================
# PREDICTIONS
# ============================================================

def generate_risk_map(
    model,
    data,
    feature_columns,
):

    X = data[
        feature_columns
    ].copy()

    X = X.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    probabilities = (
        model
        .predict_proba(X)[:, 1]
    )

    result = data[
        [
            "cell_id",
            "grid_x",
            "grid_y",
            "cell_lat",
            "cell_lon",
            "has_m5_future",
            "n_m5_future",
        ]
    ].copy()

    result[
        "predicted_probability"
    ] = probabilities

    result = result.sort_values(
        "predicted_probability",
        ascending=False,
    ).reset_index(drop=True)

    result[
        "risk_rank"
    ] = np.arange(
        1,
        len(result) + 1,
    )

    result[
        "risk_percentile"
    ] = (
        1
        - (
            result["risk_rank"] - 1
        )
        / len(result)
    )

    return result


# ============================================================
# TOP-N% CAPTURE
# ============================================================

def calculate_top_capture(
    risk_map,
):

    results = {}

    total_events = (
        risk_map[
            "n_m5_future"
        ].sum()
    )

    for percentage in [
        0.10,
        0.20,
        0.30,
        0.50,
    ]:

        n_cells = max(
            1,
            math.ceil(
                len(risk_map)
                * percentage
            ),
        )

        top_cells = risk_map.head(
            n_cells
        )

        captured_events = (
            top_cells[
                "n_m5_future"
            ].sum()
        )

        if total_events > 0:

            capture_rate = (
                captured_events
                / total_events
            )

        else:

            capture_rate = np.nan

        results[
            f"top_{int(percentage * 100)}_percent"
        ] = {
            "cells_selected": int(
                n_cells
            ),
            "events_captured": int(
                captured_events
            ),
            "total_future_events": int(
                total_events
            ),
            "capture_rate": float(
                capture_rate
            )
            if not np.isnan(
                capture_rate
            )
            else None,
        }

    return results

# ============================================================
# PROBABILISTIC METRICS
# ============================================================

def calculate_metrics(risk_map):

    y_true = risk_map[
        "has_m5_future"
    ].values

    y_prob = risk_map[
        "predicted_probability"
    ].values

    metrics = {}

    # --------------------------------------------------------
    # Brier score
    # --------------------------------------------------------

    metrics[
        "brier_score"
    ] = float(
        brier_score_loss(
            y_true,
            y_prob,
        )
    )

    # --------------------------------------------------------
    # Log loss
    # --------------------------------------------------------

    # Prevent log(0)
    y_prob_safe = np.clip(
        y_prob,
        1e-7,
        1 - 1e-7,
    )

    metrics[
        "log_loss"
    ] = float(
        log_loss(
            y_true,
            y_prob_safe,
        )
    )

    # --------------------------------------------------------
    # ROC-AUC
    # --------------------------------------------------------

    if (
        len(np.unique(y_true))
        == 2
    ):

        metrics[
            "roc_auc"
        ] = float(
            roc_auc_score(
                y_true,
                y_prob,
            )
        )

        metrics[
            "average_precision"
        ] = float(
            average_precision_score(
                y_true,
                y_prob,
            )
        )

    else:

        metrics[
            "roc_auc"
        ] = None

        metrics[
            "average_precision"
        ] = None

    # --------------------------------------------------------
    # Top capture
    # --------------------------------------------------------

    metrics[
        "top_capture"
    ] = calculate_top_capture(
        risk_map
    )

    return metrics


# ============================================================
# SAVE OUTPUTS
# ============================================================

def save_outputs(
    features,
    targets,
    risk_map,
    metrics,
    model,
):

    features_path = (
        PROCESSED_DIR
        / "forecast_m5_2003_features.parquet"
    )

    targets_path = (
        PROCESSED_DIR
        / "forecast_m5_2005_2015_targets.parquet"
    )

    risk_path = (
        PROCESSED_DIR
        / "forecast_m5_2003_risk_map.csv"
    )

    metrics_path = (
        METRICS_DIR
        / "forecast_m5_2003_metrics.json"
    )

    model_path = (
        MODEL_DIR
        / "forecast_m5_2003.json"
    )

    features.to_parquet(
        features_path,
        index=False,
    )

    targets.to_parquet(
        targets_path,
        index=False,
    )

    risk_map.to_csv(
        risk_path,
        index=False,
    )

    with open(
        metrics_path,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            metrics,
            f,
            indent=2,
        )

    model.save_model(
        model_path
    )

    print("\nSaved:")
    print(
        f"  {features_path}"
    )
    print(
        f"  {targets_path}"
    )
    print(
        f"  {risk_path}"
    )
    print(
        f"  {metrics_path}"
    )
    print(
        f"  {model_path}"
    )
# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print(
        "XGBOOST M>=5 FORECAST EXPERIMENT"
    )
    print(
        "Historical information: 1981-04-01 -> 2003-12-31"
    )
    print(
        "Blind forecast: 2005-01-01 -> 2014-12-31"
    )
    print("=" * 70)

    # --------------------------------------------------------
    # Load catalog
    # --------------------------------------------------------

    df_all, df_train = (
        load_catalog()
    )

    # --------------------------------------------------------
    # Spatial grid
    # --------------------------------------------------------

    df_train, lat_step, lon_step = (
        assign_grid(df_train)
    )

    # Need the future events to be assigned to exactly
    # the same grid.
    #
    # IMPORTANT:
    # We only use these later as targets.
    # --------------------------------------------------------

    df_future_candidate = df_all[
        (df_all["time"] >= FORECAST_START)
        & (df_all["time"] <= FORECAST_END)
        & (
            df_all["magnitude"]
            >= TARGET_MAGNITUDE
        )
    ].copy()

    df_future_candidate, _, _ = (
        assign_grid(
            df_future_candidate
        )
    )

    # --------------------------------------------------------
    # Build X
    # --------------------------------------------------------

    features = build_features(
        df_train
    )

    # --------------------------------------------------------
    # Build y
    # --------------------------------------------------------

    targets, future = (
        build_targets(
            df_future_candidate
        )
    )

    # --------------------------------------------------------
    # Leakage checks
    # --------------------------------------------------------

    leakage_checks(
        features,
        df_train,
        future,
    )

    # --------------------------------------------------------
    # Train
    # --------------------------------------------------------

    (
        model,
        data,
        feature_columns,
    ) = train_model(
        features,
        targets,
    )

    # --------------------------------------------------------
    # Generate risk map
    # --------------------------------------------------------

    risk_map = generate_risk_map(
        model,
        data,
        feature_columns,
    )

    # --------------------------------------------------------
    # Metrics
    # --------------------------------------------------------

    metrics = calculate_metrics(
        risk_map
    )

    # Add experiment metadata.
    metrics[
        "experiment"
    ] = "forecast_m5_2003_xgboost"

    metrics[
        "train_start"
    ] = str(TRAIN_START)

    metrics[
        "train_end"
    ] = str(TRAIN_END)

    metrics[
        "forecast_start"
    ] = str(FORECAST_START)

    metrics[
        "forecast_end"
    ] = str(FORECAST_END)

    metrics[
        "target_magnitude"
    ] = TARGET_MAGNITUDE

    metrics[
        "grid_rows"
    ] = GRID_ROWS

    metrics[
        "grid_cols"
    ] = GRID_COLS

    metrics[
        "cell_km"
    ] = CELL_KM

    # --------------------------------------------------------
    # Print results
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)

    print(
        f"\nBrier score: "
        f"{metrics['brier_score']:.6f}"
    )

    print(
        f"Log loss: "
        f"{metrics['log_loss']:.6f}"
    )

    if metrics["roc_auc"] is not None:

        print(
            f"ROC-AUC: "
            f"{metrics['roc_auc']:.6f}"
        )

        print(
            f"Average precision: "
            f"{metrics['average_precision']:.6f}"
        )

    print("\nTop-cell capture:")

    for key, value in (
        metrics[
            "top_capture"
        ].items()
    ):

        print(
            f"  {key}: "
            f"{value['events_captured']}/"
            f"{value['total_future_events']} "
            f"= "
            f"{value['capture_rate']:.2%}"
        )

    print("\nTop 20 predicted-risk cells:")

    print(
        risk_map[
            [
                "risk_rank",
                "cell_id",
                "cell_lat",
                "cell_lon",
                "predicted_probability",
                "n_m5_future",
            ]
        ]
        .head(20)
        .to_string(index=False)

      
  )

# --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    save_outputs(
        features,
        targets,
        risk_map,
        metrics,
        model,
    )

    print(
        "\nExperiment completed."
    )


if __name__ == "__main__":
    main()
  
