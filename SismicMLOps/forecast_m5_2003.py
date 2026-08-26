"""
Forecast M>=5 earthquakes, 2005-2015, using information available
up to 2003-12-31.
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

from config import (
    DATA_PATH,
    PROCESSED_DIR,
    METRICS_DIR,
    MODEL_DIR,

    TRAIN_START,
    TRAIN_END,
    FORECAST_START,
    FORECAST_END,

    TARGET_MAGNITUDE,
    MIN_MAGNITUDE_FEATURE,

    GRID_ROWS,
    GRID_COLS,
    CELL_KM,
    GRID_MIN_LAT,
    GRID_MIN_LON,

    RANDOM_STATE,
    MODEL_PARAMS,
)
