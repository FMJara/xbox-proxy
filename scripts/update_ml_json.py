import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import SGDClassifier
from sklearn.preprocessing import StandardScaler

DATA_DIR = "../data"
MODEL_PATH = "../model/signal_model.pkl"

FEATURES = ["tenkan","kijun","senkou_a","senkou_b","chikou","rsi","ema"]

def get_target(df, steps=1):
    df = df.copy()
    df["future_close"] = df["close"].shift(-steps)
    df["target"] = 0
    df.loc[df["future_close"] > df["close"]*1.002, "target"] = 1
    df.loc[df["future_close"] < df["close"]*0.998, "target"] = -1
    df = df.drop(columns=["future_close"])
    return df

if os.path.exists(MODEL_PATH):
    model_dict = joblib.load(MODEL_PATH)
    clf = model_dict["clf"]
    scaler = model_dict["scaler"]
else:
    clf = SGDClassifier(max_iter=1000, tol=1e-3)
    scaler = StandardScaler()
    clf.partial_fit(np.zeros((1,len(FEATURES))), [0], classes=[-1,0,1])

for file in os.listdir(DATA_DIR):
    if file.endswith(".json"):
        path = os.path.join(DATA_DIR, file)
        with open(path,"r") as f:
            data = json.load(f)
        df = pd.DataFrame(data)
        
        if len(df) > 2:
            df = get_target(df, steps=1)
            X = df[FEATURES].values
            X_scaled = scaler.fit_transform(X)
            y = df["target"].values

            clf.partial_fit(X_scaled, y)
            
            pred = clf.predict(X_scaled)
            last_pred = pred[-1]
            if last_pred == 1:
                signal = "green"
            elif last_pred == -1:
                signal = "red"
            else:
                signal = "yellow"
            df["signal"] = ["green" if p==1 else "red" if p==-1 else "yellow" for p in pred]

            df_to_save = df[["timestamp","close"] + FEATURES + ["signal"]].to_dict(orient="records")
            with open(path,"w") as f:
                json.dump(df_to_save,f,indent=2)

joblib.dump({"clf":clf,"scaler":scaler}, MODEL_PATH)
print("Actualización y entrenamiento incremental completados.")
