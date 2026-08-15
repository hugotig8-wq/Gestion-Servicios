import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split

# 1. Cargar datos
df = pd.read_csv("/workspaces/Gestion-Servicios/UL_MLOps/data/raw/earthquakes.csv")

# 2. Definir variables de entrada (X) y objetivo (y)
X = df[["latitude", "longitude", "depth"]]
y = df["magnitude"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 3. Crear y entrenar el modelo
model = XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=6, n_jobs=-1)
model.fit(X_train, y_train)

# 1. Realizar las predicciones con el modelo ya entrenado
y_pred = model.predict(X_test)

# 2. Crear un DataFrame unificando las características de prueba con la predicción
df_forecast = X_test.copy()
df_forecast['predicted_mag'] = y_pred

# 3. Filtrar solo los sismos con Magnitud Predicha > 5.0
epicentros_m5 = df_forecast[df_forecast['predicted_mag'] > 5.0]

# 4. Imprimir los resultados formateados
print(f"--- PRONÓSTICO DE EPICENTROS (M > 5.0) ---")
print(f"Se encontraron {len(epicentros_m5)} eventos potencialmente fuertes:\n")

for idx, row in epicentros_m5.iterrows():
    print(f" Epicentro detectado:")
    print(f"   ├─ Latitud:  {row['latitude']:.4f}")
    print(f"   ├─ Longitud: {row['longitude']:.4f}")
    print(f"   ├─ Profundidad: {row['depth']:.1f} km")
    print(f"   └─ Magnitud Estimada: {row['predicted_mag']:.2f} M\n")

# Los reales:

df_real = X_test.copy()
df_real["magnitude"] = y_test.copy()

epicentros_reales_m5 = df_real[df_real['magnitude'] > 5.0]

print("###############################################")
print("###############################################")
print("###############################################")
print("###############################################")
print("###############################################")

# 4. Imprimir los resultados reales
print(f"--- EPICENTROS REALES (M > 5.0) ---")
print(f"Se encontraron {len(epicentros_reales_m5)} eventos reales potencialmente fuertes:\n")

for idx, row in epicentros_reales_m5.iterrows():
    print(f" Epicentro real detectado:")
    print(f"   ├─ Latitud:  {row['latitude']:.4f}")
    print(f"   ├─ Longitud: {row['longitude']:.4f}")
    print(f"   ├─ Profundidad: {row['depth']:.1f} km")
    print(f"   └─ Magnitud real estimada: {row['magnitude']:.2f} M\n")

