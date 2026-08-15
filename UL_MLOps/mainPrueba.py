
import pandas as pd

path = "/workspaces/Gestion-Servicios/UL_MLOps/data/raw/earthquakes.csv"

df = pd.read_csv(path)

print("Shape:", df.shape)
print("\nColumnas:")
print(df.columns.tolist())

print("\nTipos:")
print(df.dtypes)

print("\nPrimeras filas:")
print(df.head())

print("\nNulos:")
print(df.isna().sum())
