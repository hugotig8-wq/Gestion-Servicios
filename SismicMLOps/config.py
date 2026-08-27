"""Configuration module for the seismic MLOps pipeline."""

from pathlib import Path
import pandas as pd

# ============================================================
# PROJECT ROOT & PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent

DATA_PATH = PROJECT_ROOT / "data" / "raw" / "earthquakes.csv"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
METRICS_DIR = PROJECT_ROOT / "metrics"
MODEL_DIR = PROJECT_ROOT / "training" / "models"

# ============================================================
# TEMPORAL BOUNDARIES
# ============================================================

TRAIN_START = pd.Timestamp("1981-04-01", tz="UTC")
TRAIN_END = pd.Timestamp("2003-12-31 23:59:59", tz="UTC")
FORECAST_START = pd.Timestamp("2005-01-01", tz="UTC")
FORECAST_END = pd.Timestamp("2014-12-31 23:59:59", tz="UTC")

# ============================================================
# EARTHQUAKE THRESHOLDS & SPATIAL GRID
# ============================================================

TARGET_MAGNITUDE = 5.0
MIN_MAGNITUDE_FEATURE = 1.4

GRID_ROWS = 18
GRID_COLS = 18
CELL_KM = 10.0
GRID_MIN_LAT = 32.8
GRID_MIN_LON = -118.5

# ============================================================
# XGBOOST CONFIGURATION
# ============================================================

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
