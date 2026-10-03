"""forecast_m5_2003.py - Pipeline de Entrenamiento, Calibración y Evaluación."""

import json
import logging
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, brier_score_loss

import config
from models import train_and_calibrate_model
from features import (
    assign_grid_indices,
    build_grid_features,
    add_cfm_features,
    grid_to_latlon,
    create_temporal_split_datasets
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def run_forecast_pipeline():
    # 1. Cargar catálogo raw
    logging.info("Cargando catálogo sismológico...")
    df_raw = pd.read_csv(config.DATA_PATH)
    
    # 2. Mapear celdas (grid_i, grid_j)
    df_mapped = assign_grid_indices(df_raw)
    """
    ##ESTO GENERABA LEAKAGE.
    # 3. Construir dataset agrupado por celda (genera 'target')
    logging.info("Construyendo features de la malla espacial...")
    df_grid = build_grid_features(df_mapped)
    
    # 4. Unir modelo de fallas CFM con todas sus características
    if config.USE_SCEC_CFM:
        logging.info("Enriqueciendo dataset con características geológicas de SCEC CFM...")
        df_grid = add_cfm_features(df_grid, config.CFM_DATA_PATH)

    # 5. Separación de matriz de características (X) y objetivo (y)
    target_col = "target"
    if target_col not in df_grid.columns:
        raise KeyError(f"La columna '{target_col}' no existe en el DataFrame.")

    # Excluir identificadores de la malla, variables objetivo y textos no numéricos
    drop_cols = ["target", "grid_i", "grid_j", "max_magnitude", "nearest_fault_name"]
    
    X = df_grid.drop(columns=[c for c in drop_cols if c in df_grid.columns])
    y = df_grid[target_col]

    logging.info(f"Matriz de entrenamiento X: {X.shape[1]} características incluidas.")

    # Split Estratificado (Train, Validation, Test)
    X_train_full, X_test, y_train_full, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_full, y_train_full, test_size=0.25, random_state=42, stratify=y_train_full
    )

    logging.info(f"Dataset Split completado: Train={X_train.shape[0]}, Val={X_val.shape[0]}, Test={X_test.shape[0]}")
    """

    # 3. Construcción de datasets de Train y Test con validación temporal estricta
    logging.info("Construyendo features temporales y asignando targets con MultiIndex.isin...")
    df_train_grid, df_test_grid = create_temporal_split_datasets(
        df_mapped, 
        train_cutoff_year=2003, 
        val_cutoff_year=2013, 
        target_mag=config.TARGET_MAGNITUDE
    )

    # 4. Unir modelo de fallas CFM a ambos conjuntos
    if config.USE_SCEC_CFM:
        logging.info("Enriqueciendo datasets con características geológicas de SCEC CFM...")
        df_train_grid = add_cfm_features(df_train_grid, config.CFM_DATA_PATH)
        df_test_grid = add_cfm_features(df_test_grid, config.CFM_DATA_PATH)

    # 5. Separación de matrices X e y
    drop_cols = ["target", "grid_i", "grid_j", "max_past_magnitude", "nearest_fault_name"]
    
    X_train_full = df_train_grid.drop(columns=[c for c in drop_cols if c in df_train_grid.columns])
    y_train_full = df_train_grid["target"]

    X_test = df_test_grid.drop(columns=[c for c in drop_cols if c in df_test_grid.columns])
    y_test = df_test_grid["target"]

    # Sub-split de Train/Validation dentro del periodo de entrenamiento para la calibración
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_full, y_train_full, test_size=0.25, random_state=42, stratify=y_train_full
    )

    logging.info(f"Dataset Split completado: Train={X_train.shape[0]}, Val={X_val.shape[0]}, Test={X_test.shape[0]}")
    
    # 6. Entrenamiento de XGBoost y Calibración
    logging.info("Entrenando modelo XGBoost y aplicando calibración isotónica...")
    calibrated_model = train_and_calibrate_model(
        X_train=X_train,
        y_train=y_train,
        X_val=X_val,
        y_val=y_val,
        scale_pos_weight=config.SCALE_POS_WEIGHT
    )

    # 7. Evaluación en conjunto de Test
    logging.info("Evaluando el modelo calibrado sobre el conjunto de test...")
    y_probs = calibrated_model.predict_proba(X_test)[:, 1]

    auc_score = roc_auc_score(y_test, y_probs)
    brier_score = brier_score_loss(y_test, y_probs)
    max_prob = float(y_probs.max())

    logging.info(f"Test ROC-AUC: {auc_score:.4f}")
    logging.info(f"Test Brier Score: {brier_score:.4f}")
    logging.info(f"Máxima Probabilidad Calibrada: {max_prob:.4f}")

    # 8. Generar y Exportar Mapa de Riesgo
    X_test_map = X_test.copy()
    X_test_map["grid_i"] = df_test_grid.loc[X_test.index, "grid_i"]
    X_test_map["grid_j"] = df_test_grid.loc[X_test.index, "grid_j"]
    X_test_map["risk_probability"] = y_probs

    # Recuperar coordenadas geográficas y enlace a Google Maps
    X_test_map = grid_to_latlon(X_test_map)

    # Reordenar columnas prioritarias al frente
    cols_order = ["google_maps_url", "latitude", "longitude", "risk_probability", "seismic_rate"] + [
        c for c in X_test_map.columns if c not in ["google_maps_url", "latitude", "longitude", "risk_probability", "seismic_rate"]
    ]
    X_test_map = X_test_map[cols_order]

    X_test_map.to_csv(config.RISK_MAP_SAVE_PATH, index=False)
    logging.info(f"Mapa de riesgo calibrado guardado en {config.RISK_MAP_SAVE_PATH}")

    # Guardar reporte de métricas
    metrics_payload = {
        "model_type": config.MODEL_TYPE,
        "calibration_method": config.CALIBRATION_METHOD,
        "use_cfm": config.USE_SCEC_CFM,
        "roc_auc": round(auc_score, 4),
        "brier_score": round(brier_score, 4),
        "max_calibrated_probability": round(max_prob, 4),
        "n_features": X_test.shape[1]
    }

    with open(config.METRICS_SAVE_PATH, "w") as f:
        json.dump(metrics_payload, f, indent=4)

    logging.info(f"Métricas del modelo exportadas a {config.METRICS_SAVE_PATH}")


if __name__ == "__main__":
    run_forecast_pipeline()
 
