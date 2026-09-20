from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent

CFM_DIR = PROJECT_ROOT / "data" / "processed" / "cfm"

VERTICES_FILE = CFM_DIR / "cfm_vertices_1000m.csv"


def main():
    print("=" * 70)
    print("CFM VERTEX ID DIAGNOSTIC")
    print("=" * 70)

    print()
    print(f"Reading:\n{VERTICES_FILE}")

    vertices = pd.read_csv(VERTICES_FILE)

    print()
    print("COLUMNS")
    print("-" * 70)

    for i, column in enumerate(vertices.columns):
        print(f"{i}: {column}")

    print()
    print("DATASET")
    print("-" * 70)

    print(f"Rows: {len(vertices):,}")
    print(f"Columns: {len(vertices.columns)}")

    print()
    print("FIRST 10 ROWS")
    print("-" * 70)

    print(vertices.head(10).to_string())

    print()
    print("POSSIBLE ID COLUMNS")
    print("-" * 70)

    possible_id_columns = [
        "vertex_id",
        "id",
        "ID",
        "vertex",
        "Vertex",
        "VRTX",
        "VRTX_ID",
        "vertex_index",
        "index",
    ]

    found = []

    for column in possible_id_columns:

        if column in vertices.columns:

            found.append(column)

            series = vertices[column]

            print()
            print(f"COLUMN: {column}")
            print(f"dtype: {series.dtype}")
            print(f"unique: {series.nunique(dropna=False):,}")
            print(
                f"duplicated: "
                f"{series.duplicated().sum():,}"
            )
            print(
                f"nulls: "
                f"{series.isna().sum():,}"
            )

            print("first values:")
            print(series.head(20).to_list())

    if not found:

        print("No obvious vertex-ID column found.")

    print()
    print("ALL INTEGER-LIKE COLUMNS")
    print("-" * 70)

    for column in vertices.columns:

        series = vertices[column]

        numeric = pd.to_numeric(
            series,
            errors="coerce",
        )

        if numeric.notna().all():

            integer_like = (
                np_all_integer(numeric)
            )

            if integer_like:

                print()
                print(
                    f"{column}: "
                    f"unique={numeric.nunique():,}, "
                    f"duplicated="
                    f"{numeric.duplicated().sum():,}, "
                    f"min={numeric.min()}, "
                    f"max={numeric.max()}"
                )


def np_all_integer(series):
    """Return True if all numeric values are integers."""

    return ((series % 1) == 0).all()


if __name__ == "__main__":
    main()
