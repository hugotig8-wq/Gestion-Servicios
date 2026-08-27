"""Machine learning model training and inference module."""

from typing import Tuple
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sismic_MLOps.config import MODEL_PARAMS


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

    params = MODEL_PARAMS.copy()
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
    
