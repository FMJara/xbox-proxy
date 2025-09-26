import json
import os
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib

DATA_DIR = "./data"
files = [f for f in os.listdir(DATA_DIR) if f.endswith(".json")]

# Combinar todos los JSON
all_data = []
for file in files:
    with open(os.path.join(DATA_DIR, file)) as f:
        all_data.extend(json.load(f))

df = pd.DataFrame(all_data)

# Features y target
X = df[["tenkan","kijun","senkou_a","senkou_b","chikou","rsi","ema"]]
y = (df["close"].shift(-1) > df["close"]).astype(int)

# Entrenar modelo
X_train, X_test, y_train, y_test = train_test_split(X[:-1], y[:-1], test_size=0.2, random_state=42)
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluación
preds = model.predict(X_test)
print("Accuracy:", accuracy_score(y_test, preds))

# Guardar modelo
joblib.dump(model, "model.pkl")
print("Modelo entrenado y guardado en model.pkl")
