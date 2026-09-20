"""
prepare_cfm_gemini.py - Versión Optimizada para Dataset XGBoost
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from pyproj import Transformer

# Configuración de Proyección
CFM_CRS = "EPSG:26711"      # UTM Zone 11N (Metros)
EARTHQUAKE_CRS = "EPSG:4326" # WGS84 (Lat/Lon)

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
CFM_DIR = DATA_DIR / "external" / "CFM6"
OUTPUT_DIR = DATA_DIR / "processed" / "cfm"

VERTICES_OUTPUT = OUTPUT_DIR / "cfm_vertices_1000m.csv"
METADATA_OUTPUT = OUTPUT_DIR / "cfm_metadata_clean.csv"

VRTX_PATTERN = re.compile(
    r"^\s*VRTX\s+(\d+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)"
)

def parse_tsurf_vertices(ts_path: Path) -> pd.DataFrame:
    vertices = []
    with ts_path.open("r", encoding="utf-8", errors="ignore") as file:
        for line in file:
            match = VRTX_PATTERN.match(line)
            if match:
                vertices.append({
                    "local_vertex_id": int(match.group(1)),
                    "x_utm": float(match.group(2)),
                    "y_utm": float(match.group(3)),
                    "z_m": float(match.group(4)),
                })
    df = pd.DataFrame(vertices)
    df["fault_name"] = ts_path.stem
    return df

def convert_coordinates(vertices: pd.DataFrame) -> pd.DataFrame:
    transformer = Transformer.from_crs(CFM_CRS, EARTHQUAKE_CRS, always_xy=True)
    longitude, latitude = transformer.transform(
        vertices["x_utm"].to_numpy(),
        vertices["y_utm"].to_numpy(),
    )
    vertices["longitude"] = longitude
    vertices["latitude"] = latitude
    vertices["depth_km"] = -vertices["z_m"] / 1000.0
    return vertices

def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts_dir = next(CFM_DIR.rglob("1000m"))
    ts_files = sorted(ts_dir.glob("*.ts"))

    all_dfs = []
    for ts_path in ts_files:
        df = parse_tsurf_vertices(ts_path)
        if not df.empty:
            all_dfs.append(df)

    vertices_df = pd.concat(all_dfs, ignore_index=True)
    vertices_df = convert_coordinates(vertices_df)
    
    # Índice global explícito para evitar confusiones
    vertices_df["global_vertex_idx"] = np.arange(len(vertices_df))
    vertices_df.to_csv(VERTICES_OUTPUT, index=False)
    print(f"Vértices procesados y guardados: {len(vertices_df):,}")

if __name__ == "__main__":
    main()
  
