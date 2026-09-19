# forecast_m5_2003.py
import json
import logging
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, brier_score_loss

import config
from features import add_ctm_features, assign_grid_indices, add_ctm_features  # O el pipeline de extracción completo
from models import train_and_calibrate_model


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def run_forecast_pipeline():
    logging.info("Starting Earthquake Forecasting Pipeline...")
    logging.info(f"Selected Model Type: {config.MODEL_TYPE}")

    # 1. Cargar conjunto de datos procesado
    if not config.DATA_PATH.exists():
        raise FileNotFoundError(f"Raw catalog not found at: {config.DATA_PATH}")

    logging.info(f"Loading raw earthquake data from {config.DATA_PATH}")
    df_raw = pd.read_csv(config.DATA_PATH)

    df_features = assign_grid_indices(df_raw)  # <── AQUÍ SE CREAN 'grid_i' Y 'grid_j'

    # 2. Construcción/Enriquecimiento de Características
    logging.info("Building base features and integrating SCEC CTM features...")
    # Supongamos que df_features es tu dataframe con grid_i, grid_j, b-value, etc.
    df_features = df_raw.copy() 

    if config.USE_SCEC_CTM:
        df_features = add_ctm_features(df_features, config.CTM_DATA_PATH)
        logging.info("SCEC CTM features successfully merged.")

    # 3. Separación de Variables X e y
    target_col = "target"  # Sismo M >= 5.0 (1 o 0)
    drop_cols = ["target", "time", "latitude", "longitude"] if "time" in df_features.columns else ["target"]
    
    X = df_features.drop(columns=[c for c in drop_cols if c in df_features.columns])
    y = df_features[target_col]

    # 4. Split de Entrenamiento, Validación (para calibración) y Test
    # Importante: Mantener división temporal o de validación limpia
    X_train_full, X_test, y_train_full, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_full, y_train_full, test_size=0.25, random_state=42, stratify=y_train_full
    )

    logging.info(f"Dataset split: Train={X_train.shape[0]}, Val={X_val.shape[0]}, Test={X_test.shape[0]}")

    # 5. Entrenamiento y Calibración Isotónica (usando get_base_model internamente)
    logging.info("Training base model and fitting Isotonic Calibration...")
    calibrated_model = train_and_calibrate_model(
        X_train=X_train,
        y_train=y_train,
        X_val=X_val,
        y_val=y_val,
        scale_pos_weight=config.SCALE_POS_WEIGHT
    )

    # 6. Evaluación en el Conjunto de Test
    logging.info("Evaluating calibrated model on test set...")
    y_probs = calibrated_model.predict_proba(X_test)[:, 1]

    auc_score = roc_auc_score(y_test, y_probs)
    brier_score = brier_score_loss(y_test, y_probs)
    max_prob = float(y_probs.max())

    logging.info(f"Test ROC-AUC: {auc_score:.4f}")
    logging.info(f"Test Brier Score: {brier_score:.4f}")
    logging.info(f"Max Calibrated Probability: {max_prob:.4f}")

    # 7. Guardar Mapa de Riesgo y Métricas usando config.py
    metrics_payload = {
        "model_type": config.MODEL_TYPE,
        "calibration_method": config.CALIBRATION_METHOD,
        "use_ctm": config.USE_SCEC_CTM,
        "roc_auc": round(auc_score, 4),
        "brier_score": round(brier_score, 4),
        "max_calibrated_probability": round(max_prob, 4),
        "n_features": X.shape[1]
    }

    with open(config.METRICS_SAVE_PATH, "w") as f:
        json.dump(metrics_payload, f, indent=4)

    logging.info(f"Metrics saved to {config.METRICS_SAVE_PATH}")
    
    # Exportar predicciones/mapa de riesgo
    X_test_map = X_test.copy()
    X_test_map["risk_probability"] = y_probs
    X_test_map.to_csv(config.RISK_MAP_SAVE_PATH, index=False)
    logging.info(f"Calibrated risk map saved to {config.RISK_MAP_SAVE_PATH}")

if __name__ == "__main__":
    run_forecast_pipeline()
    
