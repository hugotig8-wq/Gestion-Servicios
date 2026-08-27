"""Main orchestration script for M>=5 Earthquake Forecast pipeline."""

import json
from config import (
    FORECAST_END,
    FORECAST_START,
    GRID_COLS,
    GRID_ROWS,
    METRICS_DIR,
    MODEL_DIR,
    PROCESSED_DIR,
    TARGET_MAGNITUDE,
    TRAIN_END,
    TRAIN_START,
)
from data_loader import load_catalog
from evaluation import calculate_metrics
from features import assign_grid, build_backtesting_dataset
from models import generate_risk_map, train_model


def run_experiment():
    print("=" * 70)
    print("M>=5 EARTHQUAKE FORECAST PIPELINE (TODA EXPERIMENT)")
    print("=" * 70)

    # Make output directories if non-existent
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load Data
    df_all, _ = load_catalog()

    # 2. Assign Grid Geometry
    df_all, _, _ = assign_grid(df_all)

    # 3. Build Backtesting Features & Targets
    backtest = build_backtesting_dataset(df_all)
    backtest_path = PROCESSED_DIR / "backtesting_dataset.parquet"
    backtest.to_parquet(backtest_path, index=False)

    # 4. Model Training
    model, feature_cols = train_model(backtest)

    # 5. Risk Map Prediction
    risk_map = generate_risk_map(model, backtest, feature_cols)
    risk_path = PROCESSED_DIR / "forecast_m5_2003_risk_map.csv"
    risk_map.to_csv(risk_path, index=False)

    # 6. Evaluation
    metrics = calculate_metrics(risk_map)
    metrics["experiment"] = "forecast_m5_2003_xgboost"
    metrics["train_start"] = str(TRAIN_START)
    metrics["train_end"] = str(TRAIN_END)

    metrics_path = METRICS_DIR / "forecast_m5_2003_metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    # 7. Model Artifact Export
    model_path = MODEL_DIR / "forecast_m5_2003.json"
    model.save_model(model_path)

    print("\n" + "=" * 70)
    print("PIPELINE COMPLETED SUCCESSFULLY")
    print(f"Risk Map Saved: {risk_path}")
    print(f"Metrics Saved:  {metrics_path}")
    print(f"Model Artifact: {model_path}")
    print("=" * 70)


if __name__ == "__main__":
    run_experiment()
    
