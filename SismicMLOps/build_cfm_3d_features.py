"""
Build 3D earthquake-to-CFM surface distance features.

This module calculates the minimum 3D distance between earthquake
hypocenters and CFM6.0 triangular fault surfaces.

Important:
- CFM vertices are not treated as the final geological surface.
- Earthquakes are converted to the CFM coordinate system.
- Triangle centroids are indexed with scipy.spatial.cKDTree.
- Exact point-to-triangle distance is then calculated for candidate
  triangles.
- The script reports convergence for different candidate K values.

This is a feature-engineering stage.
It does NOT train the XGBoost model.
"""

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy.spatial import cKDTree


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent

EARTHQUAKE_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "cfm"
    / "earthquakes_cfm_features.parquet"
)

CFM_VERTICES_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "cfm"
    / "cfm_vertices_1000m.csv"
)

CFM_TRIANGLES_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "cfm"
    / "cfm_triangles_1000m.csv"
)

CFM_METADATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "cfm"
    / "cfm_metadata_clean.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "cfm"
    / "earthquakes_cfm_3d_features.parquet"
)

REPORT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "cfm"
    / "cfm_3d_feature_report.txt"
)


# Number of triangle-centroid candidates examined for each
# earthquake.

# We deliberately use several values so that we can test whether
# the calculated minimum distance is stable.
CANDIDATE_K_VALUES = [8, 16, 32, 64]

# Final K used for the production feature.
FINAL_CANDIDATE_K = 64

# Process earthquakes in batches to control RAM usage.
BATCH_SIZE = 5000

# Coordinate systems:
#
# CFM6.0 vertices were previously converted from:
# EPSG:26711 = NAD27 / UTM zone 11N
#
# The earthquake longitude/latitude values are WGS84.
#
# Therefore we transform earthquake coordinates into the same
# projected horizontal CRS used by the CFM vertices.
SOURCE_EARTHQUAKE_CRS = "EPSG:4326"
CFM_HORIZONTAL_CRS = "EPSG:26711"

TRANSFORMER = Transformer.from_crs(
    SOURCE_EARTHQUAKE_CRS,
    CFM_HORIZONTAL_CRS,
    always_xy=True,
)


# ============================================================
# GENERAL UTILITIES
# ============================================================

def print_header(title: str) -> None:
    """Print a visible section header."""
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def find_column(
    dataframe: pd.DataFrame,
    candidates: list[str],
    description: str,
) -> str:
    """
    Find the first available column from a list of candidates.

    Raises:
        ValueError: if none of the candidate columns exist.
    """
    for candidate in candidates:
        if candidate in dataframe.columns:
            return candidate

    raise ValueError(
        f"Could not find {description}.\n"
        f"Expected one of: {candidates}\n"
        f"Available columns: {list(dataframe.columns)}"
    )


# ============================================================
# LOAD EARTHQUAKES
# ============================================================

def load_earthquakes() -> pd.DataFrame:
    """Load the earthquake catalog enriched with preliminary CFM features."""

    print_header("Loading earthquake catalog")

    if not EARTHQUAKE_FILE.exists():
        raise FileNotFoundError(
            f"Earthquake feature file not found:\n{EARTHQUAKE_FILE}"
        )

    earthquakes = pd.read_parquet(EARTHQUAKE_FILE)

    print(f"File: {EARTHQUAKE_FILE}")
    print(f"Rows: {len(earthquakes):,}")
    print(f"Columns: {len(earthquakes.columns)}")

    lon_col = find_column(
        earthquakes,
        ["longitude", "lon", "Longitude"],
        "longitude",
    )

    lat_col = find_column(
        earthquakes,
        ["latitude", "lat", "Latitude"],
        "latitude",
    )

    depth_col = find_column(
        earthquakes,
        ["depth_km", "depth", "Depth"],
        "earthquake depth",
    )

    earthquakes = earthquakes.copy()

    # Normalize names internally.
    earthquakes["_longitude"] = pd.to_numeric(
        earthquakes[lon_col],
        errors="coerce",
    )

    earthquakes["_latitude"] = pd.to_numeric(
        earthquakes[lat_col],
        errors="coerce",
    )

    earthquakes["_depth_km"] = pd.to_numeric(
        earthquakes[depth_col],
        errors="coerce",
    )

    print(f"Longitude column: {lon_col}")
    print(f"Latitude column:  {lat_col}")
    print(f"Depth column:     {depth_col}")

    valid = (
        earthquakes["_longitude"].notna()
        & earthquakes["_latitude"].notna()
        & earthquakes["_depth_km"].notna()
    )

    print(f"Valid 3D coordinates: {valid.sum():,}")
    print(f"Missing 3D coordinates: {(~valid).sum():,}")

    return earthquakes


# ============================================================
# LOAD CFM VERTICES
# ============================================================

def load_cfm_vertices() -> pd.DataFrame:
    """Load previously prepared CFM vertices."""

    print_header("Loading CFM vertices")

    if not CFM_VERTICES_FILE.exists():
        raise FileNotFoundError(
            f"CFM vertices file not found:\n{CFM_VERTICES_FILE}"
        )

    vertices = pd.read_csv(CFM_VERTICES_FILE)

    print(f"File: {CFM_VERTICES_FILE}")
    print(f"Vertices: {len(vertices):,}")
    print(f"Columns: {list(vertices.columns)}")

    required = ["x", "y", "z"]

    missing = [
        column
        for column in required
        if column not in vertices.columns
    ]

    if missing:
        raise ValueError(
            "CFM vertex file is missing required columns: "
            f"{missing}"
        )

    vertices = vertices.copy()

    vertices["x"] = pd.to_numeric(vertices["x"], errors="coerce")
    vertices["y"] = pd.to_numeric(vertices["y"], errors="coerce")
    vertices["z"] = pd.to_numeric(vertices["z"], errors="coerce")

    valid = vertices[["x", "y", "z"]].notna().all(axis=1)

    print(f"Valid 3D vertices: {valid.sum():,}")
    print(f"Invalid 3D vertices: {(~valid).sum():,}")

    vertices = vertices.loc[valid].reset_index(drop=True)

    return vertices


# ============================================================
# LOAD CFM TRIANGLES
# ============================================================

def load_cfm_triangles() -> pd.DataFrame:
    """Load the CFM triangular surface topology."""

    print_header("Loading CFM triangles")

    if not CFM_TRIANGLES_FILE.exists():
        raise FileNotFoundError(
            f"CFM triangles file not found:\n{CFM_TRIANGLES_FILE}"
        )

    triangles = pd.read_csv(CFM_TRIANGLES_FILE)

    print(f"File: {CFM_TRIANGLES_FILE}")
    print(f"Triangles: {len(triangles):,}")
    print(f"Columns: {list(triangles.columns)}")

    return triangles


# ============================================================
# IDENTIFY TRIANGLE VERTEX COLUMNS
# ============================================================

def identify_triangle_columns(
    triangles: pd.DataFrame,
) -> tuple[str, str, str]:
    """
    Identify the three vertex-reference columns.

    The exact names depend on how prepare_cfm.py wrote the
    triangle file, so several common naming conventions are
    supported.
    """

    candidate_sets = [
        ("v1", "v2", "v3"),
        ("vertex1", "vertex2", "vertex3"),
        ("vertex_1", "vertex_2", "vertex_3"),
        ("VRTX1", "VRTX2", "VRTX3"),
        ("vertex_a", "vertex_b", "vertex_c"),
    ]

    for columns in candidate_sets:
        if all(column in triangles.columns for column in columns):
            print(
                "Triangle vertex columns detected:",
                columns,
            )
            return columns

    raise ValueError(
        "Could not identify triangle vertex-reference columns.\n"
        "Available columns:\n"
        f"{list(triangles.columns)}\n\n"
        "Expected one of these patterns:\n"
        "v1,v2,v3\n"
        "vertex1,vertex2,vertex3\n"
        "vertex_1,vertex_2,vertex_3\n"
        "VRTX1,VRTX2,VRTX3"
    )

# ============================================================
# BUILD TRIANGLE GEOMETRY
# ============================================================

def build_triangle_geometry(
    vertices: pd.DataFrame,
    triangles: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Construct triangle vertex coordinates and triangle centroids.

    Returns:
        triangle_vertices:
            Shape (N, 3, 3)
            N triangles × 3 vertices × XYZ

        triangle_centroids:
            Shape (N, 3)
            XYZ centroid for every triangle.
    """

    print_header("Building 3D triangle geometry")

    v1_col, v2_col, v3_col = identify_triangle_columns(triangles)

    v1 = pd.to_numeric(triangles[v1_col], errors="coerce")
    v2 = pd.to_numeric(triangles[v2_col], errors="coerce")
    v3 = pd.to_numeric(triangles[v3_col], errors="coerce")

    # Convert to integer vertex indices.
    #
    # The prepare_cfm.py pipeline normally stores vertex references
    # as zero-based indices. We verify this below.

    v1 = v1.to_numpy(dtype=np.float64)
    v2 = v2.to_numpy(dtype=np.float64)
    v3 = v3.to_numpy(dtype=np.float64)

    valid_reference = (
        np.isfinite(v1)
        & np.isfinite(v2)
        & np.isfinite(v3)
    )

    print(
        "Triangles with valid vertex references:",
        int(valid_reference.sum()),
        f"/ {len(triangles):,}",
    )

    triangles_valid = triangles.loc[valid_reference].copy()

    v1 = v1[valid_reference].astype(np.int64)
    v2 = v2[valid_reference].astype(np.int64)
    v3 = v3[valid_reference].astype(np.int64)

    vertex_count = len(vertices)

    if (
        v1.min() < 0
        or v2.min() < 0
        or v3.min() < 0
        or v1.max() >= vertex_count
        or v2.max() >= vertex_count
        or v3.max() >= vertex_count
    ):
        raise ValueError(
            "Triangle vertex references do not match the loaded "
            "vertex table.\n"
            f"Vertex count: {vertex_count:,}\n"
            f"Reference ranges: "
            f"v1={v1.min()}..{v1.max()}, "
            f"v2={v2.min()}..{v2.max()}, "
            f"v3={v3.min()}..{v3.max()}"
        )

    xyz = vertices[["x", "y", "z"]].to_numpy(
        dtype=np.float64
    )

    triangle_vertices = np.stack(
        [
            xyz[v1],
            xyz[v2],
            xyz[v3],
        ],
        axis=1,
    )

    triangle_centroids = triangle_vertices.mean(axis=1)

    print(
        f"Triangle geometry created: "
        f"{len(triangle_vertices):,}"
    )

    print(
        "Triangle coordinate array shape:",
        triangle_vertices.shape,
    )

    print(
        "Triangle centroid array shape:",
        triangle_centroids.shape,
    )

    return triangle_vertices, triangle_centroids


# ============================================================
# BUILD CENTROID KD-TREE
# ============================================================

def build_centroid_tree(
    triangle_centroids: np.ndarray,
) -> cKDTree:
    """Build a KD-tree from 3D triangle centroids."""

    print_header("Building 3D triangle centroid KD-tree")

    tree = cKDTree(triangle_centroids)

    print(
        f"KD-tree contains "
        f"{len(triangle_centroids):,} triangle centroids."
    )

    return tree


# ============================================================
# EARTHQUAKE COORDINATES
# ============================================================

def earthquake_coordinates_3d(
    earthquakes: pd.DataFrame,
) -> np.ndarray:
    """
    Convert earthquake longitude/latitude/depth to the same
    approximate 3D coordinate system as the CFM.

    Horizontal:
        WGS84 longitude/latitude -> EPSG:26711

    Vertical:
        earthquake depth is assumed positive downward,
        therefore:

            z = -depth_km * 1000

    Important:
        The CFM z datum and earthquake depth datum are not being
        claimed to be geodetically identical here. This is a
        practical geological 3D feature representation.
    """

    print_header("Converting earthquake hypocenters to 3D coordinates")

    lon = earthquakes["_longitude"].to_numpy(dtype=np.float64)
    lat = earthquakes["_latitude"].to_numpy(dtype=np.float64)
    depth_km = earthquakes["_depth_km"].to_numpy(dtype=np.float64)

    valid = (
        np.isfinite(lon)
        & np.isfinite(lat)
        & np.isfinite(depth_km)
    )

    x = np.full(len(earthquakes), np.nan)
    y = np.full(len(earthquakes), np.nan)
    z = np.full(len(earthquakes), np.nan)

    transformed_x, transformed_y = TRANSFORMER.transform(
        lon[valid],
        lat[valid],
    )

    x[valid] = transformed_x
    y[valid] = transformed_y

    # Positive earthquake depth = below surface.
    z[valid] = -depth_km[valid] * 1000.0

    coordinates = np.column_stack([x, y, z])

    print(
        f"Valid hypocenters converted: {valid.sum():,}"
    )

    if valid.any():
        print(
            "Earthquake X range:",
            f"{np.nanmin(x):.2f} -> {np.nanmax(x):.2f} m",
        )
        print(
            "Earthquake Y range:",
            f"{np.nanmin(y):.2f} -> {np.nanmax(y):.2f} m",
        )
        print(
            "Earthquake Z range:",
            f"{np.nanmin(z):.2f} -> {np.nanmax(z):.2f} m",
        )

    return coordinates


# ============================================================
# POINT TO TRIANGLE DISTANCE
# ============================================================

def point_to_triangle_distance_squared(
    point: np.ndarray,
    triangle: np.ndarray,
) -> float:
    """
    Calculate the exact Euclidean distance squared from one 3D
    point to one triangle.

    triangle shape:
        (3, 3)

    Uses the standard closest-point-on-triangle region tests.
    """

    a = triangle[0]
    b = triangle[1]
    c = triangle[2]

    ab = b - a
    ac = c - a
    ap = point - a

    d1 = np.dot(ab, ap)
    d2 = np.dot(ac, ap)

    # Vertex A region.
    if d1 <= 0.0 and d2 <= 0.0:
        diff = point - a
        return float(np.dot(diff, diff))

    bp = point - b

    d3 = np.dot(ab, bp)
    d4 = np.dot(ac, bp)

    # Vertex B region.
    if d3 >= 0.0 and d4 <= d3:
        diff = point - b
        return float(np.dot(diff, diff))

    vc = d1 * d4 - d3 * d2

    # Edge AB region.
    if vc <= 0.0 and d1 >= 0.0 and d3 <= 0.0:
        denominator = d1 - d3

        if denominator == 0.0:
            diff = point - a
            return float(np.dot(diff, diff))

        v = d1 / denominator
        closest = a + v * ab
        diff = point - closest

        return float(np.dot(diff, diff))

    cp = point - c

    d5 = np.dot(ab, cp)
    d6 = np.dot(ac, cp)

    # Vertex C region.
    if d6 >= 0.0 and d5 <= d6:
        diff = point - c
        return float(np.dot(diff, diff))

    vb = d5 * d2 - d1 * d6

    # Edge AC region.
    if vb <= 0.0 and d2 >= 0.0 and d6 <= 0.0:
        denominator = d2 - d6

        if denominator == 0.0:
            diff = point - a
            return float(np.dot(diff, diff))

        w = d2 / denominator
        closest = a + w * ac
        diff = point - closest

        return float(np.dot(diff, diff))

    va = d3 * d6 - d5 * d4

    # Edge BC region.
    if va <= 0.0 and (d4 - d3) >= 0.0 and (d5 - d6) >= 0.0:
        denominator = (d4 - d3) + (d5 - d6)

        if denominator == 0.0:
            diff = point - b
            return float(np.dot(diff, diff))

        w = (d4 - d3) / denominator

        closest = b + w * (c - b)
        diff = point - closest

        return float(np.dot(diff, diff))

    # Inside triangle region.
    denominator = va + vb + vc

    if denominator == 0.0:
        # Degenerate triangle.
        distances = [
            np.sum((point - a) ** 2),
            np.sum((point - b) ** 2),
            np.sum((point - c) ** 2),
        ]

        return float(min(distances))

    v = vb / denominator
    w = vc / denominator

    closest = a + ab * v + ac * w

    diff = point - closest

    return float(np.dot(diff, diff))

# ============================================================
# DISTANCE TO CANDIDATE TRIANGLES
# ============================================================

def calculate_distance_for_point(
    point: np.ndarray,
    candidate_indices: np.ndarray,
    triangle_vertices: np.ndarray,
) -> tuple[float, int]:
    """
    Calculate the minimum exact point-to-triangle distance among
    the supplied candidate triangles.

    Returns:
        distance_km
        triangle_index
    """

    best_distance_squared = np.inf
    best_triangle = -1

    for triangle_index in candidate_indices:
        triangle = triangle_vertices[triangle_index]

        distance_squared = point_to_triangle_distance_squared(
            point,
            triangle,
        )

        if distance_squared < best_distance_squared:
            best_distance_squared = distance_squared
            best_triangle = int(triangle_index)

    if best_triangle < 0:
        return np.nan, -1

    distance_km = np.sqrt(best_distance_squared) / 1000.0

    return float(distance_km), best_triangle


# ============================================================
# PROCESS ONE K VALUE
# ============================================================

def process_candidate_k(
    earthquake_coordinates: np.ndarray,
    tree: cKDTree,
    triangle_vertices: np.ndarray,
    k: int,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Calculate point-to-triangle distances using K nearest triangle
    centroids as candidates.
    """

    print()
    print(f"Processing candidate K = {k}")

    n = len(earthquake_coordinates)

    distances = np.full(n, np.nan)
    triangle_ids = np.full(n, -1, dtype=np.int64)

    valid_indices = np.where(
        np.isfinite(earthquake_coordinates).all(axis=1)
    )[0]

    for start in range(0, len(valid_indices), BATCH_SIZE):

        batch_indices = valid_indices[
            start:start + BATCH_SIZE
        ]

        points = earthquake_coordinates[batch_indices]

        _, candidate_indices = tree.query(
            points,
            k=k,
        )

        if k == 1:
            candidate_indices = candidate_indices[:, None]

        for local_index, earthquake_index in enumerate(
            batch_indices
        ):
            candidates = candidate_indices[local_index]

            distance_km, triangle_index = (
                calculate_distance_for_point(
                    points[local_index],
                    candidates,
                    triangle_vertices,
                )
            )

            distances[earthquake_index] = distance_km
            triangle_ids[earthquake_index] = triangle_index

        processed = min(
            start + len(batch_indices),
            len(valid_indices),
        )

        if (
            processed % (BATCH_SIZE * 10) == 0
            or processed == len(valid_indices)
        ):
            print(
                f"  processed "
                f"{processed:,}/{len(valid_indices):,}"
            )

    return distances, triangle_ids


# ============================================================
# CONVERGENCE TEST
# ============================================================

def run_convergence_test(
    earthquake_coordinates: np.ndarray,
    tree: cKDTree,
    triangle_vertices: np.ndarray,
) -> dict[int, tuple[np.ndarray, np.ndarray]]:
    """
    Run the distance calculation for multiple K values.

    This is important because the centroid KD-tree is a candidate
    accelerator, not a mathematical proof that K=64 contains the
    globally nearest triangle.

    We therefore explicitly measure whether increasing K changes
    the result.
    """

    print_header("Running candidate-K convergence test")

    results = {}

    for k in CANDIDATE_K_VALUES:
        distances, triangle_ids = process_candidate_k(
            earthquake_coordinates,
            tree,
            triangle_vertices,
            k,
        )

        results[k] = (
            distances,
            triangle_ids,
        )

        valid = np.isfinite(distances)

        if valid.any():
            print(
                f"K={k}: "
                f"valid={valid.sum():,}, "
                f"median={np.nanmedian(distances):.4f} km, "
                f"mean={np.nanmean(distances):.4f} km, "
                f"max={np.nanmax(distances):.4f} km"
            )

    return results


# ============================================================
# BUILD CONVERGENCE REPORT
# ============================================================

def compare_k_results(
    results: dict[int, tuple[np.ndarray, np.ndarray]],
) -> dict:
    """Compare successive K values."""

    print_header("Comparing candidate-K results")

    sorted_k = sorted(results)

    comparison = {}

    for previous_k, current_k in zip(
        sorted_k[:-1],
        sorted_k[1:],
    ):
        previous_distance = results[previous_k][0]
        current_distance = results[current_k][0]

        valid = (
            np.isfinite(previous_distance)
            & np.isfinite(current_distance)
        )

        if not valid.any():
            comparison[
                f"{previous_k}_to_{current_k}"
            ] = {
                "changed_count": 0,
                "changed_percent": np.nan,
                "max_change_km": np.nan,
            }
            continue

        difference = np.abs(
            current_distance[valid]
            - previous_distance[valid]
        )

        changed = difference > 1e-9

        changed_count = int(changed.sum())
        changed_percent = (
            changed_count / valid.sum() * 100.0
        )

        max_change = float(
            difference.max()
        )

        comparison[
            f"{previous_k}_to_{current_k}"
        ] = {
            "changed_count": changed_count,
            "changed_percent": changed_percent,
            "max_change_km": max_change,
        }

        print(
            f"K {previous_k} -> K {current_k}: "
            f"changed={changed_count:,} "
            f"({changed_percent:.4f}%), "
            f"max change={max_change:.6f} km"
        )

    return comparison


# ============================================================
# ATTACH NEAREST-FAULT INFORMATION
# ============================================================

def attach_triangle_information(
    earthquakes: pd.DataFrame,
    triangles: pd.DataFrame,
    triangle_ids: np.ndarray,
) -> pd.DataFrame:
    """
    Attach triangle-level information to earthquake records.

    If the triangle file contains a fault-name/object-name column,
    preserve it.
    """

    result = earthquakes.copy()

    result["cfm_nearest_triangle_index"] = triangle_ids

    possible_fault_columns = [
        "fault_name",
        "Fault Name",
        "CFM6.0 Fault Object Name",
        "object_name",
        "name",
    ]

    fault_column: Optional[str] = None

    for column in possible_fault_columns:
        if column in triangles.columns:
            fault_column = column
            break

    if fault_column is not None:
        triangle_faults = (
            triangles[fault_column]
            .astype("string")
            .reset_index(drop=True)
        )

        valid = (
            triangle_ids >= 0
            & (triangle_ids < len(triangle_faults))
        )

        nearest_fault = pd.Series(
            pd.NA,
            index=result.index,
            dtype="string",
        )

        nearest_fault.loc[valid] = (
            triangle_faults.iloc[
                triangle_ids[valid]
            ].to_numpy()
        )

        result["cfm_nearest_fault_3d"] = nearest_fault

        print(
            f"Triangle fault column used: {fault_column}"
        )

    else:
        print(
            "WARNING: no fault-name column was found "
            "in the triangle file."
        )

    return result


# ============================================================
# REPORT
# ============================================================

def build_report(
    result: pd.DataFrame,
    triangle_vertices: np.ndarray,
    convergence: dict,
) -> str:
    """Build a human-readable quality report."""

    distance = result[
        "cfm_distance_3d_to_surface_km"
    ].to_numpy()

    valid = np.isfinite(distance)

    lines = []

    lines.append(
        "CFM6.0 3D EARTHQUAKE FEATURE REPORT"
    )
    lines.append("=" * 70)
    lines.append("")
    lines.append(
        f"Earthquakes processed: {len(result):,}"
    )
    lines.append(
        f"CFM triangles available: "
        f"{len(triangle_vertices):,}"
    )
    lines.append("")
    lines.append(
        "3D point-to-CFM-surface distance:"
    )
    lines.append(
        f"  valid: {valid.sum():,}"
    )
    lines.append(
        f"  missing: {(~valid).sum():,}"
    )

    if valid.any():
        lines.append(
            f"  min: {np.nanmin(distance):.6f} km"
        )
        lines.append(
            f"  median: {np.nanmedian(distance):.6f} km"
        )
        lines.append(
            f"  mean: {np.nanmean(distance):.6f} km"
        )
        lines.append(
            f"  max: {np.nanmax(distance):.6f} km"
        )

    lines.append("")
    lines.append(
        "Candidate-K convergence:"
    )

    for key, values in convergence.items():
        lines.append(
            f"  {key}: "
            f"changed={values['changed_count']:,}, "
            f"changed_percent="
            f"{values['changed_percent']:.6f}%, "
            f"max_change="
            f"{values['max_change_km']:.9f} km"
        )

    if "cfm_nearest_fault_3d" in result.columns:
        unique_faults = (
            result["cfm_nearest_fault_3d"]
            .dropna()
            .nunique()
        )

        lines.append("")
        lines.append(
            "Nearest 3D CFM faults:"
        )
        lines.append(
            f"  unique faults assigned: "
            f"{unique_faults:,}"
        )

    lines.append("")
    lines.append(
        "IMPORTANT:"
    )
    lines.append(
        "cfm_distance_3d_to_surface_km is the minimum "
        "Euclidean 3D distance to candidate CFM triangles."
    )
    lines.append(
        "Candidate triangles are selected through a "
        "3D KD-tree of triangle centroids."
    )
    lines.append(
        "K-convergence is reported to detect sensitivity "
        "to the candidate search size."
    )
    lines.append(
        "The feature uses earthquake depth as positive "
        "downward depth converted to z = -depth."
    )

    return "\n".join(lines)


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    """Run the complete 3D CFM feature pipeline."""

    print_header(
        "CFM6.0 3D EARTHQUAKE FEATURE ENGINEERING"
    )

    print("Project root:")
    print(PROJECT_ROOT)

    print()
    print("Final candidate K:", FINAL_CANDIDATE_K)
    print("Batch size:", BATCH_SIZE)

    # --------------------------------------------------------
    # Load data
    # --------------------------------------------------------

    earthquakes = load_earthquakes()
    vertices = load_cfm_vertices()
    triangles = load_cfm_triangles()

    # --------------------------------------------------------
    # Build triangle geometry
    # --------------------------------------------------------

    triangle_vertices, triangle_centroids = (
        build_triangle_geometry(
            vertices,
            triangles,
        )
    )

    # --------------------------------------------------------
    # KD-tree
    # --------------------------------------------------------

    tree = build_centroid_tree(
        triangle_centroids
    )

    # --------------------------------------------------------
    # Earthquake 3D coordinates
    # --------------------------------------------------------

    earthquake_coordinates = (
        earthquake_coordinates_3d(
            earthquakes
        )
    )

    # --------------------------------------------------------
    # Candidate convergence
    # --------------------------------------------------------

    results = run_convergence_test(
        earthquake_coordinates,
        tree,
        triangle_vertices,
    )

    convergence = compare_k_results(
        results
    )

    # --------------------------------------------------------
    # Select final result
    # --------------------------------------------------------

    if FINAL_CANDIDATE_K not in results:
        raise RuntimeError(
            "FINAL_CANDIDATE_K was not calculated."
        )

    final_distances, final_triangle_ids = (
        results[FINAL_CANDIDATE_K]
    )

    earthquakes[
        "cfm_distance_3d_to_surface_km"
    ] = final_distances

    # --------------------------------------------------------
    # Attach nearest triangle / fault
    # --------------------------------------------------------

    result = attach_triangle_information(
        earthquakes,
        triangles,
        final_triangle_ids,
    )

    # Remove internal coordinate columns.
    result = result.drop(
        columns=[
            "_longitude",
            "_latitude",
            "_depth_km",
        ],
        errors="ignore",
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result.to_parquet(
        OUTPUT_FILE,
        index=False,
    )

    report = build_report(
        result,
        triangle_vertices,
        convergence,
    )

    REPORT_FILE.write_text(
        report,
        encoding="utf-8",
    )

    # --------------------------------------------------------
    # Final terminal summary
    # --------------------------------------------------------

    print_header(
        "CFM6.0 3D FEATURE ENGINEERING COMPLETE"
    )

    print("Output:")
    print(OUTPUT_FILE)

    print()
    print("Report:")
    print(REPORT_FILE)

    distance = result[
        "cfm_distance_3d_to_surface_km"
    ]

    valid = distance.notna()

    print()
    print(
        f"Earthquakes processed: "
        f"{len(result):,}"
    )

    print(
        f"Valid 3D distances: "
        f"{valid.sum():,}"
    )

    print(
        f"Missing 3D distances: "
        f"{(~valid).sum():,}"
    )

    if valid.any():
        print(
            f"3D distance median: "
            f"{distance[valid].median():.4f} km"
        )

        print(
            f"3D distance mean: "
            f"{distance[valid].mean():.4f} km"
        )

        print(
            f"3D distance max: "
            f"{distance[valid].max():.4f} km"
        )

    print()
    print("Next step:")
    print(
        "Inspect cfm_3d_feature_report.txt "
        "before integrating the 3D feature into XGBoost."
    )


if __name__ == "__main__":
    main()
  
