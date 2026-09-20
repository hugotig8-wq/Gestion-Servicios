# config.py
from pathlib import Path

# ============================================================
# 1. RUTAS DEL PROYECTO
# ============================================================
PROJECT_ROOT = Path(__file__).resolve().parent

DATA_DIR = PROJECT_ROOT / "data" 
DATA_PATH = DATA_DIR / "raw" / "earthquakes.csv"

# Dataset de CFM generado con distancias 3D y metadata geológica
CFM_DATA_PATH = DATA_DIR / "processed" / "cfm" / "xgboost_earthquakes_cfm_dataset.parquet"
CVM_DATA_PATH = DATA_DIR / "raw" / "scec_cvm_data.csv"
CTM_DATA_PATH = DATA_DIR / "raw" / "scec_ctm_data.csv"

PROCESSED_DIR = PROJECT_ROOT / "processed"
METRICS_DIR = PROJECT_ROOT / "metrics"
MODEL_DIR = PROJECT_ROOT / "training" / "models"

for directory in [PROCESSED_DIR, METRICS_DIR, MODEL_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

RISK_MAP_SAVE_PATH = PROCESSED_DIR / "risk_map_calibrated.csv"
METRICS_SAVE_PATH = METRICS_DIR / "forecast_metrics.json"

# ============================================================
# 2. PARÁMETROS GEOGRÁFICOS Y DE LA MALLA
# ============================================================
LAT_MIN = 32.0
LAT_MAX = 36.0
LON_MIN = -120.0
LON_MAX = -115.0

GRID_ROWS = 18
GRID_COLS = 18
CELL_KM = 10.0

# ============================================================
# 3. PARÁMETROS SISMOLÓGICOS Y MODELADO
# ============================================================
MIN_MAGNITUDE = 1.4     # Mmin para b-value
TARGET_MAGNITUDE = 5.0  # Magnitud objetivo (M >= 5.0)

MODEL_TYPE = "xgboost"

MODEL_CONFIGS = {
    "xgboost": {
        "n_estimators": 100,
        "max_depth": 4,
        "learning_rate": 0.05,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "random_state": 42,
        "n_jobs": -1
    }
}

SCALE_POS_WEIGHT = 10.0
CALIBRATION_METHOD = "isotonic"

# ============================================================
# 4. SWITCHES DE MODELOS SCEC
# ============================================================
USE_SCEC_CFM = True
USE_SCEC_CTM = False
USE_SCEC_CVM = False
