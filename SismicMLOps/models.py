"""Machine learning model training and inference module."""

from typing import Tuple
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
#from config import MODEL_PARAMS

import joblib
import config
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier



def train_model(data: pd.DataFrame) -> Tuple[XGBClassifier, list[str]]:
    """Train XGBoost spatial risk model on prepared feature set."""
    print("\nTraining XGBoost Classifier...")

    excluded = {
        "forecast_date",
        "cell_id",
        "cell_lat",
        "cell_lon",
        "grid_x",
        "grid_y",
        "has_m5_future",
        "n_m5_future",
        "max_m5_future",
    }
    feature_columns = [col for col in data.columns if col not in excluded]

    X = data[feature_columns].replace([np.inf, -np.inf], np.nan)
    y = data["has_m5_future"].astype(int)

    positive = int(y.sum())
    negative = int(len(y) - positive)

    if positive == 0:
        raise RuntimeError(
            "Training error: Zero positive instances found in target."
        )

    params = config.MODEL_PARAMS.copy()
    params["scale_pos_weight"] = negative / positive

    model = XGBClassifier(**params)
    model.fit(X, y, verbose=False)

    return model, feature_columns


def generate_risk_map(
    model: XGBClassifier, data: pd.DataFrame, feature_columns: list[str]
) -> pd.DataFrame:
    """Predict spatial earthquake probabilities and output risk rankings."""
    X = data[feature_columns].replace([np.inf, -np.inf], np.nan)
    probabilities = model.predict_proba(X)[:, 1]

    cols = [
        "cell_id",
        "grid_x",
        "grid_y",
        "cell_lat",
        "cell_lon",
        "has_m5_future",
        "n_m5_future",
    ]
    if "forecast_date" in data.columns:
        cols.insert(0, "forecast_date")

    result = data[cols].copy()
    result["predicted_probability"] = probabilities
    result = result.sort_values(
        "predicted_probability", ascending=False
    ).reset_index(drop=True)

    result["risk_rank"] = np.arange(1, len(result) + 1)
    result["risk_percentile"] = 1 - ((result["risk_rank"] - 1) / len(result))

    return result


# models.py

def get_base_model(model_type: str = config.MODEL_TYPE, scale_pos_weight: float = config.SCALE_POS_WEIGHT):
    """Instancia el modelo según la configuración de config.py"""
    params = config.MODEL_CONFIGS.get(model_type, {}).copy()
    
    if model_type == "xgboost":
        from xgboost import XGBClassifier
        return XGBClassifier(**params, scale_pos_weight=scale_pos_weight)
        
    elif model_type == "lightgbm":
        from lightgbm import LGBMClassifier
        return LGBMClassifier(**params, scale_pos_weight=scale_pos_weight)
        
    elif model_type == "random_forest":
        return RandomForestClassifier(**params, class_weight="balanced")
        
    else:
        raise ValueError(f"Modelo '{model_type}' no soportado.")

def train_and_calibrate_model(X_train, y_train, X_val, y_val, scale_pos_weight: float = config.SCALE_POS_WEIGHT):
    
    base_model = get_base_model(config.MODEL_TYPE, scale_pos_weight=scale_pos_weight)
    base_model.fit(X_train, y_train)
    
    calibrated_model = CalibratedClassifierCV(
        estimator=base_model,
        method=config.CALIBRATION_METHOD,
        cv="prefitted"
    )
    calibrated_model.fit(X_val, y_val)
    
    # Guardar modelo entrenado automáticamente usando config.MODEL_DIR
    model_path = config.MODEL_DIR / f"calibrated_{config.MODEL_TYPE}_model.joblib"
    joblib.dump(calibrated_model, model_path)
    
    return calibrated_model
    
    
