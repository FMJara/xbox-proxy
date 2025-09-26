# train_ml.py
import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import joblib

DATA_DIR = "data"
MODEL_PATH = "model.pkl"

def load_data():
    all_data = []
    for file in os.listdir(DATA_DIR):
        if file.endswith(".csv"):
            name = file.replace(".csv", "")
            path = os.path.join(DATA_DIR, file)
            print(f"📂 Cargando {name} desde {path}")
            df = pd.read_csv(path)

            if df.empty or len(df) < 50:
                print(f"⚠️ {name} tiene pocos datos, se omite")
                continue

            # Features (OHLCV)
            df["return"] = df["close"].pct_change()
            df["ma5"] = df["close"].rolling(5).mean()
            df["ma10"] = df["close"].rolling(10).mean()

            df.dropna(inplace=True)

            # Etiqueta: 1 si sube, 0 si baja
            df["target"] = (df["return"].shift(-1) > 0).astype(int)

            features = df[["open", "high", "low", "close", "volume", "ma5", "ma10"]]
            target = df["target"]

            all_data.append((features, target))

    return all_data

def train_model():
    datasets = load_data()
    if not datasets:
        print("❌ No hay datos válidos para entrenar.")
        return

    X = pd.concat([f for f, _ in datasets])
    y = pd.concat([t for _, t in datasets])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, shuffle=False
    )

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    print("📊 Reporte de clasificación:")
    print(classification_report(y_test, preds))

    joblib.dump(model, MODEL_PATH)
    print(f"✅ Modelo guardado en {MODEL_PATH}")

if __name__ == "__main__":
    train_model()
