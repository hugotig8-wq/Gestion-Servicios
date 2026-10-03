# config.py
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

DATA_DIR = PROJECT_ROOT / "data" 
DATA_PATH = DATA_DIR / "raw" / "earthquakes.csv"

CFM_DATA_PATH = DATA_DIR / "processed" / "cfm" / "xgboost_earthquakes_cfm_dataset.parquet"

PROCESSED_DIR = PROJECT_ROOT / "processed"
METRICS_DIR = PROJECT_ROOT / "metrics"
MODEL_DIR = PROJECT_ROOT / "training" / "models"

for directory in [PROCESSED_DIR, METRICS_DIR, MODEL_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

RISK_MAP_SAVE_PATH = PROCESSED_DIR / "risk_map_calibrated.csv"
METRICS_SAVE_PATH = METRICS_DIR / "forecast_metrics.json"

# PARÁMETROS GEOGRÁFICOS
LAT_MIN = 32.0
LAT_MAX = 36.0
LON_MIN = -120.0
LON_MAX = -115.0

GRID_ROWS = 18
GRID_COLS = 18
CELL_KM = 10.0

# PARÁMETROS SISMOLÓGICOS Y MODELADO
MIN_MAGNITUDE = 1.4     # Mmin para b-value
TARGET_MAGNITUDE = 4.5  # Ajustado a 4.5 para contar con suficientes muestras de test

MODEL_TYPE = "xgboost"

MODEL_CONFIGS = {
    "xgboost": {
        "n_estimators": 120,
        "max_depth": 3,
        "learning_rate": 0.02,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "random_state": 42,
        "n_jobs": -1
    }
}

SCALE_POS_WEIGHT = 8.0
CALIBRATION_METHOD = "sigmoid"

USE_SCEC_CFM = True
