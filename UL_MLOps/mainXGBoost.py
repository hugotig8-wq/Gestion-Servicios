import pandas as pd
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split

# 1. Cargar datos
df = pd.read_csv("/workspaces/Gestion-Servicios/data/raw/earthquakes.csv")

# 2. Definir variables de entrada (X) y objetivo (y)
X = df[["latitude", "longitude", "depth"]]
y = df["mag"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 3. Crear y entrenar el modelo
model = XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=6, n_jobs=-1)
model.fit(X_train, y_train)

# 4. Predecir
predicciones = model.predict(X_test)
