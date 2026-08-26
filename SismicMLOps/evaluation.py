import math
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss, log_loss


def calculate_top_capture(risk_map: pd.DataFrame) -> dict:
    results = {}
    total_events = risk_map["n_m5_future"].sum()

    for percentage in [0.10, 0.20, 0.30, 0.50]:
        n_cells = max(1, math.ceil(len(risk_map) * percentage))
        top_cells = risk_map.head(n_cells)
        captured_events = top_cells["n_m5_future"].sum()

        capture_rate = (captured_events / total_events) if total_events > 0 else np.nan
        results[f"top_{int(percentage * 100)}_percent"] = {
            "cells_selected": int(n_cells),
            "events_captured": int(captured_events),
            "total_future_events": int(total_events),
            "capture_rate": float(capture_rate) if not np.isnan(capture_rate) else None,
        }
    return results


def calculate_metrics(risk_map: pd.DataFrame) -> dict:
    y_true = risk_map["has_m5_future"].values
    y_prob = risk_map["predicted_probability"].values

    y_prob_safe = np.clip(y_prob, 1e-7, 1 - 1e-7)

    metrics = {
        "brier_score": float(brier_score_loss(y_true, y_prob)),
        "log_loss": float(log_loss(y_true, y_prob_safe)),
        "top_capture": calculate_top_capture(risk_map),
    }

    if len(np.unique(y_true)) == 2:
        metrics["roc_auc"] = float(roc_auc_score(y_true, y_prob))
        metrics["average_precision"] = float(average_precision_score(y_true, y_prob))
    else:
        metrics["roc_auc"] = None
        metrics["average_precision"] = None

    return metrics
  
