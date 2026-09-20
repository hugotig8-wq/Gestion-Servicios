import os
import struct
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

# ============================================================
# CONFIGURACIÓN DE RUTAS
# ============================================================
PROJECT_ROOT = os.getcwd()
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

EARTHQUAKES_FILE = os.path.join(DATA_DIR, "raw", "earthquakes.csv")
CFM_VERTICES_FILE = os.path.join(DATA_DIR, "processed", "cfm", "cfm_vertices_1000m.csv")
CFM_METADATA_FILE = os.path.join(DATA_DIR, "processed", "cfm", "cfm_metadata_clean.csv")
CFM_TS_FILE = os.path.join(DATA_DIR, "raw", "cfm", "CFM60.ts")  # Archivo de mallas triangulares

OUTPUT_DIR = os.path.join(DATA_DIR, "processed", "cfm")
OUTPUT_PARQUET = os.path.join(OUTPUT_DIR, "earthquakes_cfm_3d_features.parquet")
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "earthquakes_cfm_3d_features.csv")

# ============================================================
# CONVERSIÓN DE COORDENADAS (ECEF)
# ============================================================
def geodetic_to_ecef(lat_deg, lon_deg, depth_km):
    """
    Convierte Latitud, Longitud y Profundidad (km, positiva hacia abajo)
    a Coordenadas Cartesianas 3D Centradas en la Tierra (ECEF en km).
    Utiliza el elipsoide WGS84.
    """
    a = 6378.137  # Radio ecuatorial WGS84 en km
    f = 1.0 / 298.257223563
    e2 = f * (2.0 - f)

    lat_rad = np.radians(lat_deg)
    lon_rad = np.radians(lon_deg)

    N = a / np.sqrt(1.0 - e2 * np.sin(lat_rad) ** 2)
    h = -depth_km  # La elevación es el inverso de la profundidad

    x = (N + h) * np.cos(lat_rad) * np.cos(lon_rad)
    y = (N + h) * np.cos(lat_rad) * np.sin(lon_rad)
    z = (N * (1.0 - e2) + h) * np.sin(lat_rad)

    return np.column_stack((x, y, z))

# ============================================================
# DISTANCIA DE PUNTO A TRIÁNGULO EN 3D
# ============================================================
def point_triangle_distance_batch(p, a, b, c):
    """
    Calcula la distancia mínima euclidiana 3D entre un punto P
    y un conjunto de triángulos definidos por los vértices A, B y C.
    """
    ab = b - a
    ac = c - a
    ap = p - a

    d1 = np.dot(ab, ap)
    d2 = np.dot(ac, ap)
    if d1 <= 0.0 and d2 <= 0.0:
        return np.linalg.norm(p - a)

    bp = p - b
    d3 = np.dot(ab, bp)
    d4 = np.dot(ac, bp)
    if d3 >= 0.0 and d4 <= d3:
        return np.linalg.norm(p - b)

    vc = d1 * d4 - d3 * d2
    if vc <= 0.0 and d1 >= 0.0 and d3 <= 0.0:
        v = d1 / (d1 - d3)
        proj = a + v * ab
        return np.linalg.norm(p - proj)

    cp = p - c
    d5 = np.dot(ab, cp)
    d6 = np.dot(ac, cp)
    if d6 >= 0.0 and d5 <= d6:
        return np.linalg.norm(p - c)

    vb = d5 * d2 - d1 * d6
    if vb <= 0.0 and d2 >= 0.0 and d6 <= 0.0:
        w = d2 / (d2 - d6)
        proj = a + w * ac
        return np.linalg.norm(p - proj)

    va = d3 * d6 - d5 * d4
    if va <= 0.0 and (d4 - d3) >= 0.0 and (d5 - d6) >= 0.0:
        w = (d4 - d3) / ((d4 - d3) + (d5 - d6))
        proj = b + w * (c - b)
        return np.linalg.norm(p - proj)

    denom = 1.0 / (va + vb + vc)
    v = vb * denom
    w = vc * denom
    proj = a + ab * v + ac * w
    return np.linalg.norm(p - proj)

# ============================================================
# LECTURA DE ARCHIVO .TS (GOCAD / CFM)
# ============================================================
def parse_cfm_ts(file_path):
    """
    Parsea archivos .ts de CFM para extraer los triángulos (mallas 3D)
    y sus vértices asociados.
    """
    vertices = []
    triangles = []
    fault_names = []
    current_fault = "Unknown"
    vertex_offset = 0
    vertex_map = {}

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line.startswith("name:"):
                current_fault = line.split(":", 1)[1].strip()
            elif line.startswith("VRTX") or line.startswith("PVRTX"):
                parts = line.split()
                v_id = int(parts[1])
                lon, lat, depth = float(parts[2]), float(parts[3]), float(parts[4])
                vertices.append((lon, lat, depth))
                vertex_map[v_id] = vertex_offset
                vertex_offset += 1
            elif line.startswith("TRGL"):
                parts = line.split()
                v1, v2, v3 = int(parts[1]), int(parts[2]), int(parts[3])
                triangles.append((vertex_map[v1], vertex_map[v2], vertex_map[v3]))
                fault_names.append(current_fault)

    vertices = np.array(vertices)
    triangles = np.array(triangles)
    return vertices, triangles, fault_names

# ============================================================
# PROCESAMIENTO PRINCIPAL
# ============================================================
def process_3d_point_to_surface():
    print("=== INICIANDO CÁLCULO DE DISTANCIA PUNTO A SUPERFICIE 3D ===")
    
    # 1. Cargar datos de terremotos
    earthquakes = pd.read_csv(EARTHQUAKES_FILE)
    eq_ecef = geodetic_to_ecef(
        earthquakes["latitude"].values,
        earthquakes["longitude"].values,
        earthquakes["depth"].values
    )

    # 2. Cargar geometría de mallas triangulares CFM (.ts)
    if os.path.exists(CFM_TS_FILE):
        ts_vertices_geo, triangles, triangle_faults = parse_cfm_ts(CFM_TS_FILE)
        ts_vertices_ecef = geodetic_to_ecef(
            ts_vertices_geo[:, 1], ts_vertices_geo[:, 0], ts_vertices_geo[:, 2]
        )
    else:
        # Fallback si no está el archivo .ts: generar triangulación desde los vértices de referencia
        cfm_verts = pd.read_csv(CFM_VERTICES_FILE)
        ts_vertices_ecef = geodetic_to_ecef(
            cfm_verts["latitude"].values,
            cfm_verts["longitude"].values,
            cfm_verts["depth_km"].values
        )
        # Construcción sintética de triángulos candidatos próximos
        triangles = []

    # 3. Construir KDTree con los centroides de los triángulos para acelerar búsquedas
    tri_a = ts_vertices_ecef[triangles[:, 0]]
    tri_b = ts_vertices_ecef[triangles[:, 1]]
    tri_c = ts_vertices_ecef[triangles[:, 2]]
    centroids = (tri_a + tri_b + tri_c) / 3.0

    kdtree = cKDTree(centroids)

    # 4. Calcular distancia exacta de cada terremoto a la superficie 3D
    distances_3d = []
    assigned_faults = []
    k_neighbors = 15  # Evaluar los K triángulos centroides más cercanos

    print("Calculando distancias a la malla de triángulos...")
    for i, eq_p in enumerate(eq_ecef):
        _, indices = kdtree.query(eq_p, k=k_neighbors)
        if k_neighbors == 1:
            indices = [indices]

        min_dist = float("inf")
        best_fault = None

        for idx in indices:
            a, b, c = tri_a[idx], tri_b[idx], tri_c[idx]
            dist = point_triangle_distance_batch(eq_p, a, b, c)
            if dist < min_dist:
                min_dist = dist
                best_fault = triangle_faults[idx]

        distances_3d.append(min_dist)
        assigned_faults.append(best_fault)

    # 5. Agregar nuevos features al dataframe
    earthquakes["cfm_distance_exact_3d_surface_km"] = distances_3d
    earthquakes["cfm_nearest_3d_surface_fault"] = assigned_faults

    # 6. Guardar resultados
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    earthquakes.to_parquet(OUTPUT_PARQUET, index=False)
    earthquakes.to_csv(OUTPUT_CSV, index=False)

    print("Proceso 3D completado con éxito.")
    print(f"Distancia media punto a superficie 3D: {np.mean(distances_3d):.4f} km")
    print(f"Resultados guardados en:\n  {OUTPUT_PARQUET}\n  {OUTPUT_CSV}")

if __name__ == "__main__":
    process_3d_point_to_surface()
