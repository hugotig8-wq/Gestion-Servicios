import pandas as pd
from Sismic_MLOps.config import DATA_PATH, TRAIN_START, TRAIN_END, MIN_MAGNITUDE_FEATURE


def find_column(df: pd.DataFrame, candidates: list[str], description: str) -> str:
    normalized = {str(col).strip().lower(): col for col in df.columns}
    for candidate in candidates:
        candidate_norm = candidate.lower()
        if candidate_norm in normalized:
            return normalized[candidate_norm]
    raise ValueError(
        f"No se pudo identificar {description}. "
        f"Candidatos: {candidates}. Columnas disponibles: {list(df.columns)}"
    )


def detect_columns(df: pd.DataFrame) -> dict[str, str]:
    return {
        "time": find_column(df, ["time", "timestamp", "datetime", "date", "origin_time"], "timestamp"),
        "latitude": find_column(df, ["latitude", "lat"], "latitude"),
        "longitude": find_column(df, ["longitude", "lon", "lng"], "longitude"),
        "magnitude": find_column(df, ["magnitude", "mag", "mw", "ml"], "magnitude"),
        "depth": find_column(df, ["depth", "depth_km", "depthkm"], "depth"),
    }


def load_catalog() -> tuple[pd.DataFrame, pd.DataFrame]:
    print(f"\nCargando catálogo desde: {DATA_PATH}")
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Archivo no encontrado en: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    columns = detect_columns(df)

    df = df.rename(columns={v: k for k, v in columns.items()})

    df["time"] = pd.to_datetime(df["time"], errors="coerce", utc=True)
    for col in ["latitude", "longitude", "magnitude", "depth"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["time", "latitude", "longitude", "magnitude", "depth"]).copy()

    df_train = df[
        (df["time"] >= TRAIN_START)
        & (df["time"] <= TRAIN_END)
        & (df["magnitude"] >= MIN_MAGNITUDE_FEATURE)
    ].copy()

    if len(df_train) == 0:
        raise RuntimeError("No se encontraron eventos en el rango de entrenamiento.")

    return df, df_train
        
