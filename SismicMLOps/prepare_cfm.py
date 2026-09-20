"""
prepare_cfm.py

Preparación e inspección del SCEC Community Fault Model (CFM6.0)
para su posterior integración con earthquakes.csv.

Objetivos de esta primera versión:

1. Localizar el archivo ZIP del CFM6.0.
2. Extraerlo si todavía no está extraído.
3. Localizar:
      - CFM6.0_Metadata.xlsx
      - preferred/1000m/*.ts
4. Leer las superficies Gocad TSurf.
5. Extraer sus vértices (VRTX) y triángulos (TRGL).
6. Convertir las coordenadas X/Y del CFM:
      UTM Zone 11 / NAD27
   a:
      WGS84 longitude / latitude
7. Generar datasets CSV/Parquet para inspección.
8. Generar un informe de control de calidad.

IMPORTANTE
----------
Esta herramienta NO calcula todavía la distancia entre terremotos
y fallas. Primero necesitamos verificar que la geometría y las
coordenadas están correctamente preparadas.

El siguiente paso será construir las features espaciales para XGBoost.
"""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from pyproj import Transformer
except ImportError:
    print(
        "ERROR: falta pyproj.\n"
        "Instálalo con:\n"
        "    pip install pyproj"
    )
    sys.exit(1)


# ============================================================
# CONFIGURACIÓN
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent

DATA_DIR = PROJECT_ROOT / "data"

CFM_DIR = DATA_DIR / "external" / "CFM6"

CFM_EXTRACTED_DIR = CFM_DIR / "extracted"

OUTPUT_DIR = DATA_DIR / "processed" / "cfm"

METADATA_OUTPUT = OUTPUT_DIR / "cfm_metadata_clean.csv"

VERTICES_OUTPUT = OUTPUT_DIR / "cfm_vertices_1000m.csv"

TRIANGLES_OUTPUT = OUTPUT_DIR / "cfm_triangles_1000m.csv"

REPORT_OUTPUT = OUTPUT_DIR / "cfm_quality_report.txt"


# CFM6.0 documenta las superficies TSurf en:
#
# UTM Zone 11
# NAD27
#
# EPSG:26711 = NAD27 / UTM zone 11N
#
# El catálogo de terremotos normalmente utiliza WGS84.
#
# Transformaremos:
#
# EPSG:26711 -> EPSG:4326
#
CFM_CRS = "EPSG:26711"
EARTHQUAKE_CRS = "EPSG:4326"


# ============================================================
# UTILIDADES
# ============================================================


def print_header(title: str) -> None:
    """Imprime un encabezado legible."""
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def find_zip_file() -> Path | None:
    """
    Busca archivos ZIP relacionados con CFM dentro de data/external/CFM6.

    También permite que el usuario coloque directamente el ZIP en
    data/external/CFM6/.
    """

    if not CFM_DIR.exists():
        return None

    zip_files = sorted(CFM_DIR.glob("*.zip"))

    if not zip_files:
        return None

    # Preferimos nombres que contengan CFM.
    cfm_zips = [
        path
        for path in zip_files
        if "cfm" in path.name.lower()
    ]

    if cfm_zips:
        return cfm_zips[0]

    return zip_files[0]


def find_metadata_file() -> Path | None:
    """Busca CFM6.0_Metadata.xlsx dentro del directorio CFM."""

    candidates = list(CFM_DIR.rglob("CFM6.0_Metadata.xlsx"))

    if not candidates:
        candidates = list(CFM_DIR.rglob("*Metadata*.xlsx"))

    if not candidates:
        return None

    return candidates[0]


def find_1000m_directory() -> Path | None:
    """
    Busca el directorio preferred/1000m.

    El CFM puede quedar dentro de un directorio adicional después
    de extraer el ZIP, por eso se utiliza rglob().
    """

    candidates = [
        path
        for path in CFM_DIR.rglob("1000m")
        if path.is_dir()
        and "preferred" in str(path).lower()
    ]

    if not candidates:
        return None

    return candidates[0]


def extract_cfm_zip(zip_path: Path) -> Path:
    """
    Extrae el ZIP del CFM si todavía no existe la extracción.

    Devuelve el directorio de extracción.
    """

    if CFM_EXTRACTED_DIR.exists():
        existing_files = list(CFM_EXTRACTED_DIR.rglob("*"))

        if existing_files:
            print(
                f"El CFM ya parece estar extraído en:\n"
                f"  {CFM_EXTRACTED_DIR}"
            )
            return CFM_EXTRACTED_DIR

    CFM_EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Extrayendo:\n  {zip_path}")
    print(f"Destino:\n  {CFM_EXTRACTED_DIR}")

    with zipfile.ZipFile(zip_path, "r") as archive:
        archive.extractall(CFM_EXTRACTED_DIR)

    print("Extracción completada.")

    return CFM_EXTRACTED_DIR


# ============================================================
# LOCALIZACIÓN DE LOS DATOS
# ============================================================


def prepare_cfm_directory() -> None:
    """
    Comprueba si el CFM ya está disponible.

    Si existe un ZIP pero no los archivos extraídos, lo extrae.
    """

    CFM_DIR.mkdir(parents=True, exist_ok=True)

    metadata = find_metadata_file()
    ts_dir = find_1000m_directory()

    if metadata is not None and ts_dir is not None:
        print("CFM encontrado sin necesidad de extracción.")
        return

    zip_path = find_zip_file()

    if zip_path is None:
        raise FileNotFoundError(
            "\nNo se encontró un ZIP del CFM.\n\n"
            "Coloca el archivo ZIP del CFM6.0 en:\n"
            f"  {CFM_DIR}\n\n"
            "Por ejemplo:\n"
            f"  {CFM_DIR}/CFM6.0_release.zip\n"
        )

    extract_cfm_zip(zip_path)


# ============================================================
# LECTURA TSurf
# ============================================================


VRTX_PATTERN = re.compile(
    r"^\s*VRTX\s+(\d+)\s+"
    r"([-+0-9.eE]+)\s+"
    r"([-+0-9.eE]+)\s+"
    r"([-+0-9.eE]+)"
)

TRGL_PATTERN = re.compile(
    r"^\s*TRGL\s+(\d+)\s+(\d+)\s+(\d+)"
)


def parse_tsurf(ts_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Lee un archivo Gocad TSurf.

    Devuelve:

    vertices:
        vertex_id
        x
        y
        z

    triangles:
        triangle_id
        v1
        v2
        v3
    """

    vertices: list[dict] = []
    triangles: list[dict] = []

    triangle_id = 0

    with ts_path.open("r", encoding="utf-8", errors="ignore") as file:
        for line in file:

            vertex_match = VRTX_PATTERN.match(line)

            if vertex_match:
                vertex_id = int(vertex_match.group(1))
                x = float(vertex_match.group(2))
                y = float(vertex_match.group(3))
                z = float(vertex_match.group(4))

                vertices.append(
                    {
                        "vertex_id": vertex_id,
                        "x": x,
                        "y": y,
                        "z": z,
                    }
                )

                continue

            triangle_match = TRGL_PATTERN.match(line)

            if triangle_match:
                triangle_id += 1

                triangles.append(
                    {
                        "triangle_id": triangle_id,
                        "v1": int(triangle_match.group(1)),
                        "v2": int(triangle_match.group(2)),
                        "v3": int(triangle_match.group(3)),
                    }
                )

    vertices_df = pd.DataFrame(vertices)
    triangles_df = pd.DataFrame(triangles)

    return vertices_df, triangles_df


# ============================================================
# CONVERSIÓN DE COORDENADAS
# ============================================================


def convert_vertices_to_wgs84(vertices: pd.DataFrame) -> pd.DataFrame:
    """
    Convierte:

        UTM Zone 11 / NAD27

    a:

        WGS84 latitude / longitude.
    """

    transformer = Transformer.from_crs(
        CFM_CRS,
        EARTHQUAKE_CRS,
        always_xy=True,
    )

    longitude, latitude = transformer.transform(
        vertices["x"].to_numpy(),
        vertices["y"].to_numpy(),
    )

    result = vertices.copy()

    result["longitude"] = longitude
    result["latitude"] = latitude

    # El CFM utiliza Z como coordenada vertical.
    #
    # En las superficies de falla los valores negativos representan
    # profundidad bajo el nivel de referencia.
    #
    # Conservamos el valor original y añadimos una columna de
    # profundidad positiva para facilitar la integración posterior
    # con earthquakes.csv.
    result["elevation_or_depth_m"] = result["z"]

    result["depth_km"] = -result["z"] / 1000.0

    return result


# ============================================================
# METADATA
# ============================================================


def load_metadata(metadata_path: Path) -> pd.DataFrame:
    """
    Lee el Excel de metadata del CFM.

    No asumimos todavía nombres exactos de columnas.
    """

    print(f"Leyendo metadata:\n  {metadata_path}")

    excel = pd.ExcelFile(metadata_path)

    print("Hojas encontradas:")
    for sheet in excel.sheet_names:
        print(f"  - {sheet}")

    # Buscamos una hoja que parezca contener la tabla principal.
    preferred_sheet = None

    for sheet in excel.sheet_names:
        normalized = sheet.lower()

        if (
            "preferred" in normalized
            or "metadata" in normalized
            or "fault" in normalized
        ):
            preferred_sheet = sheet
            break

    if preferred_sheet is None:
        preferred_sheet = excel.sheet_names[0]

    print(f"Hoja seleccionada: {preferred_sheet}")

    metadata = pd.read_excel(
        metadata_path,
        sheet_name=preferred_sheet,
    )

    # Eliminamos filas completamente vacías.
    metadata = metadata.dropna(
        how="all"
    ).reset_index(drop=True)

    # Normalizamos nombres de columnas.
    metadata.columns = [
        str(column).strip()
        for column in metadata.columns
    ]

    return metadata


# ============================================================
# NOMBRE DE FALLA
# ============================================================


def infer_fault_name(ts_path: Path) -> str:
    """
    Intenta obtener un identificador estable a partir del nombre
    del archivo TSurf.

    No intentamos modificar el nombre porque CFM utiliza una
    nomenclatura jerárquica que debemos conservar.
    """

    return ts_path.stem


# ============================================================
# PROCESAMIENTO DE TODAS LAS SUPERFICIES
# ============================================================


def process_surfaces(ts_directory: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Procesa todas las superficies .ts de preferred/1000m.

    Genera dos tablas:

    vertices:
        todos los VRTX

    triangles:
        todos los TRGL
    """

    ts_files = sorted(ts_directory.glob("*.ts"))

    if not ts_files:
        raise FileNotFoundError(
            f"No se encontraron archivos .ts en:\n"
            f"  {ts_directory}"
        )

    print()
    print(f"Superficies .ts encontradas: {len(ts_files)}")

    all_vertices: list[pd.DataFrame] = []
    all_triangles: list[pd.DataFrame] = []

    for index, ts_path in enumerate(ts_files, start=1):

        fault_name = infer_fault_name(ts_path)

        print(
            f"[{index:03d}/{len(ts_files):03d}] "
            f"{fault_name}"
        )

        vertices, triangles = parse_tsurf(ts_path)

        if vertices.empty:
            print("    ADVERTENCIA: sin VRTX")
            continue

        vertices["fault_name"] = fault_name

        triangles["fault_name"] = fault_name

        vertices = convert_vertices_to_wgs84(
            vertices
        )

        all_vertices.append(vertices)
        all_triangles.append(triangles)

    if not all_vertices:
        raise RuntimeError(
            "No se pudieron extraer vértices de ninguna superficie."
        )

    vertices_df = pd.concat(
        all_vertices,
        ignore_index=True,
    )

    triangles_df = pd.concat(
        all_triangles,
        ignore_index=True,
    )

    return vertices_df, triangles_df


# ============================================================
# CONTROL DE CALIDAD
# ============================================================


def build_quality_report(
    metadata: pd.DataFrame,
    vertices: pd.DataFrame,
    triangles: pd.DataFrame,
    ts_directory: Path,
) -> str:
    """Construye un informe de control de calidad."""

    lines: list[str] = []

    lines.append(
        "CFM6.0 DATA PREPARATION - QUALITY REPORT"
    )
    lines.append("=" * 70)
    lines.append("")

    lines.append(
        f"TSurf directory: {ts_directory}"
    )

    lines.append(
        f"Number of fault surfaces: "
        f"{vertices['fault_name'].nunique()}"
    )

    lines.append(
        f"Number of vertices: {len(vertices):,}"
    )

    lines.append(
        f"Number of triangles: {len(triangles):,}"
    )

    lines.append("")

    lines.append("Coordinate system:")
    lines.append(
        f"  Source: {CFM_CRS} "
        "(UTM Zone 11 / NAD27)"
    )
    lines.append(
        f"  Output: {EARTHQUAKE_CRS} "
        "(WGS84)"
    )

    lines.append("")

    lines.append("Longitude:")
    lines.append(
        f"  min = {vertices['longitude'].min():.6f}"
    )
    lines.append(
        f"  max = {vertices['longitude'].max():.6f}"
    )

    lines.append("Latitude:")
    lines.append(
        f"  min = {vertices['latitude'].min():.6f}"
    )
    lines.append(
        f"  max = {vertices['latitude'].max():.6f}"
    )

    lines.append("")

    lines.append("Vertical coordinate:")
    lines.append(
        f"  Z min = {vertices['z'].min():.2f} m"
    )
    lines.append(
        f"  Z max = {vertices['z'].max():.2f} m"
    )

    lines.append("Depth:")
    lines.append(
        f"  min = {vertices['depth_km'].min():.3f} km"
    )
    lines.append(
        f"  max = {vertices['depth_km'].max():.3f} km"
    )

    lines.append("")

    lines.append("Missing values:")
    for column in [
        "x",
        "y",
        "z",
        "longitude",
        "latitude",
        "depth_km",
    ]:
        missing = int(
            vertices[column].isna().sum()
        )

        lines.append(
            f"  {column}: {missing}"
        )

    lines.append("")

    lines.append("Metadata:")
    lines.append(
        f"  rows = {len(metadata):,}"
    )
    lines.append(
        f"  columns = {len(metadata.columns):,}"
    )

    lines.append("")

    lines.append("Metadata columns:")
    for column in metadata.columns:
        lines.append(
            f"  - {column}"
        )

    lines.append("")

    lines.append(
        "This is an inspection/preparation stage."
    )

    lines.append(
        "No earthquake-to-fault distance has been calculated yet."
    )

    return "\n".join(lines)


# ============================================================
# GUARDADO
# ============================================================


def save_outputs(
    metadata: pd.DataFrame,
    vertices: pd.DataFrame,
    triangles: pd.DataFrame,
    report: str,
) -> None:
    """Guarda todos los resultados."""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print_header("GUARDANDO RESULTADOS")

    metadata.to_csv(
        METADATA_OUTPUT,
        index=False,
    )

    print(
        f"Metadata:\n  {METADATA_OUTPUT}"
    )

    vertices.to_csv(
        VERTICES_OUTPUT,
        index=False,
    )

    print(
        f"Vertices:\n  {VERTICES_OUTPUT}"
    )

    triangles.to_csv(
        TRIANGLES_OUTPUT,
        index=False,
    )

    print(
        f"Triangles:\n  {TRIANGLES_OUTPUT}"
    )

    REPORT_OUTPUT.write_text(
        report,
        encoding="utf-8",
    )

    print(
        f"Quality report:\n  {REPORT_OUTPUT}"
    )


# ============================================================
# MAIN
# ============================================================


def main() -> None:
    """Ejecuta todo el proceso."""

    parser = argparse.ArgumentParser(
        description=(
            "Prepara las superficies CFM6.0 preferred/1000m "
            "para su integración posterior con earthquakes.csv."
        )
    )

    args = parser.parse_args()

    del args

    print_header(
        "CFM6.0 DATA PREPARATION"
    )

    print(
        f"Project root:\n  {PROJECT_ROOT}"
    )

    print(
        f"CFM directory:\n  {CFM_DIR}"
    )

    # --------------------------------------------------------
    # 1. Preparar directorio
    # --------------------------------------------------------

    prepare_cfm_directory()

    # --------------------------------------------------------
    # 2. Localizar metadata
    # --------------------------------------------------------

    metadata_path = find_metadata_file()

    if metadata_path is None:
        raise FileNotFoundError(
            "\nNo se encontró CFM6.0_Metadata.xlsx.\n"
            f"Busca el archivo dentro de:\n  {CFM_DIR}"
        )

    # --------------------------------------------------------
    # 3. Localizar preferred/1000m
    # --------------------------------------------------------

    ts_directory = find_1000m_directory()

    if ts_directory is None:
        raise FileNotFoundError(
            "\nNo se encontró preferred/1000m.\n"
            f"Busca la estructura del CFM dentro de:\n  {CFM_DIR}"
        )

    print_header("ARCHIVOS CFM DETECTADOS")

    print(
        f"Metadata:\n  {metadata_path}"
    )

    print(
        f"1000m surfaces:\n  {ts_directory}"
    )

    # --------------------------------------------------------
    # 4. Metadata
    # --------------------------------------------------------

    metadata = load_metadata(
        metadata_path
    )

    print(
        f"Filas de metadata: {len(metadata):,}"
    )

    print(
        f"Columnas de metadata: {len(metadata.columns):,}"
    )

    # --------------------------------------------------------
    # 5. Superficies
    # --------------------------------------------------------

    print_header(
        "PROCESANDO SUPERFICIES TSurf"
    )

    vertices, triangles = process_surfaces(
        ts_directory
    )

    # --------------------------------------------------------
    # 6. Quality report
    # --------------------------------------------------------

    report = build_quality_report(
        metadata=metadata,
        vertices=vertices,
        triangles=triangles,
        ts_directory=ts_directory,
    )

    # --------------------------------------------------------
    # 7. Guardar
    # --------------------------------------------------------

    save_outputs(
        metadata=metadata,
        vertices=vertices,
        triangles=triangles,
        report=report,
    )

    # --------------------------------------------------------
    # 8. Resumen final
    # --------------------------------------------------------

    print_header("RESUMEN")

    print(
        f"Superficies: "
        f"{vertices['fault_name'].nunique():,}"
    )

    print(
        f"Vertices: "
        f"{len(vertices):,}"
    )

    print(
        f"Triángulos: "
        f"{len(triangles):,}"
    )

    print()

    print(
        "Conversión de coordenadas:"
    )

    print(
        "  CFM: UTM Zone 11 / NAD27"
    )

    print(
        "  salida: WGS84 latitude/longitude"
    )

    print()

    print(
        "Preparación CFM completada."
    )

    print(
        "Todavía NO se han calculado distancias "
        "entre terremotos y fallas."
    )

    print()

    print(
        "Siguiente paso:"
    )

    print(
        "  relacionar earthquakes.csv con las "
        "superficies CFM mediante geometría espacial."
    )


if __name__ == "__main__":
    main()
