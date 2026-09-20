"""
build_cfm_features.py

Relaciona earthquakes.csv con CFM6.0.

Esta primera versión calcula:
- vértice CFM más cercano
- distancia al vértice más cercano
- falla más cercana
- profundidad del vértice
- densidad de vértices CFM en 5, 10 y 20 km
- metadata de la falla más cercana

IMPORTANTE:
La distancia calculada aquí es al vértice CFM más cercano,
NO todavía a la superficie triangular 3D.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# CONFIGURACIÓN
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent

DATA_DIR = PROJECT_ROOT / "data"

EARTHQUAKES_FILE = (
    DATA_DIR / "raw" / "earthquakes.csv"
)

CFM_VERTICES_FILE = (
    DATA_DIR
    / "processed"
    / "cfm"
    / "cfm_vertices_1000m.csv"
)

CFM_METADATA_FILE = (
    DATA_DIR
    / "processed"
    / "cfm"
    / "cfm_metadata_clean.csv"
)

OUTPUT_DIR = (
    DATA_DIR / "processed" / "cfm"
)

OUTPUT_PARQUET = (
    OUTPUT_DIR
    / "earthquakes_cfm_features.parquet"
)

OUTPUT_CSV = (
    OUTPUT_DIR
    / "earthquakes_cfm_features.csv"
)

REPORT_FILE = (
    OUTPUT_DIR
    / "cfm_feature_report.txt"
)


# ============================================================
# PARÁMETROS
# ============================================================

RADII_KM = (
    5.0,
    10.0,
    20.0,
)

EARTHQUAKE_BATCH_SIZE = 1000


# ============================================================
# COLUMNAS POSIBLES
# ============================================================

EARTHQUAKE_LAT_COLUMNS = (
    "latitude",
    "lat",
)

EARTHQUAKE_LON_COLUMNS = (
    "longitude",
    "lon",
    "lng",
)

EARTHQUAKE_DEPTH_COLUMNS = (
    "depth",
    "depth_km",
)

EARTHQUAKE_MAG_COLUMNS = (
    "magnitude",
    "mag",
)


# ============================================================
# UTILIDADES
# ============================================================

def print_header(title: str) -> None:
    """Imprime un encabezado."""

    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def find_column(
    dataframe: pd.DataFrame,
    candidates: tuple[str, ...],
    description: str,
) -> str:
    """Busca una columna utilizando varios nombres posibles."""

    normalized = {
        str(column).strip().lower(): column
        for column in dataframe.columns
    }

    for candidate in candidates:
        if candidate.lower() in normalized:
            return normalized[candidate.lower()]

    raise ValueError(
        f"No se encontró la columna necesaria para: "
        f"{description}\n\n"
        f"Columnas disponibles:\n"
        f"{list(dataframe.columns)}"
    )


# ============================================================
# HAVERSINE
# ============================================================

def haversine_distance_km(
    latitude_1: np.ndarray,
    longitude_1: np.ndarray,
    latitude_2: np.ndarray,
    longitude_2: np.ndarray,
) -> np.ndarray:
    """
    Calcula distancia superficial aproximada entre puntos.

    Entrada:
        latitudes y longitudes en grados.

    Salida:
        distancia en kilómetros.
    """

    earth_radius_km = 6371.0088

    lat1 = np.radians(latitude_1)
    lat2 = np.radians(latitude_2)

    delta_lat = np.radians(
        latitude_2 - latitude_1
    )

    delta_lon = np.radians(
        longitude_2 - longitude_1
    )

    a = (
        np.sin(delta_lat / 2.0) ** 2
        + np.cos(lat1)
        * np.cos(lat2)
        * np.sin(delta_lon / 2.0) ** 2
    )

    a = np.clip(
        a,
        0.0,
        1.0,
    )

    c = 2.0 * np.arcsin(
        np.sqrt(a)
    )

    return earth_radius_km * c


# ============================================================
# CARGA DE EARTHQUAKES
# ============================================================

def load_earthquakes() -> pd.DataFrame:
    """Carga y valida earthquakes.csv."""

    print_header(
        "CARGANDO EARTHQUAKES.CSV"
    )

    if not EARTHQUAKES_FILE.exists():
        raise FileNotFoundError(
            f"No existe:\n{EARTHQUAKES_FILE}"
        )

    print(
        f"Archivo:\n  {EARTHQUAKES_FILE}"
    )

    earthquakes = pd.read_csv(
        EARTHQUAKES_FILE
    )

    print(
        f"Filas originales: "
        f"{len(earthquakes):,}"
    )

    lat_column = find_column(
        earthquakes,
        EARTHQUAKE_LAT_COLUMNS,
        "latitude",
    )

    lon_column = find_column(
        earthquakes,
        EARTHQUAKE_LON_COLUMNS,
        "longitude",
    )

    depth_column = find_column(
        earthquakes,
        EARTHQUAKE_DEPTH_COLUMNS,
        "depth",
    )

    earthquakes = earthquakes.copy()

    earthquakes["latitude"] = pd.to_numeric(
        earthquakes[lat_column],
        errors="coerce",
    )

    earthquakes["longitude"] = pd.to_numeric(
        earthquakes[lon_column],
        errors="coerce",
    )

    earthquakes["depth_km"] = pd.to_numeric(
        earthquakes[depth_column],
        errors="coerce",
    )

    for magnitude_column in EARTHQUAKE_MAG_COLUMNS:

        if magnitude_column in earthquakes.columns:

            earthquakes["magnitude"] = pd.to_numeric(
                earthquakes[magnitude_column],
                errors="coerce",
            )

            break

    valid = (
        earthquakes["latitude"].between(
            -90.0,
            90.0,
        )
        & earthquakes["longitude"].between(
            -180.0,
            180.0,
        )
        & earthquakes["latitude"].notna()
        & earthquakes["longitude"].notna()
    )

    invalid_count = int(
        (~valid).sum()
    )

    if invalid_count:
        print(
            f"Filas eliminadas por coordenadas inválidas: "
            f"{invalid_count:,}"
        )

    earthquakes = earthquakes.loc[
        valid
    ].copy()

    earthquakes.reset_index(
        drop=True,
        inplace=True,
    )

    earthquakes["earthquake_id"] = np.arange(
        len(earthquakes),
        dtype=np.int64,
    )

    print(
        f"Filas válidas: "
        f"{len(earthquakes):,}"
    )

    print(
        f"Latitude: "
        f"{earthquakes['latitude'].min():.6f} "
        f"→ "
        f"{earthquakes['latitude'].max():.6f}"
    )

    print(
        f"Longitude: "
        f"{earthquakes['longitude'].min():.6f} "
        f"→ "
        f"{earthquakes['longitude'].max():.6f}"
    )

    return earthquakes


# ============================================================
# CARGA CFM
# ============================================================

def load_cfm_vertices() -> pd.DataFrame:
    """Carga los vértices CFM."""

    print_header(
        "CARGANDO VÉRTICES CFM"
    )

    if not CFM_VERTICES_FILE.exists():
        raise FileNotFoundError(
            f"No existe:\n{CFM_VERTICES_FILE}\n\n"
            "Ejecuta primero:\n"
            "python prepare_cfm.py"
        )

    print(
        f"Archivo:\n  {CFM_VERTICES_FILE}"
    )

    columns = [
        "vertex_id",
        "fault_name",
        "longitude",
        "latitude",
        "z",
        "depth_km",
    ]

    vertices = pd.read_csv(
        CFM_VERTICES_FILE,
        usecols=lambda column: column in columns,
    )

    print(
        f"Vértices cargados: "
        f"{len(vertices):,}"
    )

    required = [
        "vertex_id",
        "fault_name",
        "longitude",
        "latitude",
    ]

    missing = [
        column
        for column in required
        if column not in vertices.columns
    ]

    if missing:
        raise ValueError(
            "Faltan columnas CFM:\n"
            f"{missing}"
        )

    valid = (
        vertices["latitude"].between(
            -90.0,
            90.0,
        )
        & vertices["longitude"].between(
            -180.0,
            180.0,
        )
        & vertices["latitude"].notna()
        & vertices["longitude"].notna()
    )

    invalid_count = int(
        (~valid).sum()
    )

    if invalid_count:
        print(
            f"Vértices inválidos eliminados: "
            f"{invalid_count:,}"
        )

    vertices = vertices.loc[
        valid
    ].copy()

    vertices.reset_index(
        drop=True,
        inplace=True,
    )

    return vertices


# ============================================================
# CARGA METADATA
# ============================================================

def load_cfm_metadata() -> pd.DataFrame:
    """Carga metadata del CFM."""

    print_header(
        "CARGANDO METADATA CFM"
    )

    if not CFM_METADATA_FILE.exists():
        raise FileNotFoundError(
            f"No existe:\n{CFM_METADATA_FILE}"
        )

    metadata = pd.read_csv(
        CFM_METADATA_FILE
    )

    print(
        f"Filas metadata: "
        f"{len(metadata):,}"
    )

    columns_lower = {
        str(column).strip().lower(): column
        for column in metadata.columns
    }

    object_column = None

    for candidate in (
        "CFM6.0 Fault Object Name",
        "Fault Name",
    ):

        if candidate.lower() in columns_lower:

            object_column = columns_lower[
                candidate.lower()
            ]

            break

    if object_column is None:

        print(
            "ADVERTENCIA: no se encontró "
            "el nombre del objeto CFM."
        )

        return metadata

    metadata = metadata.copy()

    metadata["cfm_object_name"] = (
        metadata[object_column]
        .astype(str)
        .str.strip()
    )

    for column in (
        "wAvgStrike",
        "wAvgDip",
        "TotalArea(km^2)",
    ):

        if column in metadata.columns:

            metadata[column] = pd.to_numeric(
                metadata[column],
                errors="coerce",
            )

    return metadata


# ============================================================
# ÍNDICE ESPACIAL
# ============================================================

def build_spatial_index(
    vertices: pd.DataFrame,
) -> dict:
    """
    Divide las coordenadas en celdas geográficas
    de aproximadamente 0.1 grados.
    """

    bin_size = 0.1

    result = {
        "bin_size": bin_size,
        "bins": {},
    }

    lat_bins = np.floor(
        vertices["latitude"].to_numpy()
        / bin_size
    ).astype(np.int32)

    lon_bins = np.floor(
        vertices["longitude"].to_numpy()
        / bin_size
    ).astype(np.int32)

    for index, (
        lat_bin,
        lon_bin,
    ) in enumerate(
        zip(
            lat_bins,
            lon_bins,
        )
    ):

        key = (
            int(lat_bin),
            int(lon_bin),
        )

        if key not in result["bins"]:
            result["bins"][key] = []

        result["bins"][key].append(
            index
        )

    return result


# ============================================================
# VÉRTICE MÁS CERCANO
# ============================================================

def find_nearest_vertex(
    latitude: float,
    longitude: float,
    vertices: pd.DataFrame,
    spatial_index: dict,
) -> tuple[int | None, float]:

    bin_size = spatial_index["bin_size"]

    lat_bin = math.floor(
        latitude / bin_size
    )

    lon_bin = math.floor(
        longitude / bin_size
    )

    candidate_indices = []

    for delta_lat in range(-3, 4):

        for delta_lon in range(-3, 4):

            key = (
                lat_bin + delta_lat,
                lon_bin + delta_lon,
            )

            indices = spatial_index[
                "bins"
            ].get(
                key
            )

            if indices:
                candidate_indices.extend(
                    indices
                )

    if not candidate_indices:
        return None, float("nan")

    candidate_indices = list(
        set(candidate_indices)
    )

    candidates = vertices.iloc[
        candidate_indices
    ]

    distances = haversine_distance_km(
        latitude,
        longitude,
        candidates["latitude"].to_numpy(),
        candidates["longitude"].to_numpy(),
    )

    minimum_position = int(
        np.argmin(distances)
    )

    minimum_distance = float(
        distances[minimum_position]
    )

    vertex_index = candidate_indices[
        minimum_position
    ]

    return (
        vertex_index,
        minimum_distance,
    )


# ============================================================
# FEATURES TERREMOTO → CFM
# ============================================================

def calculate_nearest_fault_features(
    earthquakes: pd.DataFrame,
    vertices: pd.DataFrame,
) -> pd.DataFrame:

    print_header(
        "CALCULANDO FEATURES TERREMOTO → CFM"
    )

    spatial_index = build_spatial_index(
        vertices
    )

    print(
        f"Bins espaciales: "
        f"{len(spatial_index['bins']):,}"
    )

    earthquake_count = len(
        earthquakes
    )

    nearest_distance = np.full(
        earthquake_count,
        np.nan,
        dtype=np.float64,
    )

    nearest_vertex_index = np.full(
        earthquake_count,
        -1,
        dtype=np.int64,
    )

    for start in range(
        0,
        earthquake_count,
        EARTHQUAKE_BATCH_SIZE,
    ):

        end = min(
            start + EARTHQUAKE_BATCH_SIZE,
            earthquake_count,
        )

        print(
            f"Procesando terremotos "
            f"{start:,} - {end:,} "
            f"de {earthquake_count:,}"
        )

        batch = earthquakes.iloc[
            start:end
        ]

        for local_index, row in enumerate(
            batch.itertuples(
                index=False
            )
        ):

            global_index = (
                start + local_index
            )

            vertex_index, distance = (
                find_nearest_vertex(
                    latitude=float(
                        row.latitude
                    ),
                    longitude=float(
                        row.longitude
                    ),
                    vertices=vertices,
                    spatial_index=spatial_index,
                )
            )

            if vertex_index is None:
                continue

            nearest_distance[
                global_index
            ] = distance

            nearest_vertex_index[
                global_index
            ] = vertex_index

    result = earthquakes.copy()

    result[
        "cfm_nearest_vertex_index"
    ] = nearest_vertex_index

    result[
        "cfm_distance_nearest_vertex_km"
    ] = nearest_distance

    result[
        "cfm_nearest_fault"
    ] = None

    result[
        "cfm_nearest_fault_depth_km"
    ] = np.nan

    valid_indices = (
        nearest_vertex_index >= 0
    )

    if valid_indices.any():

        selected_vertices = vertices.iloc[
            nearest_vertex_index[
                valid_indices
            ]
        ]

        result.loc[
            valid_indices,
            "cfm_nearest_fault",
        ] = (
            selected_vertices[
                "fault_name"
            ].to_numpy()
        )

        if "depth_km" in vertices.columns:

            result.loc[
                valid_indices,
                "cfm_nearest_fault_depth_km",
            ] = (
                selected_vertices[
                    "depth_km"
                ].to_numpy()
            )

    return result


# ============================================================
# DENSIDAD CFM
# ============================================================

def calculate_fault_proximity_counts(
    earthquakes: pd.DataFrame,
    vertices: pd.DataFrame,
) -> pd.DataFrame:

    print_header(
        "CALCULANDO DENSIDAD CFM"
    )

    result = earthquakes.copy()

    spatial_index = build_spatial_index(
        vertices
    )

    for radius_km in RADII_KM:

        column_name = (
            "cfm_vertex_count_within_"
            f"{int(radius_km)}km"
        )

        counts = np.zeros(
            len(result),
            dtype=np.int32,
        )

        latitude_degree_km = 111.32

        for index, row in enumerate(
            result.itertuples(
                index=False
            )
        ):

            latitude = float(
                row.latitude
            )

            longitude = float(
                row.longitude
            )

            radius_lat = (
                radius_km
                / latitude_degree_km
            )

            longitude_degree_km = (
                111.32
                * max(
                    math.cos(
                        math.radians(
                            latitude
                        )
                    ),
                    0.01,
                )
            )

            radius_lon = (
                radius_km
                / longitude_degree_km
            )

            lat_min = (
                latitude - radius_lat
            )

            lat_max = (
                latitude + radius_lat
            )

            lon_min = (
                longitude - radius_lon
            )

            lon_max = (
                longitude + radius_lon
            )

            lat_bin_min = math.floor(
                lat_min
                / spatial_index["bin_size"]
            )

            lat_bin_max = math.floor(
                lat_max
                / spatial_index["bin_size"]
            )

            lon_bin_min = math.floor(
                lon_min
                / spatial_index["bin_size"]
            )

            lon_bin_max = math.floor(
                lon_max
                / spatial_index["bin_size"]
            )

            candidate_indices = []

            for lat_bin in range(
                lat_bin_min,
                lat_bin_max + 1,
            ):

                for lon_bin in range(
                    lon_bin_min,
                    lon_bin_max + 1,
                ):

                    candidate_indices.extend(
                        spatial_index[
                            "bins"
                        ].get(
                            (
                                lat_bin,
                                lon_bin,
                            ),
                            [],
                        )
                    )

            if not candidate_indices:
                continue

            candidate_indices = list(
                set(candidate_indices)
            )

            candidates = vertices.iloc[
                candidate_indices
            ]

            distances = haversine_distance_km(
                latitude,
                longitude,
                candidates[
                    "latitude"
                ].to_numpy(),
                candidates[
                    "longitude"
                ].to_numpy(),
            )

            counts[index] = int(
                np.sum(
                    distances <= radius_km
                )
            )

        result[column_name] = counts

        print(
            f"{column_name}: "
            f"media = "
            f"{result[column_name].mean():.2f}"
        )

    return result


# ============================================================
# METADATA DE LA FALLA MÁS CERCANA
# ============================================================

def attach_fault_metadata(
    earthquakes: pd.DataFrame,
    metadata: pd.DataFrame,
) -> pd.DataFrame:

    print_header(
        "RELACIONANDO METADATA DE FALLAS"
    )

    result = earthquakes.copy()

    if "cfm_object_name" not in metadata.columns:

        print(
            "No existe cfm_object_name."
        )

        print(
            "Se omite la incorporación de metadata."
        )

        return result

    metadata_for_merge = (
        metadata[
            [
                "cfm_object_name",
                "wAvgStrike",
                "wAvgDip",
                "TotalArea(km^2)",
                "Exposure",
                "Slip Sense",
            ]
        ]
        .drop_duplicates(
            subset=[
                "cfm_object_name"
            ]
        )
    )

    result["cfm_nearest_fault"] = (
        result["cfm_nearest_fault"]
        .astype(str)
        .str.strip()
    )

    metadata_for_merge[
        "cfm_object_name"
    ] = (
        metadata_for_merge[
            "cfm_object_name"
        ]
        .astype(str)
        .str.strip()
    )

    result = result.merge(
        metadata_for_merge,
        left_on="cfm_nearest_fault",
        right_on="cfm_object_name",
        how="left",
    )

    rename_map = {
        "wAvgStrike":
            "cfm_nearest_fault_strike_deg",

        "wAvgDip":
            "cfm_nearest_fault_dip_deg",

        "TotalArea(km^2)":
            "cfm_nearest_fault_area_km2",

        "Exposure":
            "cfm_nearest_fault_exposure",

        "Slip Sense":
            "cfm_nearest_fault_slip_sense",
    }

    result.rename(
        columns=rename_map,
        inplace=True,
    )

    return result


# ============================================================
# REPORTE
# ============================================================

def build_report(
    result: pd.DataFrame,
    vertices: pd.DataFrame,
) -> str:

    lines = []

    lines.append(
        "CFM6.0 EARTHQUAKE FEATURE REPORT"
    )

    lines.append(
        "=" * 70
    )

    lines.append("")

    lines.append(
        f"Earthquakes processed: "
        f"{len(result):,}"
    )

    lines.append(
        f"CFM vertices available: "
        f"{len(vertices):,}"
    )

    lines.append("")

    lines.append(
        "Nearest CFM vertex distance:"
    )

    distance = result[
        "cfm_distance_nearest_vertex_km"
    ]

    lines.append(
        f"  valid: "
        f"{distance.notna().sum():,}"
    )

    lines.append(
        f"  missing: "
        f"{distance.isna().sum():,}"
    )

    if distance.notna().any():

        lines.append(
            f"  min: "
            f"{distance.min():.4f} km"
        )

        lines.append(
            f"  median: "
            f"{distance.median():.4f} km"
        )

        lines.append(
            f"  mean: "
            f"{distance.mean():.4f} km"
        )

        lines.append(
            f"  max: "
            f"{distance.max():.4f} km"
        )

    lines.append("")

    lines.append(
        "Nearest CFM faults:"
    )

    if "cfm_nearest_fault" in result.columns:

        unique_faults = (
            result[
                "cfm_nearest_fault"
            ]
            .dropna()
            .nunique()
        )

        lines.append(
            f"  unique faults assigned: "
            f"{unique_faults:,}"
        )

    lines.append("")

    lines.append(
        "Output columns:"
    )

    for column in result.columns:

        lines.append(
            f"  - {column}"
        )

    lines.append("")

    lines.append(
        "IMPORTANT:"
    )

    lines.append(
        "cfm_distance_nearest_vertex_km is the "
        "distance to the nearest CFM vertex."
    )

    lines.append(
        "It is NOT yet the exact 3D point-to-surface "
        "distance."
    )

    lines.append("")

    lines.append(
        "The vertex count features count CFM vertices, "
        "not unique geological faults."
    )

    return "\n".join(lines)


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    print_header(
        "CFM6.0 → EARTHQUAKES FEATURE BUILDER"
    )

    print(
        f"Project root:\n  {PROJECT_ROOT}"
    )

    # --------------------------------------------------------
    # 1. Earthquakes
    # --------------------------------------------------------

    earthquakes = load_earthquakes()

    # --------------------------------------------------------
    # 2. CFM vertices
    # --------------------------------------------------------

    vertices = load_cfm_vertices()

    # --------------------------------------------------------
    # 3. Metadata
    # --------------------------------------------------------

    metadata = load_cfm_metadata()

    # --------------------------------------------------------
    # 4. Vértice más cercano
    # --------------------------------------------------------

    result = calculate_nearest_fault_features(
        earthquakes=earthquakes,
        vertices=vertices,
    )

    # --------------------------------------------------------
    # 5. Proximidad
    # --------------------------------------------------------

    result = calculate_fault_proximity_counts(
        earthquakes=result,
        vertices=vertices,
    )

    # --------------------------------------------------------
    # 6. Metadata de la falla
    # --------------------------------------------------------

    result = attach_fault_metadata(
        earthquakes=result,
        metadata=metadata,
    )

    # --------------------------------------------------------
    # 7. Guardado
    # --------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print_header(
        "GUARDANDO FEATURES"
    )

    result.to_parquet(
        OUTPUT_PARQUET,
        index=False,
    )

    print(
        f"Parquet:\n  {OUTPUT_PARQUET}"
    )

    result.to_csv(
        OUTPUT_CSV,
        index=False,
    )

    print(
        f"CSV:\n  {OUTPUT_CSV}"
    )

    # --------------------------------------------------------
    # 8. Reporte
    # --------------------------------------------------------

    report = build_report(
        result=result,
        vertices=vertices,
    )

    REPORT_FILE.write_text(
        report,
        encoding="utf-8",
    )

    print(
        f"Report:\n  {REPORT_FILE}"
    )

    # --------------------------------------------------------
    # 9. Resumen
    # --------------------------------------------------------

    print_header(
        "RESUMEN FINAL"
    )

    print(
        f"Terremotos procesados: "
        f"{len(result):,}"
    )

    print(
        "Feature principal:"
    )

    print(
        "  cfm_distance_nearest_vertex_km"
    )

    print(
        "Features de proximidad:"
    )

    for radius in RADII_KM:

        print(
            f"  cfm_vertex_count_within_"
            f"{int(radius)}km"
        )

    print()

    print(
        "IMPORTANTE:"
    )

    print(
        "La distancia es al vértice CFM más cercano,"
    )

    print(
        "no todavía a la superficie triangular 3D."
    )

    print()

    print(
        "Proceso completado correctamente."
    )


if __name__ == "__main__":
    main()
