# config.py
from pathlib import Path

# config.py

# --- SCEC INTEGRATION FLAGS ---
USE_SCEC_CTM = True
USE_SCEC_CFM = True  # Activador de SCEC CVM

# Rutas de datos SCEC
CTM_DATA_PATH = "data/raw/scec_ctm_data.csv"
CFM_DATA_PATH = "data/raw/scec_cfm_data.csv"


# --- SCEC INTEGRATION FLAGS ---
USE_SCEC_CTM = True
USE_SCEC_NEW_MODEL = True  # Activador del nuevo modelo

# Rutas a los datos
CTM_DATA_PATH = "data/raw/scec_ctm_data.csv"
NEW_SCEC_MODEL_PATH = "data/raw/scec_new_model_data.csv"


# ============================================================
# 1. PROJECT ROOT & PATHS (Rutas Dinámicas Robusta)
# ============================================================
PROJECT_ROOT = Path(__file__).resolve().parent

DATA_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PATH = DATA_DIR / "earthquakes.csv"
ROCK_DATA_PATH = DATA_DIR / "rock_properties.parquet"

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
METRICS_DIR = PROJECT_ROOT / "metrics"
MODEL_DIR = PROJECT_ROOT / "training" / "models"

# Crear directorios si no existen
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
# 3. PARÁMETROS DE CATÁLOGO Y SISMOLOGÍA
# ============================================================
MIN_MAGNITUDE = 1.4     # Mmin para cálculo de b-value
TARGET_MAGNITUDE = 5.0  # Magnitud objetivo (M >= 5.0)

# ============================================================
# 4. VENTANAS TEMPORALES
# ============================================================
TRAIN_START = "1981-01-01"
TRAIN_END = "2003-12-31"

TEST_START = "2005-01-01"
TEST_END = "2014-12-31"

PREDICTION_HORIZON_YEARS = 10

# ============================================================
# 5. SELECCIÓN DE MODELO E HIPERPARÁMETROS
# ============================================================
# Opciones disponibles: "xgboost", "lightgbm", "random_forest"
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
    },
    "lightgbm": {
        "n_estimators": 100,
        "max_depth": 4,
        "learning_rate": 0.05,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "random_state": 42,
        "n_jobs": -1,
        "verbose": -1
    },
    "random_forest": {
        "n_estimators": 100,
        "max_depth": 6,
        "random_state": 42,
        "n_jobs": -1
    }
}

SCALE_POS_WEIGHT = 10.0
CALIBRATION_METHOD = "isotonic"  # 'isotonic' o 'sigmoid'

# ============================================================
# 6. CONFIGURACIÓN DE MODELOS COMUNITARIOS SCEC
# ============================================================
SCEC_DIR = DATA_DIR / "scec"

# Rutas de los datasets SCEC
#CTM_DATA_PATH = SCEC_DIR / "ctm_processed.parquet"
CFM_DATA_PATH = SCEC_DIR / "cfm_processed.parquet"
CGM_DATA_PATH = SCEC_DIR / "cgm_processed.parquet"
CRM_DATA_PATH = SCEC_DIR / "crm_processed.parquet"
CSM_DATA_PATH = SCEC_DIR / "csm_processed.parquet"

# Switches para experimentos (Permite activar/desactivar en pruebas)
USE_SCEC_CTM = True
USE_SCEC_CFM = False  # Activaremos en el siguiente paso
USE_SCEC_CGM = False  # Activaremos en el siguiente paso
USE_SCEC_CRM = False  # Activaremos en el siguiente paso
USE_SCEC_CSM = False  # Activaremos en el siguiente paso

