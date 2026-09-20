"""Microscopic audit of CFM6.0 earthquake-to-surface geometry."""

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

# Fixed seed makes the audit reproducible.
RANDOM_SEED = 20260920

# Number of earthquakes to inspect.
N_SAMPLE = 5

# Source geographic CRS of earthquake catalog.
EARTHQUAKE_CRS = "EPSG:4326"

# CFM projected CRS.
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
# COLUMN DETECTION
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


def detect_triangle_columns(
    triangles: pd.DataFrame,
) -> tuple[str, str, str]:
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


# ---------------------------------------------------------------------
# POINT-TO-TRIANGLE GEOMETRY
# ---------------------------------------------------------------------

def point_to_triangle_distance(
    point: np.ndarray,
    triangle: np.ndarray,
) -> float:
    """
    Exact Euclidean distance from one 3D point to one triangle.

    Parameters
    ----------
    point:
        Shape (3,), XYZ coordinates.

    triangle:
        Shape (3, 3), XYZ coordinates of triangle vertices.

    Returns
    -------
    float
        Distance in meters.
    """

    p = point
    a = triangle[0]
    b = triangle[1]
    c = triangle[2]

    ab = b - a
    ac = c - a
    ap = p - a

    d1 = np.dot(ab, ap)
    d2 = np.dot(ac, ap)

    # Region around vertex A.
    if d1 <= 0.0 and d2 <= 0.0:
        return float(np.linalg.norm(p - a))

    bp = p - b

    d3 = np.dot(ab, bp)
    d4 = np.dot(ac, bp)

    # Region around vertex B.
    if d3 >= 0.0 and d4 <= d3:
        return float(np.linalg.norm(p - b))

    vc = d1 * d4 - d3 * d2

    # Region on edge AB.
    if vc <= 0.0 and d1 >= 0.0 and d3 <= 0.0:
        v = d1 / (d1 - d3)
        projection = a + v * ab
        return float(np.linalg.norm(p - projection))

    cp = p - c

    d5 = np.dot(ab, cp)
    d6 = np.dot(ac, cp)

    # Region around vertex C.
    if d6 >= 0.0 and d5 <= d6:
        return float(np.linalg.norm(p - c))

    vb = d5 * d2 - d1 * d6

    # Region on edge AC.
    if vb <= 0.0 and d2 >= 0.0 and d6 <= 0.0:
        w = d2 / (d2 - d6)
        projection = a + w * ac
        return float(np.linalg.norm(p - projection))

    va = d3 * d6 - d5 * d4

    # Region on edge BC.
    if va <= 0.0 and (d4 - d3) >= 0.0 and (d5 - d6) >= 0.0:
        w = (d4 - d3) / ((d4 - d3) + (d5 - d6))
        projection = b + w * (c - b)
        return float(np.linalg.norm(p - projection))

    # Interior of triangle.
    normal = np.cross(ab, ac)
    normal_norm = np.linalg.norm(normal)

    if normal_norm == 0.0:
        # Degenerate triangle.
        distances = [
            np.linalg.norm(p - a),
            np.linalg.norm(p - b),
            np.linalg.norm(p - c),
        ]
        return float(min(distances))

    distance = abs(np.dot(p - a, normal)) / normal_norm

    return float(distance)


# ---------------------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------------------

def load_data():
    """Load earthquake, vertex and triangle datasets."""

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


# ---------------------------------------------------------------------
# VERTEX COORDINATES
# ---------------------------------------------------------------------

def detect_vertex_columns(vertices: pd.DataFrame):
    """Detect vertex ID and XYZ columns."""

    vertex_id = find_column(
        vertices,
        ["vertex_id", "id", "ID", "vertex"],
        "vertex ID",
    )

    x_col = find_column(
        vertices,
        ["x", "X", "X_m", "x_m"],
        "X",
    )

    y_col = find_column(
        vertices,
        ["y", "Y", "Y_m", "y_m"],
        "Y",
    )

    z_col = find_column(
        vertices,
        ["z", "Z", "Z_m", "z_m"],
        "Z",
    )

    return vertex_id, x_col, y_col, z_col


def prepare_vertices(vertices: pd.DataFrame):
    """Prepare vertex IDs and XYZ coordinates."""

    vertex_id_col, x_col, y_col, z_col = detect_vertex_columns(vertices)

    result = vertices.copy()

    result["_vertex_id"] = pd.to_numeric(
        result[vertex_id_col],
        errors="raise",
    ).astype(int)

    result["_x"] = pd.to_numeric(
        result[x_col],
        errors="raise",
    ).astype(float)

    result["_y"] = pd.to_numeric(
        result[y_col],
        errors="raise",
    ).astype(float)

    result["_z"] = pd.to_numeric(
        result[z_col],
        errors="raise",
    ).astype(float)

    return result


# ---------------------------------------------------------------------
# TRIANGLE INDEXING
# ---------------------------------------------------------------------

def detect_indexing(
    triangles: pd.DataFrame,
    triangle_columns: tuple[str, str, str],
    n_vertices: int,
) -> int:
    """
    Detect whether triangle vertex references are 0-based or 1-based.

    Returns
    -------
    int
        0 or 1.
    """

    refs = triangles[list(triangle_columns)].to_numpy(dtype=np.int64)

    minimum = int(refs.min())
    maximum = int(refs.max())

    print()
    print("Triangle reference range:")
    print(f"minimum: {minimum}")
    print(f"maximum: {maximum}")
    print(f"number of vertices: {n_vertices}")

    if minimum == 0 and maximum < n_vertices:
        print("Detected indexing: 0-based")
        return 0

    if minimum >= 1 and maximum <= n_vertices:
        print("Detected indexing: 1-based")
        return 1

    raise ValueError(
        "Triangle references do not match either "
        "0-based or 1-based indexing."
    )


# ---------------------------------------------------------------------
# BUILD TRIANGLE ARRAYS
# ---------------------------------------------------------------------

def build_triangle_arrays(
    vertices: pd.DataFrame,
    triangles: pd.DataFrame,
    triangle_columns: tuple[str, str, str],
    indexing: int,
):
    """Build triangle XYZ arrays and vertex-reference arrays."""

    vertex_lookup = (
        vertices
        .set_index("_vertex_id")[["_x", "_y", "_z"]]
    )

    refs = triangles[list(triangle_columns)].to_numpy(
        dtype=np.int64
    )

    if indexing == 1:
        refs = refs - 1

    triangle_xyz = np.empty(
        (len(triangles), 3, 3),
        dtype=np.float64,
    )

    for i in range(3):
        vertex_ids = refs[:, i]

        try:
            triangle_xyz[:, i, :] = vertex_lookup.loc[
                vertex_ids
            ].to_numpy()
        except KeyError as exc:
            raise ValueError(
                "Triangle references contain a vertex ID "
                "that does not exist in the vertex table."
            ) from exc

    centroids = triangle_xyz.mean(axis=1)

    return refs, triangle_xyz, centroids

# ---------------------------------------------------------------------
# EARTHQUAKE COORDINATES
# ---------------------------------------------------------------------

def detect_earthquake_columns(
    earthquakes: pd.DataFrame,
):
    """Detect longitude, latitude and depth columns."""

    lon_col = find_column(
        earthquakes,
        ["longitude", "lon", "LONGITUDE", "LONG"],
        "longitude",
    )

    lat_col = find_column(
        earthquakes,
        ["latitude", "lat", "LATITUDE", "LAT"],
        "latitude",
    )

    depth_col = find_column(
        earthquakes,
        ["depth_km", "depth", "DEPTH"],
        "depth",
    )

    return lon_col, lat_col, depth_col


def earthquake_xyz(
    earthquake: pd.Series,
    lon_col: str,
    lat_col: str,
    depth_col: str,
) -> tuple[float, float, float]:
    """
    Convert earthquake longitude/latitude/depth to CFM XYZ.

    Vertical convention used here:
        z = -depth_km * 1000

    This is deliberately printed in the audit so it can be
    checked against the CFM vertical reference.
    """

    lon = float(earthquake[lon_col])
    lat = float(earthquake[lat_col])
    depth_km = float(earthquake[depth_col])

    x, y = TRANSFORMER.transform(lon, lat)

    z = -depth_km * 1000.0

    return float(x), float(y), float(z)


# ---------------------------------------------------------------------
# FAULT NAME
# ---------------------------------------------------------------------

def detect_fault_name_column(
    triangles: pd.DataFrame,
) -> str | None:
    """Find an optional fault-name column in triangle data."""

    candidates = [
        "fault_name",
        "Fault Name",
        "CFM6.0 Fault Object Name",
        "object_name",
        "name",
    ]

    for candidate in candidates:
        if candidate in triangles.columns:
            return candidate

    return None


# ---------------------------------------------------------------------
# TRIANGLE CONTAINING A VERTEX
# ---------------------------------------------------------------------

def find_triangles_containing_vertex(
    refs: np.ndarray,
    vertex_index: int,
) -> np.ndarray:
    """Return triangle indices containing a particular vertex."""

    mask = np.any(refs == vertex_index, axis=1)

    return np.flatnonzero(mask)


# ---------------------------------------------------------------------
# EXHAUSTIVE DISTANCE FOR ONE EARTHQUAKE
# ---------------------------------------------------------------------

def exhaustive_nearest_triangle(
    point: np.ndarray,
    triangle_xyz: np.ndarray,
) -> tuple[int, float]:
    """Find exact nearest triangle by checking every triangle."""

    best_index = -1
    best_distance = float("inf")

    for i in range(len(triangle_xyz)):
        distance = point_to_triangle_distance(
            point,
            triangle_xyz[i],
        )

        if distance < best_distance:
            best_distance = distance
            best_index = i

    return best_index, best_distance


# ---------------------------------------------------------------------
# FORMAT HELPERS
# ---------------------------------------------------------------------

def format_xyz(xyz: np.ndarray) -> str:
    """Format XYZ coordinates for the report."""

    return (
        f"X={xyz[0]:.3f} m, "
        f"Y={xyz[1]:.3f} m, "
        f"Z={xyz[2]:.3f} m"
    )


def format_km(value_m: float) -> str:
    """Format a distance in meters as kilometers."""

    return f"{value_m / 1000.0:.6f} km"


# ---------------------------------------------------------------------
# MICROSCOPIC AUDIT
# ---------------------------------------------------------------------

def audit_one_earthquake(
    earthquake_number: int,
    earthquake: pd.Series,
    lon_col: str,
    lat_col: str,
    depth_col: str,
    vertices: pd.DataFrame,
    vertex_tree: cKDTree,
    refs: np.ndarray,
    triangle_xyz: np.ndarray,
    centroids: np.ndarray,
    centroid_tree: cKDTree,
    triangles: pd.DataFrame,
    fault_name_column: str | None,
):
    """Perform the full microscopic audit for one earthquake."""

    point_xyz = np.array(
        earthquake_xyz(
            earthquake,
            lon_col,
            lat_col,
            depth_col,
        )
    )

    # -------------------------------------------------------------
    # Nearest CFM vertex
    # -------------------------------------------------------------

    vertex_distance_m, vertex_position = vertex_tree.query(
        point_xyz
    )

    nearest_vertex_id = int(
        vertices.iloc[vertex_position]["_vertex_id"]
    )

    nearest_vertex_xyz = vertices.iloc[
        vertex_position
    ][["_x", "_y", "_z"]].to_numpy(dtype=float)

    # -------------------------------------------------------------
    # Every triangle containing that nearest vertex
    # -------------------------------------------------------------

    triangles_with_vertex = find_triangles_containing_vertex(
        refs,
        nearest_vertex_id,
    )

    containing_distances = []

    for triangle_index in triangles_with_vertex:

        distance_m = point_to_triangle_distance(
            point_xyz,
            triangle_xyz[triangle_index],
        )

        containing_distances.append(
            (int(triangle_index), float(distance_m))
        )

    containing_distances.sort(
        key=lambda item: item[1]
    )

    # -------------------------------------------------------------
    # Centroid nearest triangle
    # -------------------------------------------------------------

    centroid_distance_m, centroid_index = centroid_tree.query(
        point_xyz
    )

    centroid_index = int(centroid_index)

    centroid_triangle = triangle_xyz[centroid_index]

    centroid_exact_distance_m = point_to_triangle_distance(
        point_xyz,
        centroid_triangle,
    )

    # -------------------------------------------------------------
    # Exhaustive nearest triangle
    # -------------------------------------------------------------

    exhaustive_index, exhaustive_distance_m = (
        exhaustive_nearest_triangle(
            point_xyz,
            triangle_xyz,
        )
    )

    # -------------------------------------------------------------
    # Report
    # -------------------------------------------------------------

    lines = []

    lines.append("")
    lines.append("=" * 78)
    lines.append(
        f"EARTHQUAKE AUDIT #{earthquake_number}"
    )
    lines.append("=" * 78)

    lines.append("")
    lines.append("EARTHQUAKE ORIGINAL VALUES")

    for column in earthquake.index:
        value = earthquake[column]

        if pd.notna(value):
            lines.append(
                f"{column}: {value}"
            )

    lines.append("")
    lines.append("EARTHQUAKE XYZ")

    lines.append(
        format_xyz(point_xyz)
    )

    lines.append("")
    lines.append("NEAREST CFM VERTEX")

    lines.append(
        f"vertex_id: {nearest_vertex_id}"
    )

    lines.append(
        f"distance: {format_km(vertex_distance_m)}"
    )

    lines.append(
        f"coordinates: {format_xyz(nearest_vertex_xyz)}"
    )

    lines.append("")
    lines.append(
        "TRIANGLES CONTAINING THE NEAREST VERTEX"
    )

    lines.append(
        f"count: {len(triangles_with_vertex)}"
    )

    if len(containing_distances) == 0:

        lines.append(
            "ERROR: no triangle contains the nearest vertex."
        )

    else:

        for rank, (
            triangle_index,
            distance_m,
        ) in enumerate(
            containing_distances[:10],
            start=1,
        ):

            lines.append(
                f"{rank}. triangle_index="
                f"{triangle_index}, "
                f"distance="
                f"{format_km(distance_m)}"
            )

    # -------------------------------------------------------------
    # Triangle containing nearest vertex
    # -------------------------------------------------------------

    if containing_distances:

        selected_containing_index = (
            containing_distances[0][0]
        )

        selected_containing_triangle = triangle_xyz[
            selected_containing_index
        ]

        lines.append("")
        lines.append(
            "CLOSEST TRIANGLE THAT CONTAINS "
            "THE NEAREST VERTEX"
        )

        lines.append(
            f"triangle_index: "
            f"{selected_containing_index}"
        )

        lines.append(
            f"distance: "
            f"{format_km(containing_distances[0][1])}"
        )

        triangle_refs = refs[
            selected_containing_index
        ]

        lines.append(
            f"vertex references: "
            f"{triangle_refs.tolist()}"
        )

        for j in range(3):

            lines.append(
                f"V{j + 1}: "
                f"{format_xyz(selected_containing_triangle[j])}"
            )

        selected_centroid = (
            selected_containing_triangle.mean(axis=0)
        )

        lines.append(
            f"centroid: "
            f"{format_xyz(selected_centroid)}"
        )

        if fault_name_column is not None:

            fault_name = triangles.iloc[
                selected_containing_index
            ][fault_name_column]

            lines.append(
                f"fault: {fault_name}"
            )

    # -------------------------------------------------------------
    # Nearest centroid
    # -------------------------------------------------------------

    lines.append("")
    lines.append("NEAREST CENTROID")

    lines.append(
        f"triangle_index: {centroid_index}"
    )

    lines.append(
        f"centroid distance: "
        f"{format_km(centroid_distance_m)}"
    )

    lines.append(
        f"exact distance to that triangle: "
        f"{format_km(centroid_exact_distance_m)}"
    )

    lines.append(
        f"triangle references: "
        f"{refs[centroid_index].tolist()}"
    )

    for j in range(3):

        lines.append(
            f"V{j + 1}: "
            f"{format_xyz(centroid_triangle[j])}"
        )

    if fault_name_column is not None:

        fault_name = triangles.iloc[
            centroid_index
        ][fault_name_column]

        lines.append(
            f"fault: {fault_name}"
        )

    # -------------------------------------------------------------
    # Exhaustive reference
    # -------------------------------------------------------------

    lines.append("")
    lines.append("EXHAUSTIVE EXACT RESULT")

    lines.append(
        f"triangle_index: {exhaustive_index}"
    )

    lines.append(
        f"distance: "
        f"{format_km(exhaustive_distance_m)}"
    )

    lines.append(
        f"triangle references: "
        f"{refs[exhaustive_index].tolist()}"
    )

    exhaustive_triangle = triangle_xyz[
        exhaustive_index
    ]

    for j in range(3):

        lines.append(
            f"V{j + 1}: "
            f"{format_xyz(exhaustive_triangle[j])}"
        )

    if fault_name_column is not None:

        fault_name = triangles.iloc[
            exhaustive_index
        ][fault_name_column]

        lines.append(
            f"fault: {fault_name}"
        )

    # -------------------------------------------------------------
    # Critical comparisons
    # -------------------------------------------------------------

    lines.append("")
    lines.append("CRITICAL COMPARISONS")

    lines.append(
        "Earthquake -> nearest vertex: "
        f"{format_km(vertex_distance_m)}"
    )

    if containing_distances:

        lines.append(
            "Earthquake -> best triangle "
            "containing that vertex: "
            f"{format_km(containing_distances[0][1])}"
        )

    lines.append(
        "Earthquake -> nearest-centroid triangle: "
        f"{format_km(centroid_exact_distance_m)}"
    )

    lines.append(
        "Earthquake -> exhaustive nearest triangle: "
        f"{format_km(exhaustive_distance_m)}"
    )

    if containing_distances:

        difference = (
            containing_distances[0][1]
            - vertex_distance_m
        )

        lines.append(
            "Containing-triangle minus vertex distance: "
            f"{difference / 1000.0:.6f} km"
        )

    centroid_error = (
        centroid_exact_distance_m
        - exhaustive_distance_m
    )

    lines.append(
        "Nearest-centroid triangle error: "
        f"{centroid_error / 1000.0:.6f} km"
    )

    return lines

# ---------------------------------------------------------------------
# EARTHQUAKE COORDINATES
# ---------------------------------------------------------------------

def detect_earthquake_columns(
    earthquakes: pd.DataFrame,
):
    """Detect longitude, latitude and depth columns."""

    lon_col = find_column(
        earthquakes,
        ["longitude", "lon", "LONGITUDE", "LONG"],
        "longitude",
    )

    lat_col = find_column(
        earthquakes,
        ["latitude", "lat", "LATITUDE", "LAT"],
        "latitude",
    )

    depth_col = find_column(
        earthquakes,
        ["depth_km", "depth", "DEPTH"],
        "depth",
    )

    return lon_col, lat_col, depth_col


def earthquake_xyz(
    earthquake: pd.Series,
    lon_col: str,
    lat_col: str,
    depth_col: str,
) -> tuple[float, float, float]:
    """
    Convert earthquake longitude/latitude/depth to CFM XYZ.

    Vertical convention used here:
        z = -depth_km * 1000

    This is deliberately printed in the audit so it can be
    checked against the CFM vertical reference.
    """

    lon = float(earthquake[lon_col])
    lat = float(earthquake[lat_col])
    depth_km = float(earthquake[depth_col])

    x, y = TRANSFORMER.transform(lon, lat)

    z = -depth_km * 1000.0

    return float(x), float(y), float(z)


# ---------------------------------------------------------------------
# FAULT NAME
# ---------------------------------------------------------------------

def detect_fault_name_column(
    triangles: pd.DataFrame,
) -> str | None:
    """Find an optional fault-name column in triangle data."""

    candidates = [
        "fault_name",
        "Fault Name",
        "CFM6.0 Fault Object Name",
        "object_name",
        "name",
    ]

    for candidate in candidates:
        if candidate in triangles.columns:
            return candidate

    return None


# ---------------------------------------------------------------------
# TRIANGLE CONTAINING A VERTEX
# ---------------------------------------------------------------------

def find_triangles_containing_vertex(
    refs: np.ndarray,
    vertex_index: int,
) -> np.ndarray:
    """Return triangle indices containing a particular vertex."""

    mask = np.any(refs == vertex_index, axis=1)

    return np.flatnonzero(mask)


# ---------------------------------------------------------------------
# EXHAUSTIVE DISTANCE FOR ONE EARTHQUAKE
# ---------------------------------------------------------------------

def exhaustive_nearest_triangle(
    point: np.ndarray,
    triangle_xyz: np.ndarray,
) -> tuple[int, float]:
    """Find exact nearest triangle by checking every triangle."""

    best_index = -1
    best_distance = float("inf")

    for i in range(len(triangle_xyz)):
        distance = point_to_triangle_distance(
            point,
            triangle_xyz[i],
        )

        if distance < best_distance:
            best_distance = distance
            best_index = i

    return best_index, best_distance


# ---------------------------------------------------------------------
# FORMAT HELPERS
# ---------------------------------------------------------------------

def format_xyz(xyz: np.ndarray) -> str:
    """Format XYZ coordinates for the report."""

    return (
        f"X={xyz[0]:.3f} m, "
        f"Y={xyz[1]:.3f} m, "
        f"Z={xyz[2]:.3f} m"
    )


def format_km(value_m: float) -> str:
    """Format a distance in meters as kilometers."""

    return f"{value_m / 1000.0:.6f} km"


# ---------------------------------------------------------------------
# MICROSCOPIC AUDIT
# ---------------------------------------------------------------------

def audit_one_earthquake(
    earthquake_number: int,
    earthquake: pd.Series,
    lon_col: str,
    lat_col: str,
    depth_col: str,
    vertices: pd.DataFrame,
    vertex_tree: cKDTree,
    refs: np.ndarray,
    triangle_xyz: np.ndarray,
    centroids: np.ndarray,
    centroid_tree: cKDTree,
    triangles: pd.DataFrame,
    fault_name_column: str | None,
):
    """Perform the full microscopic audit for one earthquake."""

    point_xyz = np.array(
        earthquake_xyz(
            earthquake,
            lon_col,
            lat_col,
            depth_col,
        )
    )

    # -------------------------------------------------------------
    # Nearest CFM vertex
    # -------------------------------------------------------------

    vertex_distance_m, vertex_position = vertex_tree.query(
        point_xyz
    )

    nearest_vertex_id = int(
        vertices.iloc[vertex_position]["_vertex_id"]
    )

    nearest_vertex_xyz = vertices.iloc[
        vertex_position
    ][["_x", "_y", "_z"]].to_numpy(dtype=float)

    # -------------------------------------------------------------
    # Every triangle containing that nearest vertex
    # -------------------------------------------------------------

    triangles_with_vertex = find_triangles_containing_vertex(
        refs,
        nearest_vertex_id,
    )

    containing_distances = []

    for triangle_index in triangles_with_vertex:

        distance_m = point_to_triangle_distance(
            point_xyz,
            triangle_xyz[triangle_index],
        )

        containing_distances.append(
            (int(triangle_index), float(distance_m))
        )

    containing_distances.sort(
        key=lambda item: item[1]
    )

    # -------------------------------------------------------------
    # Centroid nearest triangle
    # -------------------------------------------------------------

    centroid_distance_m, centroid_index = centroid_tree.query(
        point_xyz
    )

    centroid_index = int(centroid_index)

    centroid_triangle = triangle_xyz[centroid_index]

    centroid_exact_distance_m = point_to_triangle_distance(
        point_xyz,
        centroid_triangle,
    )

    # -------------------------------------------------------------
    # Exhaustive nearest triangle
    # -------------------------------------------------------------

    exhaustive_index, exhaustive_distance_m = (
        exhaustive_nearest_triangle(
            point_xyz,
            triangle_xyz,
        )
    )

    # -------------------------------------------------------------
    # Report
    # -------------------------------------------------------------

    lines = []

    lines.append("")
    lines.append("=" * 78)
    lines.append(
        f"EARTHQUAKE AUDIT #{earthquake_number}"
    )
    lines.append("=" * 78)

    lines.append("")
    lines.append("EARTHQUAKE ORIGINAL VALUES")

    for column in earthquake.index:
        value = earthquake[column]

        if pd.notna(value):
            lines.append(
                f"{column}: {value}"
            )

    lines.append("")
    lines.append("EARTHQUAKE XYZ")

    lines.append(
        format_xyz(point_xyz)
    )

    lines.append("")
    lines.append("NEAREST CFM VERTEX")

    lines.append(
        f"vertex_id: {nearest_vertex_id}"
    )

    lines.append(
        f"distance: {format_km(vertex_distance_m)}"
    )

    lines.append(
        f"coordinates: {format_xyz(nearest_vertex_xyz)}"
    )

    lines.append("")
    lines.append(
        "TRIANGLES CONTAINING THE NEAREST VERTEX"
    )

    lines.append(
        f"count: {len(triangles_with_vertex)}"
    )

    if len(containing_distances) == 0:

        lines.append(
            "ERROR: no triangle contains the nearest vertex."
        )

    else:

        for rank, (
            triangle_index,
            distance_m,
        ) in enumerate(
            containing_distances[:10],
            start=1,
        ):

            lines.append(
                f"{rank}. triangle_index="
                f"{triangle_index}, "
                f"distance="
                f"{format_km(distance_m)}"
            )

    # -------------------------------------------------------------
    # Triangle containing nearest vertex
    # -------------------------------------------------------------

    if containing_distances:

        selected_containing_index = (
            containing_distances[0][0]
        )

        selected_containing_triangle = triangle_xyz[
            selected_containing_index
        ]

        lines.append("")
        lines.append(
            "CLOSEST TRIANGLE THAT CONTAINS "
            "THE NEAREST VERTEX"
        )

        lines.append(
            f"triangle_index: "
            f"{selected_containing_index}"
        )

        lines.append(
            f"distance: "
            f"{format_km(containing_distances[0][1])}"
        )

        triangle_refs = refs[
            selected_containing_index
        ]

        lines.append(
            f"vertex references: "
            f"{triangle_refs.tolist()}"
        )

        for j in range(3):

            lines.append(
                f"V{j + 1}: "
                f"{format_xyz(selected_containing_triangle[j])}"
            )

        selected_centroid = (
            selected_containing_triangle.mean(axis=0)
        )

        lines.append(
            f"centroid: "
            f"{format_xyz(selected_centroid)}"
        )

        if fault_name_column is not None:

            fault_name = triangles.iloc[
                selected_containing_index
            ][fault_name_column]

            lines.append(
                f"fault: {fault_name}"
            )

    # -------------------------------------------------------------
    # Nearest centroid
    # -------------------------------------------------------------

    lines.append("")
    lines.append("NEAREST CENTROID")

    lines.append(
        f"triangle_index: {centroid_index}"
    )

    lines.append(
        f"centroid distance: "
        f"{format_km(centroid_distance_m)}"
    )

    lines.append(
        f"exact distance to that triangle: "
        f"{format_km(centroid_exact_distance_m)}"
    )

    lines.append(
        f"triangle references: "
        f"{refs[centroid_index].tolist()}"
    )

    for j in range(3):

        lines.append(
            f"V{j + 1}: "
            f"{format_xyz(centroid_triangle[j])}"
        )

    if fault_name_column is not None:

        fault_name = triangles.iloc[
            centroid_index
        ][fault_name_column]

        lines.append(
            f"fault: {fault_name}"
        )

    # -------------------------------------------------------------
    # Exhaustive reference
    # -------------------------------------------------------------

    lines.append("")
    lines.append("EXHAUSTIVE EXACT RESULT")

    lines.append(
        f"triangle_index: {exhaustive_index}"
    )

    lines.append(
        f"distance: "
        f"{format_km(exhaustive_distance_m)}"
    )

    lines.append(
        f"triangle references: "
        f"{refs[exhaustive_index].tolist()}"
    )

    exhaustive_triangle = triangle_xyz[
        exhaustive_index
    ]

    for j in range(3):

        lines.append(
            f"V{j + 1}: "
            f"{format_xyz(exhaustive_triangle[j])}"
        )

    if fault_name_column is not None:

        fault_name = triangles.iloc[
            exhaustive_index
        ][fault_name_column]

        lines.append(
            f"fault: {fault_name}"
        )

    # -------------------------------------------------------------
    # Critical comparisons
    # -------------------------------------------------------------

    lines.append("")
    lines.append("CRITICAL COMPARISONS")

    lines.append(
        "Earthquake -> nearest vertex: "
        f"{format_km(vertex_distance_m)}"
    )

    if containing_distances:

        lines.append(
            "Earthquake -> best triangle "
            "containing that vertex: "
            f"{format_km(containing_distances[0][1])}"
        )

    lines.append(
        "Earthquake -> nearest-centroid triangle: "
        f"{format_km(centroid_exact_distance_m)}"
    )

    lines.append(
        "Earthquake -> exhaustive nearest triangle: "
        f"{format_km(exhaustive_distance_m)}"
    )

    if containing_distances:

        difference = (
            containing_distances[0][1]
            - vertex_distance_m
        )

        lines.append(
            "Containing-triangle minus vertex distance: "
            f"{difference / 1000.0:.6f} km"
        )

    centroid_error = (
        centroid_exact_distance_m
        - exhaustive_distance_m
    )

    lines.append(
        "Nearest-centroid triangle error: "
        f"{centroid_error / 1000.0:.6f} km"
    )

    return lines


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main():
    """Run the microscopic CFM geometry audit."""

    print("=" * 78)
    print("CFM6.0 MICROSCOPIC GEOMETRY AUDIT")
    print("=" * 78)

    earthquakes, vertices, triangles, metadata = load_data()

    # -------------------------------------------------------------
    # Prepare vertices
    # -------------------------------------------------------------

    print()
    print("Preparing vertices...")

    vertices = prepare_vertices(vertices)

    # Check duplicate vertex IDs.
    duplicate_vertex_ids = (
        vertices["_vertex_id"]
        .duplicated()
        .sum()
    )

    print(
        f"Duplicate vertex IDs: "
        f"{duplicate_vertex_ids}"
    )

    if duplicate_vertex_ids > 0:
        raise ValueError(
            "Duplicate vertex IDs detected."
        )

    # -------------------------------------------------------------
    # Prepare triangles
    # -------------------------------------------------------------

    print()
    print("Preparing triangles...")

    triangle_columns = detect_triangle_columns(
        triangles
    )

    print(
        "Triangle reference columns: "
        f"{triangle_columns}"
    )

    indexing = detect_indexing(
        triangles,
        triangle_columns,
        len(vertices),
    )

    refs, triangle_xyz, centroids = (
        build_triangle_arrays(
            vertices,
            triangles,
            triangle_columns,
            indexing,
        )
    )

    print(
        f"Triangle XYZ array: "
        f"{triangle_xyz.shape}"
    )

    # -------------------------------------------------------------
    # Build spatial indexes
    # -------------------------------------------------------------

    print()
    print("Building vertex KDTree...")

    vertex_xyz = vertices[
        ["_x", "_y", "_z"]
    ].to_numpy(dtype=float)

    vertex_tree = cKDTree(vertex_xyz)

    print("Building centroid KDTree...")

    centroid_tree = cKDTree(centroids)

    # -------------------------------------------------------------
    # Earthquake columns
    # -------------------------------------------------------------

    lon_col, lat_col, depth_col = (
        detect_earthquake_columns(
            earthquakes
        )
    )

    print()
    print("Earthquake columns:")
    print(f"longitude: {lon_col}")
    print(f"latitude:  {lat_col}")
    print(f"depth:    {depth_col}")

    # -------------------------------------------------------------
    # Reproducible sample
    # -------------------------------------------------------------

    print()
    print(
        f"Selecting {N_SAMPLE} earthquakes "
        f"with seed {RANDOM_SEED}..."
    )

    sample = earthquakes.sample(
        n=N_SAMPLE,
        random_state=RANDOM_SEED,
    )

    # -------------------------------------------------------------
    # Optional fault name
    # -------------------------------------------------------------

    fault_name_column = detect_fault_name_column(
        triangles
    )

    print(
        "Fault-name column: "
        f"{fault_name_column}"
    )

    # -------------------------------------------------------------
    # Audit
    # -------------------------------------------------------------

    report_lines = []

    report_lines.append(
        "CFM6.0 MICROSCOPIC GEOMETRY AUDIT"
    )

    report_lines.append("=" * 78)

    report_lines.append("")
    report_lines.append("DATASET SIZES")
    report_lines.append(
        f"Earthquakes: {len(earthquakes):,}"
    )
    report_lines.append(
        f"CFM vertices: {len(vertices):,}"
    )
    report_lines.append(
        f"CFM triangles: {len(triangles):,}"
    )

    report_lines.append("")
    report_lines.append("TRIANGLE INDEXING")
    report_lines.append(
        f"Convention: {'0-based' if indexing == 0 else '1-based'}"
    )

    report_lines.append("")
    report_lines.append("VERTICAL CONVENTION")
    report_lines.append(
        "Earthquake z = -depth_km * 1000"
    )

    report_lines.append(
        "CFM z is used exactly as stored in the CFM XYZ file."
    )

    report_lines.append("")
    report_lines.append("SAMPLE")
    report_lines.append(
        f"Seed: {RANDOM_SEED}"
    )
    report_lines.append(
        f"Earthquakes: {N_SAMPLE}"
    )

    # -------------------------------------------------------------
    # Process each sample
    # -------------------------------------------------------------

    for number, (_, earthquake) in enumerate(
        sample.iterrows(),
        start=1,
    ):

        print()
        print(
            f"Auditing earthquake "
            f"{number}/{N_SAMPLE}..."
        )

        lines = audit_one_earthquake(
            earthquake_number=number,
            earthquake=earthquake,
            lon_col=lon_col,
            lat_col=lat_col,
            depth_col=depth_col,
            vertices=vertices,
            vertex_tree=vertex_tree,
            refs=refs,
            triangle_xyz=triangle_xyz,
            centroids=centroids,
            centroid_tree=centroid_tree,
            triangles=triangles,
            fault_name_column=fault_name_column,
        )

        report_lines.extend(lines)

    # -------------------------------------------------------------
    # Write report
    # -------------------------------------------------------------

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT_FILE.write_text(
        "\n".join(report_lines),
        encoding="utf-8",
    )

    print()
    print("=" * 78)
    print("AUDIT COMPLETE")
    print("=" * 78)

    print()
    print(
        f"Report written to:\n{REPORT_FILE}"
    )

    print()
    print(
        "IMPORTANT: do not integrate the CFM 3D "
        "distance into XGBoost yet."
    )


if __name__ == "__main__":
    main()
