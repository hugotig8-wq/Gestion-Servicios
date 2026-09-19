# forecast_m5_2003.py
import json
import logging
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, brier_score_loss

import config
 # O el pipeline de extracción completo
from models import train_and_calibrate_model
#from features import assign_grid_indices, add_ctm_features, create_target_label, grid_to_latlon

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# forecast_m5_2003.py
import pandas as pd
import config
#from features import assign_grid_indices, build_grid_features, add_ctm_features

from features import (
    assign_grid_indices,
    build_grid_features,
    add_ctm_features,
    add_cvm_features,
    grid_to_latlon
)

def run_forecast_pipeline():
    # 1. Cargar catálogo raw
    df_raw = pd.read_csv(config.DATA_PATH)
    
    # 2. Mapear celdas (grid_i, grid_j)
    df_mapped = assign_grid_indices(df_raw)
    
    # 3. Construir dataset agrupado por celda (AQUÍ SE GENERA 'target')
    df_grid = build_grid_features(df_mapped)
    
    # 4. Unir modelo térmico CTM
    if config.USE_SCEC_CTM:
        df_grid = add_ctm_features(df_grid, config.CTM_DATA_PATH)

    if getattr(config, "USE_SCEC_CFM", False):
        df_grid = add_cfm_features(df_grid, config.NEW_SCEC_MODEL_PATH)
     
 
    # 5. Separar X e y (Línea 106 protegida)
    target_col = "target"
    if target_col not in df_grid.columns:
        raise KeyError(f"La columna '{target_col}' no existe en el DataFrame. Columnas disponibles: {list(df_grid.columns)}")

    # Eliminar la magnitud máxima del conjunto de entrenamiento
    drop_cols = ["target", "grid_i", "grid_j", "max_magnitude"]
    X = df_grid.drop(columns=[c for c in drop_cols if c in df_grid.columns])

    #drop_cols = ["target", "grid_i", "grid_j"]
    
    #X = df_grid.drop(columns=[c for c in drop_cols if c in df_grid.columns])
    y = df_grid[target_col]

    # Continuar con la división train/val/test y entrenamiento con XGBoost/Calibración...

    # Split de Entrenamiento, Validación (para calibración) y Test
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

 

# ... después de calcular y_probs ...

    # Guardar mapa de riesgo con coordenadas y enlace a Google Maps
    X_test_map = X_test.copy()
    X_test_map["grid_i"] = df_grid.loc[X_test.index, "grid_i"]
    X_test_map["grid_j"] = df_grid.loc[X_test.index, "grid_j"]
    X_test_map["risk_probability"] = y_probs

# Recuperar coordenadas geográficas
    X_test_map = grid_to_latlon(X_test_map)

# Ordenar colocando el enlace al principio para fácil lectura en el móvil
    cols_order = ["google_maps_url", "latitude", "longitude", "risk_probability", "seismic_rate"] + [
        c for c in X_test_map.columns if c not in ["google_maps_url", "latitude", "longitude", "risk_probability", "seismic_rate"]
    ]
    X_test_map = X_test_map[cols_order]

    X_test_map.to_csv(config.RISK_MAP_SAVE_PATH, index=False)

    '''
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
    '''
if __name__ == "__main__":
    run_forecast_pipeline()
    
