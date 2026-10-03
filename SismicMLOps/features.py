"""Spatial binning and seismic feature engineering module."""

import math
from typing import Optional
from pathlib import Path
import numpy as np
import pandas as pd
import config

def add_cfm_features(df_grid: pd.DataFrame, cfm_path: str = None) -> pd.DataFrame:
    """
    Integra todas las características geométricas y geológicas 3D del CFM
    a la malla espacial (grid_i, grid_j).
    """
    if cfm_path is None:
        cfm_path = config.CFM_DATA_PATH
        
    df = df_grid.copy()
    
    try:
        df_cfm = pd.read_parquet(cfm_path)
    except Exception as e:
        print(f"⚠️ No se pudo cargar el dataset CFM desde {cfm_path}: {e}. Se omiten estas features.")
        return df

    # Asignar índices de celda (grid_i, grid_j) al dataset de eventos con CFM
    if "grid_i" not in df_cfm.columns or "grid_j" not in df_cfm.columns:
        df_cfm = assign_grid_indices(df_cfm)

    # Convertir variables categóricas a numéricas mediante One-Hot Encoding
    if "nearest_fault_slip_sense" in df_cfm.columns:
        df_cfm = pd.get_dummies(df_cfm, columns=["nearest_fault_slip_sense"], prefix="slip_sense", dummy_na=False)

    # Identificar todas las características numéricas a resumir
    numeric_cols = [
        "distance_to_nearest_fault_km",
        "nearest_fault_vertex_depth_km",
        "nearest_fault_strike",
        "nearest_fault_dip",
        "nearest_fault_area_km2",
        "fault_count_5km",
        "fault_count_10km",
        "fault_count_20km",
        "fault_density_10km"
    ] + [c for c in df_cfm.columns if c.startswith("slip_sense_")]

    # Filtrar solo columnas presentes
    cols_to_agg = [c for c in numeric_cols if c in df_cfm.columns]

    # Agrupar por celda (grid_i, grid_j) promediando la influencia geológica
    cfm_summary = df_cfm.groupby(["grid_i", "grid_j"])[cols_to_agg].mean().reset_index()

    # Fusionar con el DataFrame de la malla
    df_merged = pd.merge(df, cfm_summary, on=["grid_i", "grid_j"], how="left")

    # Imputar celdas vacías utilizando la mediana regional
    for col in cols_to_agg:
        if col in df_merged.columns:
            df_merged[col] = df_merged[col].fillna(df_merged[col].median())

    return df_merged


def assign_grid_indices(df: pd.DataFrame) -> pd.DataFrame:
    """Asigna los índices de celda (grid_i, grid_j) a las coordenadas del dataset."""
    df = df.copy()
    
    if "latitude" not in df.columns or "longitude" not in df.columns:
        raise KeyError("El DataFrame debe contener las columnas 'latitude' y 'longitude'.")
        
    lat_step = (config.LAT_MAX - config.LAT_MIN) / config.GRID_ROWS
    lon_step = (config.LON_MAX - config.LON_MIN) / config.GRID_COLS
    
    df["grid_i"] = ((df["latitude"] - config.LAT_MIN) / lat_step).astype(int)
    df["grid_j"] = ((df["longitude"] - config.LON_MIN) / lon_step).astype(int)
    
    df["grid_i"] = df["grid_i"].clip(0, config.GRID_ROWS - 1)
    df["grid_j"] = df["grid_j"].clip(0, config.GRID_COLS - 1)
    
    return df


def build_grid_features(df_events: pd.DataFrame, cutoff_year: Optional[int] = None) -> pd.DataFrame:
    """
    Agrupa el catálogo por celda calculando indicadores sismológicos
    hasta un año de corte para evitar data leakage.
    """
    df = df_events.copy()
    
    if "grid_i" not in df.columns or "grid_j" not in df.columns:
        df = assign_grid_indices(df)
        
    if "year" not in df.columns and "time" in df.columns:
        #  Usa format="mixed" para inferir dinámicamente cada registro
        df["year"] = pd.to_datetime(df["time"], format="mixed", errors="coerce").dt.year


    # Filtrar solo la información histórica hasta el año límite (ej: 2003)
    if cutoff_year is not None and "year" in df.columns:
        df = df[df["year"] <= cutoff_year]

    grid_df = df.groupby(["grid_i", "grid_j"]).agg(
        seismic_rate=("magnitude", "count"),
        max_past_magnitude=("magnitude", "max"),
        mean_magnitude=("magnitude", "mean")
    ).reset_index()

    return grid_df
    


def grid_to_latlon(df: pd.DataFrame) -> pd.DataFrame:
    """Convierte los índices de la celda a coordenadas y genera la URL para Google Maps."""
    df = df.copy()
    
    lat_step = (config.LAT_MAX - config.LAT_MIN) / config.GRID_ROWS
    lon_step = (config.LON_MAX - config.LON_MIN) / config.GRID_COLS
    
    df["latitude"] = config.LAT_MIN + (df["grid_i"] + 0.5) * lat_step
    df["longitude"] = config.LON_MIN + (df["grid_j"] + 0.5) * lon_step
    
    df["google_maps_url"] = df.apply(
        lambda r: f"https://www.google.com/maps?q={r['latitude']:.4f},{r['longitude']:.4f}", axis=1
    )
    
    return df

def create_temporal_split_datasets(df_mapped: pd.DataFrame, 
                                   train_cutoff_year: int = 2003, 
                                   val_cutoff_year: int = 2013, 
                                   target_mag: float = 5.0):
    """
    Crea las matrices de Train y Test aplicando MultiIndex.isin vectorizado
    y separación temporal estricta.
    """
    df = df_mapped.copy()
    
    if "year" not in df.columns and "time" in df.columns:
        # format="mixed" y errors="coerce" evitan que el script falle por formatos mixtos o nulos
        df["year"] = pd.to_datetime(df["time"], format="mixed", errors="coerce").dt.year

    # 1. Construir features basándose ÚNICAMENTE en el pasado histórico (<= 2003)
    df_grid_features = build_grid_features(df, cutoff_year=train_cutoff_year)

    # 2. Identificar celdas con eventos M>=5 en los periodos futuros
    df_train_period = df[(df["year"] > train_cutoff_year) & (df["year"] <= val_cutoff_year)]
    df_test_period = df[df["year"] > val_cutoff_year]

    # Extraer pares (grid_i, grid_j) donde hubo terremoto M>=5
    train_m5_pairs = df_train_period[df_train_period["magnitude"] >= target_mag][["grid_i", "grid_j"]].drop_duplicates()
    test_m5_pairs = df_test_period[df_test_period["magnitude"] >= target_mag][["grid_i", "grid_j"]].drop_duplicates()

    # 3. Asignación vectorizada de TARGET usando MultiIndex.isin
    grid_index = pd.MultiIndex.from_frame(df_grid_features[["grid_i", "grid_j"]])
    
    train_index = pd.MultiIndex.from_frame(train_m5_pairs) if not train_m5_pairs.empty else pd.MultiIndex(levels=[[],[]], codes=[[],[]])
    test_index = pd.MultiIndex.from_frame(test_m5_pairs) if not test_m5_pairs.empty else pd.MultiIndex(levels=[[],[]], codes=[[],[]])

    df_train = df_grid_features.copy()
    df_train["target"] = grid_index.isin(train_index).astype(int)

    df_test = df_grid_features.copy()
    df_test["target"] = grid_index.isin(test_index).astype(int)

    return df_train, df_test
                                       
