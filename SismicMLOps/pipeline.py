import json
from SismicMLOps.config import PROCESSED_DIR, METRICS_DIR, MODEL_DIR
from SismicMLOps.data_loader import load_catalog
from Sismic_MLOps.features import assign_grid, build_backtesting_dataset
from SismicMLOps.models import train_model, generate_risk_map
from SismicMLOps.evaluation import calculate_metrics


def run_pipeline():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Cargar datos
    df_all, _ = load_catalog()

    # 2. Asignar Grid
    df_all, _, _ = assign_grid(df_all)

    # 3. Construir Dataset Backtesting
    backtest = build_backtesting_dataset(df_all)
    backtest_path = PROCESSED_DIR / "backtesting_dataset.parquet"
    backtest.to_parquet(backtest_path, index=False)
    print(f"Dataset de backtesting guardado en: {backtest_path}")

    # 4. Entrenar Modelo
    model, feature_cols = train_model(backtest)

    # 5. Generar Mapa de Riesgo
    risk_map = generate_risk_map(model, backtest, feature_cols)
    risk_path = PROCESSED_DIR / "risk_map.csv"
    risk_map.to_csv(risk_path, index=False)

    # 6. Evaluar
    metrics = calculate_metrics(risk_map)
    metrics_path = METRICS_DIR / "metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    # 7. Guardar Modelo
    model_path = MODEL_DIR / "xgboost_model.json"
    model.save_model(model_path)

    print("\n¡Pipeline ejecutado con éxito!")


if __name__ == "__main__":
    run_pipeline()
  
