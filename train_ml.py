import os
import json
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

DATA_DIR = "./data"
OUTPUT_MODEL = "model.pkl"

def load_data():
    X, y = [], []
    for file in os.listdir(DATA_DIR):
        if not file.endswith(".json"):
            continue
        with open(os.path.join(DATA_DIR, file)) as f:
            data = json.load(f)
            for row in data:
                if None in [row['tenkan'], row['kijun'], row['senkou_a'], row['senkou_b'], row['chikou'], row['rsi'], row['ema']]:
                    continue
                X.append([
                    row['tenkan'],
                    row['kijun'],
                    row['senkou_a'],
                    row['senkou_b'],
                    row['chikou'],
                    row['rsi'],
                    row['ema']
                ])
                # Etiqueta ficticia: sube si precio actual > EMA
                y.append(1 if row['close'] > row['ema'] else 0)
    return np.array(X), np.array(y)

def train():
    X, y = load_data()
    if len(X) == 0:
        print("❌ No hay datos válidos para entrenar.")
        return

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"✅ Modelo entrenado con accuracy: {acc:.2f}")

    joblib.dump(model, OUTPUT_MODEL)
    print(f"💾 Modelo guardado en {OUTPUT_MODEL}")

if __name__ == "__main__":
    train()
