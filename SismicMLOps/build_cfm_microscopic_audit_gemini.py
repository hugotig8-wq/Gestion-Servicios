"""Microscopic audit of CFM6.0 earthquake-to-surface geometry.

Corrected version: 'vertex_id' is local per fault/object.
Composite lookup key: (fault_name, vertex_id).
"""

from pathlib import Path

import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy.spatial import cKDTree


# ---------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent

CFM_DIR = PROJECT_ROOT / "data" / "processed" / "cfm"

EARTHQUAKES_FILE = CFM_DIR / "earthquakes_cfm_features.parquet"
VERTICES_FILE = CFM_DIR / "cfm_vertices_1000m.csv"
TRIANGLES_FILE = CFM_DIR / "cfm_triangles_1000m.csv"
METADATA_FILE = CFM_DIR / "cfm_metadata_clean.csv"

REPORT_FILE = CFM_DIR / "cfm_microscopic_audit_report.txt"


# ---------------------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------------------

RANDOM_SEED = 20260920
N_SAMPLE = 5
EARTHQUAKE_CRS = "EPSG:4326"
CFM_CRS = "EPSG:26711"


# ---------------------------------------------------------------------
# CRS TRANSFORMATION
# ---------------------------------------------------------------------

TRANSFORMER = Transformer.from_crs(
    EARTHQUAKE_CRS,
    CFM_CRS,
    always_xy=True,
)


# ---------------------------------------------------------------------
# HELPER FUNCTIONS & COLUMN DETECTION
# ---------------------------------------------------------------------

def find_column(df: pd.DataFrame, candidates: list[str], label: str) -> str:
    """Find a dataframe column from a list of accepted names."""
    for candidate in candidates:
        if candidate in df.columns:
            return candidate
    raise ValueError(
        f"Could not find {label} column.\n"
        f"Accepted names: {candidates}\n"
        f"Available columns: {list(df.columns)}"
    )


def detect_triangle_columns(triangles: pd.DataFrame) -> tuple[str, str, str]:
    """Detect the three triangle vertex-reference columns."""
    candidates = [
        ("v1", "v2", "v3"),
        ("vertex1", "vertex2", "vertex3"),
        ("vertex_1", "vertex_2", "vertex_3"),
        ("VRTX1", "VRTX2", "VRTX3"),
        ("vertex_a", "vertex_b", "vertex_c"),
    ]
    for names in candidates:
        if all(name in triangles.columns for name in names):
            return names
    raise ValueError(
        "Could not identify triangle vertex-reference columns.\n"
        f"Available columns: {list(triangles.columns)}"
    )


def detect_fault_name_column(df: pd.DataFrame) -> str:
    """Detect the fault/object identifier column."""
    return find_column(
        df,
        ["fault_name", "Fault Name", "CFM6.0 Fault Object Name", "object_name", "name"],
        "fault name",
    )


# ---------------------------------------------------------------------
# POINT-TO-TRIANGLE GEOMETRY
# ---------------------------------------------------------------------

def point_to_triangle_distance(point: np.ndarray, triangle: np.ndarray) -> float:
    """Exact Euclidean distance from one 3D point to one triangle."""
    p = point
    a, b, c = triangle[0], triangle[1], triangle[2]

    ab = b - a
    ac = c - a
    ap = p - a

    d1 = np.dot(ab, ap)
    d2 = np.dot(ac, ap)

    if d1 <= 0.0 and d2 <= 0.0:
        return float(np.linalg.norm(p - a))

    bp = p - b
    d3 = np.dot(ab, bp)
    d4 = np.dot(ac, bp)

    if d3 >= 0.0 and d4 <= d3:
        return float(np.linalg.norm(p - b))

    vc = d1 * d4 - d3 * d2
    if vc <= 0.0 and d1 >= 0.0 and d3 <= 0.0:
        v = d1 / (d1 - d3)
        projection = a + v * ab
        return float(np.linalg.norm(p - projection))

    cp = p - c
    d5 = np.dot(ab, cp)
    d6 = np.dot(ac, cp)

    if d6 >= 0.0 and d5 <= d6:
        return float(np.linalg.norm(p - c))

    vb = d5 * d2 - d1 * d6
    if vb <= 0.0 and d2 >= 0.0 and d6 <= 0.0:
        w = d2 / (d2 - d6)
        projection = a + w * ac
        return float(np.linalg.norm(p - projection))

    va = d3 * d6 - d5 * d4
    if va <= 0.0 and (d4 - d3) >= 0.0 and (d5 - d6) >= 0.0:
        w = (d4 - d3) / ((d4 - d3) + (d5 - d6))
        projection = b + w * (c - b)
        return float(np.linalg.norm(p - projection))

    normal = np.cross(ab, ac)
    normal_norm = np.linalg.norm(normal)

    if normal_norm == 0.0:
        return float(min(np.linalg.norm(p - a), np.linalg.norm(p - b), np.linalg.norm(p - c)))

    distance = abs(np.dot(p - a, normal)) / normal_norm
    return float(distance)

# ---------------------------------------------------------------------
# LOAD DATA & PREPARATION
# ---------------------------------------------------------------------

def load_data():
    """Load earthquake, vertex, triangle, and metadata datasets."""
    print("Loading earthquake dataset...")
    earthquakes = pd.read_parquet(EARTHQUAKES_FILE)

    print("Loading CFM vertices...")
    vertices = pd.read_csv(VERTICES_FILE)

    print("Loading CFM triangles...")
    triangles = pd.read_csv(TRIANGLES_FILE)

    print("Loading CFM metadata...")
    metadata = pd.read_csv(METADATA_FILE)

    print()
    print(f"Earthquakes: {len(earthquakes):,}")
    print(f"Vertices:    {len(vertices):,}")
    print(f"Triangles:   {len(triangles):,}")
    print(f"Metadata:    {len(metadata):,}")

    return earthquakes, vertices, triangles, metadata


def prepare_vertices(vertices: pd.DataFrame) -> pd.DataFrame:
    """Prepare vertices with normalized column names and types."""
    vertex_id_col = find_column(vertices, ["vertex_id", "id", "ID", "vertex"], "vertex ID")
    fault_col = detect_fault_name_column(vertices)
    x_col = find_column(vertices, ["x", "X", "X_m", "x_m"], "X")
    y_col = find_column(vertices, ["y", "Y", "Y_m", "y_m"], "Y")
    z_col = find_column(vertices, ["z", "Z", "Z_m", "z_m"], "Z")

    result = vertices.copy()
    result["_vertex_id"] = pd.to_numeric(result[vertex_id_col], errors="raise").astype(int)
    result["_fault_name"] = result[fault_col].astype(str)
    result["_x"] = pd.to_numeric(result[x_col], errors="raise").astype(float)
    result["_y"] = pd.to_numeric(result[y_col], errors="raise").astype(float)
    result["_z"] = pd.to_numeric(result[z_col], errors="raise").astype(float)

    # Validate composite key uniqueness
    duplicates = result.duplicated(subset=["_fault_name", "_vertex_id"]).sum()
    print(f"Duplicate (fault_name, vertex_id) pairs in vertices: {duplicates}")
    if duplicates > 0:
        raise ValueError("Vertices table contains duplicate local vertex_ids within the same fault!")

    return result


def build_triangle_arrays(
    vertices: pd.DataFrame,
    triangles: pd.DataFrame,
    triangle_columns: tuple[str, str, str],
):
    """
    Build 3D triangle array using composite key (fault_name, vertex_id) mapping.
    """
    fault_col = detect_fault_name_column(triangles)
    triangles["_fault_name"] = triangles[fault_col].astype(str)

    # Build multi-index lookup table for 3D coordinates
    vertex_lookup = vertices.set_index(["_fault_name", "_vertex_id"])[["_x", "_y", "_z"]]

    n_triangles = len(triangles)
    triangle_xyz = np.empty((n_triangles, 3, 3), dtype=np.float64)

    # Array to store row indices in the global vertices DataFrame
    # Shape: (n_triangles, 3)
    triangle_vertex_global_indices = np.empty((n_triangles, 3), dtype=np.int64)

    # Fast mapping from (fault_name, vertex_id) to global DataFrame row index
    vertex_row_map = {
        (fault, vid): idx 
        for idx, (fault, vid) in enumerate(zip(vertices["_fault_name"], vertices["_vertex_id"]))
    }

    print("Mapping triangles to global 3D vertex coordinates...")
    
    v1_col, v2_col, v3_col = triangle_columns
    v_cols = [v1_col, v2_col, v3_col]

    for i, row in triangles.iterrows():
        fault = row["_fault_name"]
        for j, col in enumerate(v_cols):
            local_vid = int(row[col])
            
            try:
                # 1. Lookup 3D coordinates
                coords = vertex_lookup.loc[(fault, local_vid)].to_numpy()
                triangle_xyz[i, j, :] = coords

                # 2. Lookup global row index in vertices DataFrame
                global_row_idx = vertex_row_map[(fault, local_vid)]
                triangle_vertex_global_indices[i, j] = global_row_idx

            except KeyError as exc:
                raise ValueError(
                    f"Triangle row {i} references fault '{fault}' and local vertex_id {local_vid}, "
                    f"which was not found in vertices file!"
                ) from exc

    centroids = triangle_xyz.mean(axis=1)

    return triangle_vertex_global_indices, triangle_xyz, centroids


def detect_earthquake_columns(earthquakes: pd.DataFrame):
    """Detect longitude, latitude, and depth columns."""
    lon_col = find_column(earthquakes, ["longitude", "lon", "LONGITUDE", "LONG"], "longitude")
    lat_col = find_column(earthquakes, ["latitude", "lat", "LATITUDE", "LAT"], "latitude")
    depth_col = find_column(earthquakes, ["depth_km", "depth", "DEPTH"], "depth")
    return lon_col, lat_col, depth_col


def earthquake_xyz(earthquake: pd.Series, lon_col: str, lat_col: str, depth_col: str) -> tuple[float, float, float]:
    """Convert earthquake longitude/latitude/depth to CFM XYZ."""
    lon = float(earthquake[lon_col])
    lat = float(earthquake[lat_col])
    depth_km = float(earthquake[depth_col])

    x, y = TRANSFORMER.transform(lon, lat)
    z = -depth_km * 1000.0

    return float(x), float(y), float(z)


# ---------------------------------------------------------------------
# SEARCH & AUDIT LOGIC
# ---------------------------------------------------------------------

def find_triangles_containing_global_vertex(
    triangle_vertex_global_indices: np.ndarray,
    global_vertex_idx: int,
) -> np.ndarray:
    """Find indices of all triangles containing the given global vertex row index."""
    mask = np.any(triangle_vertex_global_indices == global_vertex_idx, axis=1)
    return np.flatnonzero(mask)


def exhaustive_nearest_triangle(point: np.ndarray, triangle_xyz: np.ndarray) -> tuple[int, float]:
    """Find exact nearest triangle by checking every triangle."""
    best_index = -1
    best_distance = float("inf")

    for i in range(len(triangle_xyz)):
        distance = point_to_triangle_distance(point, triangle_xyz[i])
        if distance < best_distance:
            best_distance = distance
            best_index = i

    return best_index, best_distance


def format_xyz(xyz: np.ndarray) -> str:
    return f"X={xyz[0]:.3f} m, Y={xyz[1]:.3f} m, Z={xyz[2]:.3f} m"


def format_km(value_m: float) -> str:
    return f"{value_m / 1000.0:.6f} km"


def audit_one_earthquake(
    earthquake_number: int,
    earthquake: pd.Series,
    lon_col: str,
    lat_col: str,
    depth_col: str,
    vertices: pd.DataFrame,
    vertex_tree: cKDTree,
    triangle_vertex_global_indices: np.ndarray,
    triangle_xyz: np.ndarray,
    centroids: np.ndarray,
    centroid_tree: cKDTree,
    triangles: pd.DataFrame,
    fault_name_column: str,
):
    """Perform microscopic audit for one earthquake using global vertex row indexing."""
    point_xyz = np.array(earthquake_xyz(earthquake, lon_col, lat_col, depth_col))

    # 1. Nearest CFM global vertex via KDTree
    vertex_distance_m, global_vertex_row_idx = vertex_tree.query(point_xyz)
    global_vertex_row_idx = int(global_vertex_row_idx)

    nearest_vertex_row = vertices.iloc[global_vertex_row_idx]
    nearest_local_vid = nearest_vertex_row["_vertex_id"]
    nearest_fault = nearest_vertex_row["_fault_name"]
    nearest_vertex_xyz = nearest_vertex_row[["_x", "_y", "_z"]].to_numpy(dtype=float)

    # 2. Find triangles that contain this exact global vertex
    triangles_with_vertex = find_triangles_containing_global_vertex(
        triangle_vertex_global_indices,
        global_vertex_row_idx,
    )

    containing_distances = []
    for tri_idx in triangles_with_vertex:
        dist_m = point_to_triangle_distance(point_xyz, triangle_xyz[tri_idx])
        containing_distances.append((int(tri_idx), float(dist_m)))

    containing_distances.sort(key=lambda x: x[1])

    # 3. Nearest Centroid Triangle
    centroid_distance_m, centroid_index = centroid_tree.query(point_xyz)
    centroid_index = int(centroid_index)
    centroid_triangle = triangle_xyz[centroid_index]
    centroid_exact_distance_m = point_to_triangle_distance(point_xyz, centroid_triangle)

    # 4. Exhaustive Search
    exhaustive_index, exhaustive_distance_m = exhaustive_nearest_triangle(point_xyz, triangle_xyz)

    # --- Build Report Section ---
    lines = [
        "",
        "=" * 78,
        f"EARTHQUAKE AUDIT #{earthquake_number}",
        "=" * 78,
        "",
        "EARTHQUAKE ORIGINAL VALUES",
    ]

    for col in earthquake.index:
        if pd.notna(earthquake[col]):
            lines.append(f"{col}: {earthquake[col]}")

    lines.extend([
        "",
        "EARTHQUAKE XYZ",
        format_xyz(point_xyz),
        "",
        "NEAREST CFM VERTEX",
        f"fault: {nearest_fault}",
        f"local vertex_id: {nearest_local_vid}",
        f"global row index in vertices file: {global_vertex_row_idx}",
        f"distance: {format_km(vertex_distance_m)}",
        f"coordinates: {format_xyz(nearest_vertex_xyz)}",
        "",
        "TRIANGLES CONTAINING THE NEAREST VERTEX",
        f"count: {len(triangles_with_vertex)}",
    ])

    if len(containing_distances) == 0:
        lines.append("ERROR: No triangle contains this vertex in its specific fault context.")
    else:
        for rank, (tri_idx, dist_m) in enumerate(containing_distances[:10], start=1):
            lines.append(f"{rank}. triangle_index={tri_idx}, distance={format_km(dist_m)}")

    if containing_distances:
        sel_idx = containing_distances[0][0]
        sel_tri = triangle_xyz[sel_idx]
        lines.extend([
            "",
            "CLOSEST TRIANGLE THAT CONTAINS THE NEAREST VERTEX",
            f"triangle_index: {sel_idx}",
            f"distance: {format_km(containing_distances[0][1])}",
            f"fault: {triangles.iloc[sel_idx][fault_name_column]}",
            f"centroid: {format_xyz(sel_tri.mean(axis=0))}",
        ])
        for j in range(3):
            lines.append(f"V{j + 1}: {format_xyz(sel_tri[j])}")

    lines.extend([
        "",
        "NEAREST CENTROID",
        f"triangle_index: {centroid_index}",
        f"centroid distance: {format_km(centroid_distance_m)}",
        f"exact distance to triangle: {format_km(centroid_exact_distance_m)}",
        f"fault: {triangles.iloc[centroid_index][fault_name_column]}",
        "",
        "EXHAUSTIVE EXACT RESULT",
        f"triangle_index: {exhaustive_index}",
        f"distance: {format_km(exhaustive_distance_m)}",
        f"fault: {triangles.iloc[exhaustive_index][fault_name_column]}",
        "",
        "CRITICAL COMPARISONS",
        f"Earthquake -> nearest vertex: {format_km(vertex_distance_m)}",
    ])

    if containing_distances:
        lines.append(
            f"Earthquake -> best containing triangle: {format_km(containing_distances[0][1])}"
        )

    lines.extend([
        f"Earthquake -> nearest-centroid triangle: {format_km(centroid_exact_distance_m)}",
        f"Earthquake -> exhaustive nearest triangle: {format_km(exhaustive_distance_m)}",
    ])

    if containing_distances:
        diff = containing_distances[0][1] - vertex_distance_m
        lines.append(f"Containing-triangle minus vertex distance: {diff / 1000.0:.6f} km")

    c_err = centroid_exact_distance_m - exhaustive_distance_m
    lines.append(f"Nearest-centroid triangle error: {c_err / 1000.0:.6f} km")

    return lines


# ---------------------------------------------------------------------
# MAIN EXECUTION
# ---------------------------------------------------------------------

def main():
    print("=" * 78)
    print("CFM6.0 MICROSCOPIC GEOMETRY AUDIT (LOCAL VERTEX_ID CORRECTION)")
    print("=" * 78)

    earthquakes, vertices, triangles, metadata = load_data()

    print("\nPreparing vertices...")
    vertices = prepare_vertices(vertices)

    print("\nPreparing triangles & mapping local vertex IDs...")
    triangle_columns = detect_triangle_columns(triangles)
    fault_name_column = detect_fault_name_column(triangles)

    triangle_vertex_global_indices, triangle_xyz, centroids = build_triangle_arrays(
        vertices,
        triangles,
        triangle_columns,
    )

    print(f"Triangle XYZ array shape: {triangle_xyz.shape}")

    print("\nBuilding KDTree spatial indexes...")
    vertex_xyz = vertices[["_x", "_y", "_z"]].to_numpy(dtype=float)
    vertex_tree = cKDTree(vertex_xyz)
    centroid_tree = cKDTree(centroids)

    lon_col, lat_col, depth_col = detect_earthquake_columns(earthquakes)

    print(f"\nSelecting {N_SAMPLE} random earthquakes (seed {RANDOM_SEED})...")
    sample = earthquakes.sample(n=N_SAMPLE, random_state=RANDOM_SEED)

    report_lines = [
        "CFM6.0 MICROSCOPIC GEOMETRY AUDIT",
        "=" * 78,
        f"Earthquakes count: {len(earthquakes):,}",
        f"CFM vertices count: {len(vertices):,}",
        f"CFM triangles count: {len(triangles):,}",
        "Mapping strategy: Composite Key (fault_name, local_vertex_id)",
        f"Vertical convention: Earthquake z = -depth_km * 1000",
    ]

    for number, (_, earthquake) in enumerate(sample.iterrows(), start=1):
        print(f"Auditing earthquake {number}/{N_SAMPLE}...")
        lines = audit_one_earthquake(
            earthquake_number=number,
            earthquake=earthquake,
            lon_col=lon_col,
            lat_col=lat_col,
            depth_col=depth_col,
            vertices=vertices,
            vertex_tree=vertex_tree,
            triangle_vertex_global_indices=triangle_vertex_global_indices,
            triangle_xyz=triangle_xyz,
            centroids=centroids,
            centroid_tree=centroid_tree,
            triangles=triangles,
            fault_name_column=fault_name_column,
        )
        report_lines.extend(lines)

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text("\n".join(report_lines), encoding="utf-8")

    print("\n" + "=" * 78)
    print("AUDIT COMPLETE")
    print("=" * 78)
    print(f"Report written to:\n{REPORT_FILE}")


if __name__ == "__main__":
    main()
  
