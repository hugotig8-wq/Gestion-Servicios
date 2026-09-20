"""
build_cfm_features_gemini.py - Construcción del Dataset Final para XGBoost
"""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy.spatial import cKDTree

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"

EARTHQUAKES_FILE = DATA_DIR / "raw" / "earthquakes.csv"
CFM_VERTICES_FILE = DATA_DIR / "processed" / "cfm" / "cfm_vertices_1000m.csv"
CFM_METADATA_FILE = DATA_DIR / "processed" / "cfm" / "cfm_metadata_clean.csv"

OUTPUT_DIR = DATA_DIR / "processed" / "cfm"
OUTPUT_PARQUET = OUTPUT_DIR / "xgboost_earthquakes_cfm_dataset.parquet"

# Configuración Espacial
CFM_CRS = "EPSG:26711"      # UTM 11N
EARTHQUAKE_CRS = "EPSG:4326" # WGS84

RADII_KM = [5.0, 10.0, 20.0]

def load_and_project_earthquakes() -> pd.DataFrame:
    df = pd.read_csv(EARTHQUAKES_FILE)
    
    # Proyección de Lat/Lon a UTM Zone 11N (Metros)
    transformer = Transformer.from_crs(EARTHQUAKE_CRS, CFM_CRS, always_xy=True)
    x_utm, y_utm = transformer.transform(df["longitude"].to_numpy(), df["latitude"].to_numpy())
    
    df["x_utm"] = x_utm
    df["y_utm"] = y_utm
    # Convención Z: Profundidad negativa en metros (concuerda con el CFM)
    df["z_m"] = -df["depth"] * 1000.0 
    return df

def main() -> None:
    print("Cargando datos...")
    eq_df = load_and_project_earthquakes()
    vertices_df = pd.read_csv(CFM_VERTICES_FILE)
    metadata_df = pd.read_csv(CFM_METADATA_FILE)

    # 1. Construcción de Arbol cKDTree 3D en Metros
    print("Construyendo árbol KDTree 3D...")
    cfm_coords_3d = vertices_df[["x_utm", "y_utm", "z_m"]].to_numpy()
    tree_3d = cKDTree(cfm_coords_3d)

    eq_coords_3d = eq_df[["x_utm", "y_utm", "z_m"]].to_numpy()

    # 2. Búsqueda del Vértice/Falla Más Cercana (Distancia 3D Exacta)
    print("Calculando distancias 3D...")
    distances_m, nearest_indices = tree_3d.query(eq_coords_3d, k=1)

    eq_df["distance_to_nearest_fault_km"] = distances_m / 1000.0
    
    # Asignar la falla más cercana usando el índice retornado por KDTree
    nearest_faults = vertices_df.iloc[nearest_indices]["fault_name"].values
    eq_df["nearest_fault_name"] = nearest_faults
    eq_df["nearest_fault_vertex_depth_km"] = vertices_df.iloc[nearest_indices]["depth_km"].values

    # 3. Conteo de Fallas Únicas dentro de los radios (Densidad Geológica Real)
    print("Calculando conteo y densidad de FALLAS ÚNICAS...")
    for r_km in RADII_KM:
        r_m = r_km * 1000.0
        # Retorna lista de índices de vértices dentro del radio
        neighbors_list = tree_3d.query_ball_point(eq_coords_3d, r=r_m)
        
        # Mapear índices a nombres de fallas y obtener conteo único
        unique_fault_counts = [
            len(set(vertices_df.iloc[idxs]["fault_name"])) if idxs else 0
            for idxs in neighbors_list
        ]
        
        eq_df[f"fault_count_{int(r_km)}km"] = unique_fault_counts

    # Densidad en el radio principal de 10km (Fallas únicas por km²)
    area_10km2 = np.pi * (10.0 ** 2)
    eq_df["fault_density_10km"] = eq_df["fault_count_10km"] / area_10km2

    # 4. Merge de Metadata Geológica de la Falla Más Cercana
    print("Uniendo metadata geológica...")
    metadata_sub = metadata_df[[
        "CFM6.0 Fault Object Name", "wAvgStrike", "wAvgDip", 
        "TotalArea(km^2)", "Slip Sense"
    ]].drop_duplicates(subset=["CFM6.0 Fault Object Name"])

    eq_df = eq_df.merge(
        metadata_sub,
        left_on="nearest_fault_name",
        right_on="CFM6.0 Fault Object Name",
        how="left"
    )

    # Renombrar columnas para formato limpio final
    eq_df.rename(columns={
        "wAvgStrike": "nearest_fault_strike",
        "wAvgDip": "nearest_fault_dip",
        "TotalArea(km^2)": "nearest_fault_area_km2",
        "Slip Sense": "nearest_fault_slip_sense"
    }, inplace=True)

    # Limpieza final de columnas
    features_to_keep = [
        "earthquake_id", "latitude", "longitude", "depth", "magnitude",
        "distance_to_nearest_fault_km", "nearest_fault_name",
        "nearest_fault_vertex_depth_km", "nearest_fault_strike", 
        "nearest_fault_dip", "nearest_fault_area_km2", "nearest_fault_slip_sense",
        "fault_count_5km", "fault_count_10km", "fault_count_20km", "fault_density_10km"
    ]
    
    final_dataset = eq_df[[col for col in features_to_keep if col in eq_df.columns]]
    
    # Guardado Parquet
    final_dataset.to_parquet(OUTPUT_PARQUET, index=False)
    print(f"\nDataset para XGBoost construido exitosamente en:\n{OUTPUT_PARQUET}")

if __name__ == "__main__":
    main()
  
