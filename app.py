import os
import json
import joblib
import pandas as pd
from flask import Flask, render_template_string
import plotly.graph_objs as go
from plotly.offline import plot

app = Flask(__name__)

# Carpeta base del proyecto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Rutas
DATA_DIR = os.path.join(BASE_DIR, "data")
MODEL_PATH = os.path.join(BASE_DIR, "model", "model.pkl")

# Cargar modelo entrenado
model = None
if os.path.exists(MODEL_PATH):
    model = joblib.load(MODEL_PATH)
    print("✅ Modelo cargado")
else:
    print("⚠️ No se encontró model.pkl. Ejecuta train_ml.py primero.")

# Plantilla HTML mínima
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Crypto Dashboard</title>
    <meta charset="utf-8">
</head>
<body>
    <h1>Crypto Dashboard</h1>
    {% for crypto, chart in charts.items() %}
        <h2>{{ crypto }}</h2>
        <div>{{ chart|safe }}</div>
    {% endfor %}
</body>
</html>
"""

def load_crypto_data(symbol):
    path = os.path.join(DATA_DIR, f"{symbol}.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return pd.DataFrame(json.load(f))

def predict_signal(df):
    if model is None or df.empty:
        return "yellow"
    last = df.iloc[-1]
    if None in [last['tenkan'], last['kijun'], last['senkou_a'],
                last['senkou_b'], last['chikou'], last['rsi'], last['ema']]:
        return "yellow"
    features = [[
        last['tenkan'], last['kijun'], last['senkou_a'],
        last['senkou_b'], last['chikou'], last['rsi'], last['ema']
    ]]
    pred = model.predict(features)[0]
    return "green" if pred == 1 else "red"

def create_chart(symbol, df):
    fig = go.Figure()

    # Precio (línea negra destacada)
    fig.add_trace(go.Scatter(x=df["timestamp"], y=df["close"], mode="lines",
                             name="Precio", line=dict(color="black", width=2)))

    # Ichimoku
    fig.add_trace(go.Scatter(x=df["timestamp"], y=df["tenkan"], mode="lines", name="Tenkan", line=dict(color="blue")))
    fig.add_trace(go.Scatter(x=df["timestamp"], y=df["kijun"], mode="lines", name="Kijun", line=dict(color="red")))
    fig.add_trace(go.Scatter(x=df["timestamp"], y=df["senkou_a"], mode="lines", name="Senkou A", line=dict(color="green")))
    fig.add_trace(go.Scatter(x=df["timestamp"], y=df["senkou_b"], mode="lines", name="Senkou B", line=dict(color="orange")))
    fig.add_trace(go.Scatter(x=df["timestamp"], y=df["chikou"], mode="lines", name="Chikou", line=dict(color="purple")))
    fig.add_trace(go.Scatter(x=df["timestamp"], y=df["ema"], mode="lines", name="EMA", line=dict(color="brown")))

    fig.update_layout(title=f"Indicadores para {symbol}",
                      xaxis_title="Tiempo",
                      yaxis_title="Precio (USD)",
                      template="plotly_dark")

    return plot(fig, output_type="div")

@app.route("/")
def index():
    charts = {}
    for file in os.listdir(DATA_DIR):
        if not file.endswith(".json"):
            continue
        symbol = file.replace(".json", "")
        df = load_crypto_data(symbol)
        if df is None or df.empty:
            continue
        signal = predict_signal(df)
        chart_html = create_chart(symbol, df)
        charts[symbol] = f"<p>Señal ML: <b style='color:{signal}'>{signal.upper()}</b></p>{chart_html}"
    return render_template_string(HTML_TEMPLATE, charts=charts)

if __name__ == "__main__":
    # Permite correr localmente
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
