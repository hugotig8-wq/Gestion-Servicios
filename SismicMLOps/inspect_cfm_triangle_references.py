from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent

CFM_DIR = PROJECT_ROOT / "data" / "processed" / "cfm"

VERTICES_FILE = CFM_DIR / "cfm_vertices_1000m.csv"
TRIANGLES_FILE = CFM_DIR / "cfm_triangles_1000m.csv"


def main():
    print("=" * 80)
    print("CFM TRIANGLE / VERTEX REFERENCE DIAGNOSTIC")
    print("=" * 80)

    vertices = pd.read_csv(VERTICES_FILE)
    triangles = pd.read_csv(TRIANGLES_FILE)

    # --------------------------------------------------------------
    # VERTICES
    # --------------------------------------------------------------

    print()
    print("VERTEX FILE")
    print("-" * 80)

    print(f"Rows: {len(vertices):,}")
    print(f"Columns: {len(vertices.columns)}")

    print()
    print("Vertex columns:")

    for i, column in enumerate(vertices.columns):
        print(f"{i}: {column}")

    print()
    print("First 10 vertex rows:")

    print(
        vertices.head(10).to_string(
            index=False
        )
    )

    # --------------------------------------------------------------
    # TRIANGLES
    # --------------------------------------------------------------

    print()
    print("TRIANGLE FILE")
    print("-" * 80)

    print(f"Rows: {len(triangles):,}")
    print(f"Columns: {len(triangles.columns)}")

    print()
    print("Triangle columns:")

    for i, column in enumerate(triangles.columns):
        print(f"{i}: {column}")

    print()
    print("First 10 triangle rows:")

    print(
        triangles.head(10).to_string(
            index=False
        )
    )

    # --------------------------------------------------------------
    # POSSIBLE TRIANGLE REFERENCE COLUMNS
    # --------------------------------------------------------------

    print()
    print("POSSIBLE TRIANGLE REFERENCE COLUMNS")
    print("-" * 80)

    reference_candidates = [
        "v1",
        "v2",
        "v3",
        "vertex1",
        "vertex2",
        "vertex3",
        "vertex_1",
        "vertex_2",
        "vertex_3",
        "VRTX1",
        "VRTX2",
        "VRTX3",
        "vertex_a",
        "vertex_b",
        "vertex_c",
    ]

    found = []

    for column in reference_candidates:

        if column in triangles.columns:

            found.append(column)

            series = pd.to_numeric(
                triangles[column],
                errors="coerce",
            )

            print()
            print(f"{column}")
            print(
                f"  dtype: {triangles[column].dtype}"
            )
            print(
                f"  nulls: {series.isna().sum():,}"
            )
            print(
                f"  min: {series.min()}"
            )
            print(
                f"  max: {series.max()}"
            )
            print(
                f"  unique: {series.nunique():,}"
            )

    if not found:
        print("No standard reference columns detected.")

    # --------------------------------------------------------------
    # ALL INTEGER-LIKE TRIANGLE COLUMNS
    # --------------------------------------------------------------

    print()
    print("INTEGER-LIKE TRIANGLE COLUMNS")
    print("-" * 80)

    for column in triangles.columns:

        numeric = pd.to_numeric(
            triangles[column],
            errors="coerce",
        )

        if numeric.notna().all():

            integer_like = (
                (numeric % 1) == 0
            ).all()

            if integer_like:

                print(
                    f"{column}: "
                    f"min={numeric.min()}, "
                    f"max={numeric.max()}, "
                    f"unique={numeric.nunique():,}"
                )

    # --------------------------------------------------------------
    # POSSIBLE OBJECT / FAULT COLUMNS
    # --------------------------------------------------------------

    print()
    print("POSSIBLE OBJECT / FAULT COLUMNS")
    print("-" * 80)

    object_candidates = [
        "fault_name",
        "Fault Name",
        "CFM6.0 Fault Object Name",
        "object_name",
        "name",
        "fault",
        "object",
        "Fault",
    ]

    for column in object_candidates:

        if column in vertices.columns:

            print(
                f"VERTICES: {column}: "
                f"{vertices[column].nunique(dropna=False):,} "
                "unique values"
            )

        if column in triangles.columns:

            print(
                f"TRIANGLES: {column}: "
                f"{triangles[column].nunique(dropna=False):,} "
                "unique values"
            )

    # --------------------------------------------------------------
    # DUPLICATE VERTEX ID BY OBJECT
    # --------------------------------------------------------------

    if "vertex_id" in vertices.columns:

        print()
        print("VERTEX_ID DUPLICATION BY POSSIBLE OBJECT")
        print("-" * 80)

        object_column = None

        for candidate in [
            "CFM6.0 Fault Object Name",
            "fault_name",
            "Fault Name",
            "object_name",
            "name",
        ]:

            if candidate in vertices.columns:
                object_column = candidate
                break

        if object_column is not None:

            grouped = (
                vertices
                .groupby(object_column)["vertex_id"]
                .nunique()
            )

            print(
                f"Object column: {object_column}"
            )

            print(
                f"Objects: {len(grouped):,}"
            )

            print(
                f"Minimum unique vertex IDs/object: "
                f"{grouped.min():,}"
            )

            print(
                f"Maximum unique vertex IDs/object: "
                f"{grouped.max():,}"
            )

            print(
                f"Median unique vertex IDs/object: "
                f"{grouped.median():.1f}"
            )

            print()
            print("First 20 objects:")

            print(
                grouped.head(20).to_string()
            )

        else:

            print(
                "No obvious object/fault column found."
            )


if __name__ == "__main__":
    main()
