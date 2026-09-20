"""
CFM6.0 geometry audit.

Purpose
-------
Audit the geometric consistency of:

    earthquake hypocenters
        +
    CFM vertices
        +
    CFM triangles

before using 3D CFM distance as a machine-learning feature.

This script DOES NOT modify the existing feature datasets.

It performs:

1. File/schema inspection.
2. Triangle -> vertex reference validation.
3. Automatic detection of 0-based vs 1-based triangle indices.
4. Coordinate-range inspection.
5. Reproducible sample of 1,000 earthquakes.
6. Centroid-K convergence test:
       K = 64, 256, 1024, 4096
7. Exhaustive point-to-triangle search for 20 earthquakes.
8. Comparison between:
       centroid-K result
       exhaustive result
9. Comparison between:
       nearest vertex distance
       nearest triangle-surface distance
10. Identification of suspicious cases.

The exhaustive test is intentionally restricted to 20 earthquakes
because it compares every selected earthquake with every CFM
triangle.

Outputs
-------
data/processed/cfm/cfm_geometry_audit_report.txt
data/processed/cfm/cfm_geometry_audit_samples.csv
"""

from pathlib import Path

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

REPORT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "cfm"
    / "cfm_geometry_audit_report.txt"
)

SAMPLE_SIZE = 1000

EXHAUSTIVE_SAMPLE_SIZE = 20

RANDOM_SEED = 20260920

K_VALUES = [64, 256, 1024, 4096]

TRIANGLE_CHUNK_SIZE = 10000

CFM_CRS = "EPSG:26711"

EARTHQUAKE_CRS = "EPSG:4326"

TRANSFORMER = Transformer.from_crs(
    EARTHQUAKE_CRS,
    CFM_CRS,
    always_xy=True,
)


# ============================================================
# OUTPUT / LOGGING
# ============================================================

def section(title: str) -> None:
    """Print a visible terminal section."""
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


# ============================================================
# COLUMN DETECTION
# ============================================================

def find_column(
    dataframe: pd.DataFrame,
    candidates: list[str],
    description: str,
) -> str:
    """Find a column using a list of possible names."""

    for candidate in candidates:
        if candidate in dataframe.columns:
            return candidate

    raise ValueError(
        f"Could not find {description}.\n"
        f"Expected one of: {candidates}\n"
        f"Available columns:\n{list(dataframe.columns)}"
    )


# ============================================================
# LOAD EARTHQUAKES
# ============================================================

def load_earthquakes() -> pd.DataFrame:
    """Load earthquake records."""

    section("1. LOADING EARTHQUAKES")

    if not EARTHQUAKE_FILE.exists():
        raise FileNotFoundError(
            f"Earthquake file not found:\n{EARTHQUAKE_FILE}"
        )

    earthquakes = pd.read_parquet(
        EARTHQUAKE_FILE
    )

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

    earthquakes["_audit_longitude"] = pd.to_numeric(
        earthquakes[lon_col],
        errors="coerce",
    )

    earthquakes["_audit_latitude"] = pd.to_numeric(
        earthquakes[lat_col],
        errors="coerce",
    )

    earthquakes["_audit_depth_km"] = pd.to_numeric(
        earthquakes[depth_col],
        errors="coerce",
    )

    valid = (
        earthquakes["_audit_longitude"].notna()
        & earthquakes["_audit_latitude"].notna()
        & earthquakes["_audit_depth_km"].notna()
    )

    print(f"Longitude column: {lon_col}")
    print(f"Latitude column:  {lat_col}")
    print(f"Depth column:     {depth_col}")

    print(
        f"Valid coordinates: {valid.sum():,}"
    )

    print(
        f"Missing coordinates: {(~valid).sum():,}"
    )

    return earthquakes


# ============================================================
# LOAD CFM VERTICES
# ============================================================

def load_vertices() -> pd.DataFrame:
    """Load CFM vertices."""

    section("2. LOADING CFM VERTICES")

    if not CFM_VERTICES_FILE.exists():
        raise FileNotFoundError(
            f"CFM vertex file not found:\n"
            f"{CFM_VERTICES_FILE}"
        )

    vertices = pd.read_csv(
        CFM_VERTICES_FILE
    )

    print(f"File: {CFM_VERTICES_FILE}")
    print(f"Rows: {len(vertices):,}")
    print(
        f"Columns: {list(vertices.columns)}"
    )

    for column in ["x", "y", "z"]:
        if column not in vertices.columns:
            raise ValueError(
                f"Required vertex column '{column}' "
                "was not found."
            )

    vertices = vertices.copy()

    vertices["x"] = pd.to_numeric(
        vertices["x"],
        errors="coerce",
    )

    vertices["y"] = pd.to_numeric(
        vertices["y"],
        errors="coerce",
    )

    vertices["z"] = pd.to_numeric(
        vertices["z"],
        errors="coerce",
    )

    valid = vertices[
        ["x", "y", "z"]
    ].notna().all(axis=1)

    print(
        f"Valid XYZ vertices: {valid.sum():,}"
    )

    print(
        f"Invalid XYZ vertices: {(~valid).sum():,}"
    )

    vertices = vertices.loc[
        valid
    ].reset_index(drop=True)

    print()
    print("CFM XYZ ranges:")

    print(
        f"  X: {vertices['x'].min():.3f} "
        f"-> {vertices['x'].max():.3f} m"
    )

    print(
        f"  Y: {vertices['y'].min():.3f} "
        f"-> {vertices['y'].max():.3f} m"
    )

    print(
        f"  Z: {vertices['z'].min():.3f} "
        f"-> {vertices['z'].max():.3f} m"
    )

    return vertices


# ============================================================
# TRIANGLE COLUMN DETECTION
# ============================================================

def identify_triangle_columns(
    triangles: pd.DataFrame,
) -> tuple[str, str, str]:
    """Identify the three triangle vertex-reference columns."""

    candidates = [
        ("v1", "v2", "v3"),
        ("vertex1", "vertex2", "vertex3"),
        ("vertex_1", "vertex_2", "vertex_3"),
        ("VRTX1", "VRTX2", "VRTX3"),
        ("vertex_a", "vertex_b", "vertex_c"),
    ]

    for candidate in candidates:
        if all(
            column in triangles.columns
            for column in candidate
        ):
            print(
                "Detected triangle columns:",
                candidate,
            )

            return candidate

    raise ValueError(
        "Could not identify triangle vertex columns.\n"
        f"Available columns:\n{list(triangles.columns)}"
    )


# ============================================================
# LOAD TRIANGLES
# ============================================================

def load_triangles() -> pd.DataFrame:
    """Load CFM triangles."""

    section("3. LOADING CFM TRIANGLES")

    if not CFM_TRIANGLES_FILE.exists():
        raise FileNotFoundError(
            f"CFM triangle file not found:\n"
            f"{CFM_TRIANGLES_FILE}"
        )

    triangles = pd.read_csv(
        CFM_TRIANGLES_FILE
    )

    print(f"File: {CFM_TRIANGLES_FILE}")
    print(f"Rows: {len(triangles):,}")
    print(
        f"Columns: {list(triangles.columns)}"
    )

    v1_col, v2_col, v3_col = (
        identify_triangle_columns(triangles)
    )

    for column in [
        v1_col,
        v2_col,
        v3_col,
    ]:
        triangles[column] = pd.to_numeric(
            triangles[column],
            errors="coerce",
        )

    return triangles


# ============================================================
# RESOLVE TRIANGLE INDICES
# ============================================================

def resolve_triangle_indices(
    triangles: pd.DataFrame,
    vertices: pd.DataFrame,
) -> tuple[pd.DataFrame, str]:
    """
    Validate triangle -> vertex references.

    Automatically handles:

        0-based:
            0 ... N-1

        1-based:
            1 ... N
    """

    section(
        "4. VALIDATING TRIANGLE -> VERTEX REFERENCES"
    )

    v1_col, v2_col, v3_col = (
        identify_triangle_columns(triangles)
    )

    references = triangles[
        [v1_col, v2_col, v3_col]
    ].to_numpy(
        dtype=np.float64
    )

    valid_numeric = np.isfinite(
        references
    ).all(axis=1)

    print(
        f"Triangles with numeric references: "
        f"{valid_numeric.sum():,}/"
        f"{len(triangles):,}"
    )

    triangles = triangles.loc[
        valid_numeric
    ].copy()

    references = references[
        valid_numeric
    ]

    integer_references = (
        references
        == np.floor(references)
    ).all(axis=1)

    if not integer_references.all():
        bad_count = (
            ~integer_references
        ).sum()

        raise ValueError(
            f"{bad_count:,} triangle rows contain "
            "non-integer vertex references."
        )

    references = references.astype(
        np.int64
    )

    vertex_count = len(vertices)

    minimum = int(
        references.min()
    )

    maximum = int(
        references.max()
    )

    print(
        f"Raw reference range: "
        f"{minimum} -> {maximum}"
    )

    print(
        f"Vertex table size: "
        f"{vertex_count:,}"
    )

    if (
        minimum >= 0
        and maximum < vertex_count
    ):
        indexing = "0-based"

        print(
            "Detected indexing convention: 0-based"
        )

    elif (
        minimum >= 1
        and maximum <= vertex_count
        and not np.any(
            references == 0
        )
    ):
        indexing = "1-based"

        print(
            "Detected indexing convention: 1-based"
        )

        references = references - 1

    else:
        raise ValueError(
            "Triangle references do not match either "
            "0-based or 1-based indexing.\n"
            f"Reference range: {minimum} -> {maximum}\n"
            f"Vertex count: {vertex_count:,}"
        )

    if (
        references.min() < 0
        or references.max() >= vertex_count
    ):
        raise ValueError(
            "Resolved triangle references are outside "
            "the vertex table."
        )

    triangles = triangles.reset_index(
        drop=True
    )

    triangles[v1_col] = references[:, 0]
    triangles[v2_col] = references[:, 1]
    triangles[v3_col] = references[:, 2]

    print(
        "Resolved reference range:",
        f"{references.min()} -> {references.max()}",
    )

    return triangles, indexing

# ============================================================
# BUILD TRIANGLE ARRAYS
# ============================================================

def build_triangle_arrays(
    vertices: pd.DataFrame,
    triangles: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Build:

        triangle_vertices
            shape = (N, 3, 3)

        triangle_centroids
            shape = (N, 3)
    """

    section("5. BUILDING TRIANGLE GEOMETRY")

    v1_col, v2_col, v3_col = (
        identify_triangle_columns(triangles)
    )

    xyz = vertices[
        ["x", "y", "z"]
    ].to_numpy(
        dtype=np.float64
    )

    v1 = triangles[
        v1_col
    ].to_numpy(
        dtype=np.int64
    )

    v2 = triangles[
        v2_col
    ].to_numpy(
        dtype=np.int64
    )

    v3 = triangles[
        v3_col
    ].to_numpy(
        dtype=np.int64
    )

    triangle_vertices = np.stack(
        [
            xyz[v1],
            xyz[v2],
            xyz[v3],
        ],
        axis=1,
    )

    triangle_centroids = (
        triangle_vertices.mean(
            axis=1
        )
    )

    print(
        "Triangle array shape:",
        triangle_vertices.shape,
    )

    print(
        "Centroid array shape:",
        triangle_centroids.shape,
    )

    edge_ab = (
        triangle_vertices[:, 1]
        - triangle_vertices[:, 0]
    )

    edge_bc = (
        triangle_vertices[:, 2]
        - triangle_vertices[:, 1]
    )

    edge_ca = (
        triangle_vertices[:, 0]
        - triangle_vertices[:, 2]
    )

    length_ab = np.linalg.norm(
        edge_ab,
        axis=1,
    )

    length_bc = np.linalg.norm(
        edge_bc,
        axis=1,
    )

    length_ca = np.linalg.norm(
        edge_ca,
        axis=1,
    )

    max_edge = np.maximum.reduce(
        [
            length_ab,
            length_bc,
            length_ca,
        ]
    )

    degenerate = (
        max_edge < 1e-6
    )

    print()
    print(
        "Triangle edge length:"
    )

    print(
        f"  median max-edge: "
        f"{np.median(max_edge):.2f} m"
    )

    print(
        f"  mean max-edge: "
        f"{np.mean(max_edge):.2f} m"
    )

    print(
        f"  max max-edge: "
        f"{np.max(max_edge):.2f} m"
    )

    print(
        f"  degenerate triangles: "
        f"{degenerate.sum():,}"
    )

    return (
        triangle_vertices,
        triangle_centroids,
    )


# ============================================================
# EARTHQUAKE 3D COORDINATES
# ============================================================

def build_earthquake_coordinates(
    earthquakes: pd.DataFrame,
) -> np.ndarray:
    """
    Convert earthquake longitude/latitude/depth to
    approximate CFM 3D coordinates.

    Horizontal:
        WGS84 -> EPSG:26711

    Vertical:
        positive earthquake depth
        ->
        negative Z
    """

    section(
        "6. BUILDING EARTHQUAKE 3D COORDINATES"
    )

    lon = earthquakes[
        "_audit_longitude"
    ].to_numpy(
        dtype=np.float64
    )

    lat = earthquakes[
        "_audit_latitude"
    ].to_numpy(
        dtype=np.float64
    )

    depth_km = earthquakes[
        "_audit_depth_km"
    ].to_numpy(
        dtype=np.float64
    )

    valid = (
        np.isfinite(lon)
        & np.isfinite(lat)
        & np.isfinite(depth_km)
    )

    coordinates = np.full(
        (len(earthquakes), 3),
        np.nan,
        dtype=np.float64,
    )

    x, y = TRANSFORMER.transform(
        lon[valid],
        lat[valid],
    )

    coordinates[
        valid,
        0
    ] = x

    coordinates[
        valid,
        1
    ] = y

    coordinates[
        valid,
        2
    ] = -depth_km[
        valid
    ] * 1000.0

    print(
        f"Valid hypocenters: "
        f"{valid.sum():,}"
    )

    print()
    print("Earthquake 3D ranges:")

    for index, axis in enumerate(
        ["X", "Y", "Z"]
    ):
        values = coordinates[
            :,
            index
        ]

        finite = np.isfinite(
            values
        )

        print(
            f"  {axis}: "
            f"{np.min(values[finite]):.2f}"
            f" -> "
            f"{np.max(values[finite]):.2f} m"
        )

    print()
    print(
        "Earthquake depth statistics:"
    )

    valid_depth = depth_km[
        np.isfinite(depth_km)
    ]

    print(
        f"  min: "
        f"{valid_depth.min():.3f} km"
    )

    print(
        f"  median: "
        f"{np.median(valid_depth):.3f} km"
    )

    print(
        f"  max: "
        f"{valid_depth.max():.3f} km"
    )

    return coordinates


# ============================================================
# POINT -> TRIANGLE DISTANCE
# ============================================================

def point_to_triangle_distance_squared(
    point: np.ndarray,
    triangle: np.ndarray,
) -> float:
    """
    Exact squared Euclidean distance from a point to
    a triangle in 3D.

    triangle shape:
        (3, 3)
    """

    a = triangle[0]
    b = triangle[1]
    c = triangle[2]

    ab = b - a
    ac = c - a
    ap = point - a

    d1 = np.dot(ab, ap)
    d2 = np.dot(ac, ap)

    if d1 <= 0.0 and d2 <= 0.0:
        diff = point - a

        return float(
            np.dot(diff, diff)
        )

    bp = point - b

    d3 = np.dot(ab, bp)
    d4 = np.dot(ac, bp)

    if d3 >= 0.0 and d4 <= d3:
        diff = point - b

        return float(
            np.dot(diff, diff)
        )

    vc = (
        d1 * d4
        - d3 * d2
    )

    if (
        vc <= 0.0
        and d1 >= 0.0
        and d3 <= 0.0
    ):
        denominator = d1 - d3

        if denominator == 0.0:
            diff = point - a

            return float(
                np.dot(diff, diff)
            )

        v = d1 / denominator

        closest = (
            a + v * ab
        )

        diff = (
            point - closest
        )

        return float(
            np.dot(diff, diff)
        )

    cp = point - c

    d5 = np.dot(ab, cp)
    d6 = np.dot(ac, cp)

    if d6 >= 0.0 and d5 <= d6:
        diff = point - c

        return float(
            np.dot(diff, diff)
        )

    vb = (
        d5 * d2
        - d1 * d6
    )

    if (
        vb <= 0.0
        and d2 >= 0.0
        and d6 <= 0.0
    ):
        denominator = d2 - d6

        if denominator == 0.0:
            diff = point - a

            return float(
                np.dot(diff, diff)
            )

        w = d2 / denominator

        closest = (
            a + w * ac
        )

        diff = (
            point - closest
        )

        return float(
            np.dot(diff, diff)
        )

    va = (
        d3 * d6
        - d5 * d4
    )

    if (
        va <= 0.0
        and (d4 - d3) >= 0.0
        and (d5 - d6) >= 0.0
    ):
        denominator = (
            (d4 - d3)
            + (d5 - d6)
        )

        if denominator == 0.0:
            diff = point - b

            return float(
                np.dot(diff, diff)
            )

        w = (
            d4 - d3
        ) / denominator

        closest = (
            b + w * (c - b)
        )

        diff = (
            point - closest
        )

        return float(
            np.dot(diff, diff)
        )

    denominator = (
        va + vb + vc
    )

    if denominator == 0.0:
        distances = [
            np.sum((point - a) ** 2),
            np.sum((point - b) ** 2),
            np.sum((point - c) ** 2),
        ]

        return float(
            min(distances)
        )

    v = vb / denominator
    w = vc / denominator

    closest = (
        a
        + ab * v
        + ac * w
    )

    diff = (
        point - closest
    )

    return float(
        np.dot(diff, diff)
    )


# ============================================================
# POINT -> TRIANGLE FOR CANDIDATES
# ============================================================

def point_to_candidates(
    point: np.ndarray,
    candidate_indices: np.ndarray,
    triangle_vertices: np.ndarray,
) -> tuple[float, int]:
    """Calculate minimum distance among candidate triangles."""

    best_distance_squared = np.inf
    best_index = -1

    for triangle_index in candidate_indices:

        triangle = triangle_vertices[
            triangle_index
        ]

        distance_squared = (
            point_to_triangle_distance_squared(
                point,
                triangle,
            )
        )

        if (
            distance_squared
            < best_distance_squared
        ):
            best_distance_squared = (
                distance_squared
            )

            best_index = int(
                triangle_index
            )

    if best_index < 0:
        return np.nan, -1

    return (
        np.sqrt(
            best_distance_squared
        ) / 1000.0,
        best_index,
    )


# ============================================================
# CENTROID KD-TREE AUDIT
# ============================================================

def centroid_k_audit(
    sample_indices: np.ndarray,
    earthquake_coordinates: np.ndarray,
    triangle_vertices: np.ndarray,
    triangle_centroids: np.ndarray,
) -> pd.DataFrame:
    """
    Compare centroid-K searches.

    This does NOT claim the centroid method is exact.
    It is specifically an audit of its convergence.
    """

    section(
        "7. CENTROID-K CONVERGENCE AUDIT"
    )

    tree = cKDTree(
        triangle_centroids
    )

    records = []

    for counter, earthquake_index in enumerate(
        sample_indices
    ):

        point = earthquake_coordinates[
            earthquake_index
        ]

        record = {
            "earthquake_index":
                int(earthquake_index)
        }

        for k in K_VALUES:

            distances, candidate_indices = (
                tree.query(
                    point,
                    k=k,
                )
            )

            candidate_indices = np.atleast_1d(
                candidate_indices
            )

            distance_km, triangle_index = (
                point_to_candidates(
                    point,
                    candidate_indices,
                    triangle_vertices,
                )
            )

            record[
                f"distance_k{k}_km"
            ] = distance_km

            record[
                f"triangle_k{k}"
            ] = triangle_index

        records.append(record)

        if (
            (counter + 1) % 100 == 0
            or counter + 1 == len(
                sample_indices
            )
        ):
            print(
                f"  processed "
                f"{counter + 1:,}/"
                f"{len(sample_indices):,}"
            )

    result = pd.DataFrame(
        records
    )

    for previous_k, current_k in zip(
        K_VALUES[:-1],
        K_VALUES[1:],
    ):

        previous = result[
            f"distance_k{previous_k}_km"
        ]

        current = result[
            f"distance_k{current_k}_km"
        ]

        result[
            f"change_{previous_k}_{current_k}_km"
        ] = (
            current - previous
        ).abs()

    print()
    print(
        "Centroid-K sample statistics:"
    )

    for k in K_VALUES:

        column = (
            f"distance_k{k}_km"
        )

        values = result[
            column
        ].to_numpy()

        print(
            f"  K={k}: "
            f"median="
            f"{np.median(values):.4f} km, "
            f"mean="
            f"{np.mean(values):.4f} km, "
            f"max="
            f"{np.max(values):.4f} km"
        )

    return result


# ============================================================
# EXHAUSTIVE POINT -> TRIANGLE
# ============================================================

def exhaustive_distance_for_point(
    point: np.ndarray,
    triangle_vertices: np.ndarray,
) -> tuple[float, int]:
    """
    Calculate the true minimum over every triangle.

    This is deliberately used only for a very small sample.
    """

    best_squared = np.inf
    best_triangle = -1

    triangle_count = len(
        triangle_vertices
    )

    for start in range(
        0,
        triangle_count,
        TRIANGLE_CHUNK_SIZE,
    ):

        end = min(
            start + TRIANGLE_CHUNK_SIZE,
            triangle_count,
        )

        for triangle_index in range(
            start,
            end,
        ):

            triangle = (
                triangle_vertices[
                    triangle_index
                ]
            )

            distance_squared = (
                point_to_triangle_distance_squared(
                    point,
                    triangle,
                )
            )

            if (
                distance_squared
                < best_squared
            ):
                best_squared = (
                    distance_squared
                )

                best_triangle = (
                    triangle_index
                )

    if best_triangle < 0:
        return np.nan, -1

    return (
        np.sqrt(
            best_squared
        ) / 1000.0,
        best_triangle,
    )


def exhaustive_audit(
    sample_indices: np.ndarray,
    earthquake_coordinates: np.ndarray,
    triangle_vertices: np.ndarray,
) -> pd.DataFrame:
    """
    Exhaustively compare each selected earthquake against
    every CFM triangle.

    Only 20 earthquakes are used.
    """

    section(
        "8. EXHAUSTIVE POINT-TO-TRIANGLE AUDIT"
    )

    records = []

    for counter, earthquake_index in enumerate(
        sample_indices
    ):

        point = earthquake_coordinates[
            earthquake_index
        ]

        distance_km, triangle_index = (
            exhaustive_distance_for_point(
                point,
                triangle_vertices,
            )
        )

        records.append(
            {
                "earthquake_index":
                    int(earthquake_index),
                "exhaustive_distance_km":
                    distance_km,
                "exhaustive_triangle":
                    triangle_index,
            }
        )

        print(
            f"  exhaustive "
            f"{counter + 1:,}/"
            f"{len(sample_indices):,}: "
            f"distance="
            f"{distance_km:.6f} km, "
            f"triangle="
            f"{triangle_index}"
        )

    return pd.DataFrame(
        records
  )


# ============================================================
# NEAREST VERTEX AUDIT
# ============================================================

def nearest_vertex_audit(
    sample_indices: np.ndarray,
    earthquake_coordinates: np.ndarray,
    vertices: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate true 3D nearest-vertex distance.

    This is different from the previous feature, which was
    primarily a 2D longitude/latitude distance.
    """

    section(
        "9. 3D NEAREST-VERTEX AUDIT"
    )

    xyz = vertices[
        ["x", "y", "z"]
    ].to_numpy(
        dtype=np.float64
    )

    tree = cKDTree(
        xyz
    )

    points = earthquake_coordinates[
        sample_indices
    ]

    distances, vertex_indices = (
        tree.query(
            points,
            k=1,
        )
    )

    return pd.DataFrame(
        {
            "earthquake_index":
                sample_indices,
            "nearest_vertex_3d_km":
                distances / 1000.0,
            "nearest_vertex_index":
                vertex_indices,
        }
    )


# ============================================================
# TRIANGLE FAULT NAME
# ============================================================

def attach_fault_names(
    audit: pd.DataFrame,
    triangles: pd.DataFrame,
) -> pd.DataFrame:
    """Attach fault names when available."""

    possible_columns = [
        "fault_name",
        "Fault Name",
        "CFM6.0 Fault Object Name",
        "object_name",
        "name",
    ]

    fault_column = None

    for column in possible_columns:
        if column in triangles.columns:
            fault_column = column
            break

    if fault_column is None:
        print(
            "No fault-name column found in triangle CSV."
        )

        return audit

    fault_names = (
        triangles[
            fault_column
        ]
        .astype("string")
        .reset_index(drop=True)
    )

    audit = audit.copy()

    for source_column, output_column in [
        (
            "exhaustive_triangle",
            "exhaustive_fault",
        ),
        (
            "triangle_k64",
            "fault_k64",
        ),
        (
            "triangle_k256",
            "fault_k256",
        ),
        (
            "triangle_k1024",
            "fault_k1024",
        ),
        (
            "triangle_k4096",
            "fault_k4096",
        ),
    ]:

        if source_column not in audit.columns:
            continue

        indices = audit[
            source_column
        ].to_numpy()

        values = pd.Series(
            pd.NA,
            index=audit.index,
            dtype="string",
        )

        valid = (
            (indices >= 0)
            & (
                indices
                < len(fault_names)
            )
        )

        values.loc[valid] = (
            fault_names.iloc[
                indices[valid]
            ].to_numpy()
        )

        audit[
            output_column
        ] = values

    print(
        f"Fault-name column used: "
        f"{fault_column}"
    )

    return audit


# ============================================================
# MERGE AUDIT RESULTS
# ============================================================

def merge_results(
    centroid_result: pd.DataFrame,
    exhaustive_result: pd.DataFrame,
    vertex_result: pd.DataFrame,
) -> pd.DataFrame:
    """Merge all audit measurements."""

    result = centroid_result.merge(
        exhaustive_result,
        on="earthquake_index",
        how="left",
    )

    result = result.merge(
        vertex_result,
        on="earthquake_index",
        how="left",
    )

    result[
        "centroid_k64_error_vs_exhaustive_km"
    ] = (
        result["distance_k64_km"]
        - result["exhaustive_distance_km"]
    ).abs()

    result[
        "centroid_k4096_error_vs_exhaustive_km"
    ] = (
        result["distance_k4096_km"]
        - result["exhaustive_distance_km"]
    ).abs()

    result[
        "triangle_to_vertex_ratio"
    ] = (
        result[
            "exhaustive_distance_km"
        ]
        / result[
            "nearest_vertex_3d_km"
        ].replace(0, np.nan)
    )

    return result


# ============================================================
# SAMPLE INFORMATION
# ============================================================

def add_earthquake_information(
    audit: pd.DataFrame,
    earthquakes: pd.DataFrame,
) -> pd.DataFrame:
    """Attach earthquake coordinates and identifiers."""

    result = audit.copy()

    selected = earthquakes.iloc[
        result["earthquake_index"].to_numpy()
    ].reset_index(
        drop=True
    )

    result["longitude"] = (
        selected[
            "_audit_longitude"
        ].to_numpy()
    )

    result["latitude"] = (
        selected[
            "_audit_latitude"
        ].to_numpy()
    )

    result["depth_km"] = (
        selected[
            "_audit_depth_km"
        ].to_numpy()
    )

    if "earthquake_id" in selected.columns:
        result["earthquake_id"] = (
            selected[
                "earthquake_id"
            ].to_numpy()
        )

    return result


# ============================================================
# SUSPICIOUS CASES
# ============================================================

def identify_suspicious_cases(
    audit: pd.DataFrame,
) -> pd.DataFrame:
    """
    Identify geometrically interesting cases.

    These are not automatically errors.
    They are cases worth inspecting.
    """

    suspicious = audit.copy()

    suspicious["suspicious"] = False
    suspicious["reason"] = ""

    change = (
        suspicious[
            "distance_k64_km"
        ]
        - suspicious[
            "distance_k4096_km"
        ]
    ).abs()

    mask = change > 5.0

    suspicious.loc[
        mask,
        "suspicious",
    ] = True

    suspicious.loc[
        mask,
        "reason",
    ] += (
        "K64_vs_K4096_change>5km; "
    )

    error = suspicious[
        "centroid_k4096_error_vs_exhaustive_km"
    ]

    mask = error > 1.0

    suspicious.loc[
        mask,
        "suspicious",
    ] = True

    suspicious.loc[
        mask,
        "reason",
    ] += (
        "K4096_error_vs_exhaustive>1km; "
    )

    mask = (
        suspicious[
            "exhaustive_distance_km"
        ] > 100.0
    )

    suspicious.loc[
        mask,
        "suspicious",
    ] = True

    suspicious.loc[
        mask,
        "reason",
    ] += (
        "surface_distance>100km; "
    )

    difference = (
        suspicious[
            "exhaustive_distance_km"
        ]
        - suspicious[
            "nearest_vertex_3d_km"
        ]
    ).abs()

    mask = difference > 20.0

    suspicious.loc[
        mask,
        "suspicious",
    ] = True

    suspicious.loc[
        mask,
        "reason",
    ] += (
        "surface_vs_vertex_difference>20km; "
    )

    return suspicious


# ============================================================
# REPORT
# ============================================================

def build_report(
    earthquakes: pd.DataFrame,
    vertices: pd.DataFrame,
    triangles: pd.DataFrame,
    indexing: str,
    centroid_result: pd.DataFrame,
    audit: pd.DataFrame,
    suspicious: pd.DataFrame,
) -> str:
    """Create the final audit report."""

    lines = []

    lines.append(
        "CFM6.0 GEOMETRY AUDIT REPORT"
    )

    lines.append(
        "=" * 72
    )

    lines.append("")

    lines.append(
        "DATASET SIZES"
    )

    lines.append(
        f"Earthquakes: {len(earthquakes):,}"
    )

    lines.append(
        f"CFM vertices: {len(vertices):,}"
    )

    lines.append(
        f"CFM triangles: {len(triangles):,}"
    )

    lines.append("")

    lines.append(
        "TRIANGLE INDEXING"
    )

    lines.append(
        f"Detected convention: {indexing}"
    )

    lines.append("")

    lines.append(
        "CFM XYZ RANGES"
    )

    for column in ["x", "y", "z"]:

        lines.append(
            f"{column}: "
            f"{vertices[column].min():.3f}"
            f" -> "
            f"{vertices[column].max():.3f} m"
        )

    lines.append("")

    lines.append(
        "AUDIT SAMPLES"
    )

    lines.append(
        f"Centroid convergence sample: "
        f"{len(centroid_result):,}"
    )

    lines.append(
        f"Exhaustive sample: "
        f"{len(audit):,}"
    )

    lines.append("")

    lines.append(
        "CENTROID K CONVERGENCE"
    )

    for previous_k, current_k in zip(
        K_VALUES[:-1],
        K_VALUES[1:],
    ):

        column = (
            f"change_"
            f"{previous_k}_"
            f"{current_k}_km"
        )

        values = centroid_result[
            column
        ].to_numpy()

        lines.append(
            f"K {previous_k} -> "
            f"K {current_k}: "
            f"median change="
            f"{np.median(values):.6f} km, "
            f"mean change="
            f"{np.mean(values):.6f} km, "
            f"max change="
            f"{np.max(values):.6f} km"
        )

    lines.append("")

    lines.append(
        "EXHAUSTIVE DISTANCE"
    )

    values = audit[
        "exhaustive_distance_km"
    ].to_numpy()

    lines.append(
        f"median: "
        f"{np.median(values):.6f} km"
    )

    lines.append(
        f"mean: "
        f"{np.mean(values):.6f} km"
    )

    lines.append(
        f"min: "
        f"{np.min(values):.6f} km"
    )

    lines.append(
        f"max: "
        f"{np.max(values):.6f} km"
    )

    lines.append("")

    lines.append(
        "K=64 ERROR AGAINST EXHAUSTIVE"
    )

    values = audit[
        "centroid_k64_error_vs_exhaustive_km"
    ].to_numpy()

    lines.append(
        f"median absolute error: "
        f"{np.median(values):.6f} km"
    )

    lines.append(
        f"mean absolute error: "
        f"{np.mean(values):.6f} km"
    )

    lines.append(
        f"max absolute error: "
        f"{np.max(values):.6f} km"
    )

    lines.append(
        f">1 km errors: "
        f"{(values > 1).sum():,}"
        f"/{len(values):,}"
    )

    lines.append("")

    lines.append(
        "K=4096 ERROR AGAINST EXHAUSTIVE"
    )

    values = audit[
        "centroid_k4096_error_vs_exhaustive_km"
    ].to_numpy()

    lines.append(
        f"median absolute error: "
        f"{np.median(values):.6f} km"
    )

    lines.append(
        f"mean absolute error: "
        f"{np.mean(values):.6f} km"
    )

    lines.append(
        f"max absolute error: "
        f"{np.max(values):.6f} km"
    )

    lines.append(
        f">1 km errors: "
        f"{(values > 1).sum():,}"
        f"/{len(values):,}"
    )

    lines.append("")

    lines.append(
        "3D VERTEX VS 3D SURFACE"
    )

    surface = audit[
        "exhaustive_distance_km"
    ].to_numpy()

    vertex = audit[
        "nearest_vertex_3d_km"
    ].to_numpy()

    difference = np.abs(
        surface - vertex
    )

    lines.append(
        f"surface median: "
        f"{np.median(surface):.6f} km"
    )

    lines.append(
        f"vertex median: "
        f"{np.median(vertex):.6f} km"
    )

    lines.append(
        f"median absolute difference: "
        f"{np.median(difference):.6f} km"
    )

    lines.append(
        f"max absolute difference: "
        f"{np.max(difference):.6f} km"
    )

    lines.append("")

    lines.append(
        "SUSPICIOUS CASES"
    )

    lines.append(
        f"Flagged cases: "
        f"{suspicious['suspicious'].sum():,}"
        f"/{len(suspicious):,}"
    )

    lines.append("")

    lines.append(
        "INTERPRETATION NOTE"
    )

    lines.append(
        "This audit does not assume that a large "
        "earthquake-to-CFM distance is an error."
    )

    lines.append(
        "It identifies cases where the centroid "
        "candidate method disagrees with exhaustive "
        "point-to-triangle geometry."
    )

    lines.append(
        "The exhaustive calculation over all CFM "
        "triangles is the reference for the sampled "
        "events."
    )

    lines.append(
        "No XGBoost feature is modified by this script."
    )

    return "\n".join(lines)


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    """Run the complete geometry audit."""

    section(
        "CFM6.0 GEOMETRY AUDIT START"
    )

    print(
        f"Random seed: {RANDOM_SEED}"
    )

    print(
        f"Centroid sample: "
        f"{SAMPLE_SIZE:,}"
    )

    print(
        f"Exhaustive sample: "
        f"{EXHAUSTIVE_SAMPLE_SIZE:,}"
    )

    print(
        f"K values: "
        f"{K_VALUES}"
    )

    earthquakes = (
        load_earthquakes()
    )

    vertices = (
        load_vertices()
    )

    triangles = (
        load_triangles()
    )

    triangles, indexing = (
        resolve_triangle_indices(
            triangles,
            vertices,
        )
    )

    (
        triangle_vertices,
        triangle_centroids,
    ) = build_triangle_arrays(
        vertices,
        triangles,
    )

    earthquake_coordinates = (
        build_earthquake_coordinates(
            earthquakes
        )
    )

    valid_indices = np.where(
        np.isfinite(
            earthquake_coordinates
        ).all(axis=1)
    )[0]

    if len(valid_indices) < SAMPLE_SIZE:
        raise ValueError(
            "Not enough valid earthquake coordinates "
            "for requested sample."
        )

    rng = np.random.default_rng(
        RANDOM_SEED
    )

    centroid_sample = (
        rng.choice(
            valid_indices,
            size=SAMPLE_SIZE,
            replace=False,
        )
    )

    exhaustive_sample = (
        centroid_sample[
            :EXHAUSTIVE_SAMPLE_SIZE
        ]
    )

    centroid_result = (
        centroid_k_audit(
            centroid_sample,
            earthquake_coordinates,
            triangle_vertices,
            triangle_centroids,
        )
    )

    exhaustive_result = (
        exhaustive_audit(
            exhaustive_sample,
            earthquake_coordinates,
            triangle_vertices,
        )
    )

    vertex_result = (
        nearest_vertex_audit(
            exhaustive_sample,
            earthquake_coordinates,
            vertices,
        )
    )

    audit = merge_results(
        centroid_result[
            centroid_result[
                "earthquake_index"
            ].isin(
                exhaustive_sample
            )
        ].copy(),
        exhaustive_result,
        vertex_result,
    )

    audit = attach_fault_names(
        audit,
        triangles,
    )

    audit = add_earthquake_information(
        audit,
        earthquakes,
    )

    suspicious = (
        identify_suspicious_cases(
            audit
        )
    )

    audit_output = (
        PROJECT_ROOT
        / "data"
        / "processed"
        / "cfm"
        / "cfm_geometry_audit_samples.csv"
    )

    audit.to_csv(
        audit_output,
        index=False,
    )

    report = build_report(
        earthquakes,
        vertices,
        triangles,
        indexing,
        centroid_result,
        audit,
        suspicious,
    )

    REPORT_FILE.write_text(
        report,
        encoding="utf-8",
    )

    section(
        "CFM6.0 GEOMETRY AUDIT COMPLETE"
    )

    print(
        f"Report:\n{REPORT_FILE}"
    )

    print()
    print(
        f"Samples:\n{audit_output}"
    )

    print()
    print(
        "Triangle indexing:",
        indexing,
    )

    print()
    print(
        "Exhaustive reference:"
    )

    print(
        f"  median = "
        f"{audit['exhaustive_distance_km'].median():.6f} km"
    )

    print(
        f"  mean = "
        f"{audit['exhaustive_distance_km'].mean():.6f} km"
    )

    print()
    print(
        "Centroid K=64 vs exhaustive:"
    )

    print(
        f"  median error = "
        f"{audit['centroid_k64_error_vs_exhaustive_km'].median():.6f} km"
    )

    print(
        f"  max error = "
        f"{audit['centroid_k64_error_vs_exhaustive_km'].max():.6f} km"
    )

    print()
    print(
        "Centroid K=4096 vs exhaustive:"
    )

    print(
        f"  median error = "
        f"{audit['centroid_k4096_error_vs_exhaustive_km'].median():.6f} km"
    )

    print(
        f"  max error = "
        f"{audit['centroid_k4096_error_vs_exhaustive_km'].max():.6f} km"
    )

    print()
    print(
        "Flagged suspicious cases:",
        int(
            suspicious["suspicious"].sum()
        ),
    )

    print()
    print(
        "IMPORTANT:"
    )

    print(
        "Do not integrate the 3D feature into XGBoost yet."
    )

    print(
        "Inspect cfm_geometry_audit_report.txt first."
    )


if __name__ == "__main__":
    main()
