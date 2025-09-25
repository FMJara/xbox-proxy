import ccxt
import pandas as pd
import plotly.graph_objects as go
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import json

# Inicializar FastAPI
app = FastAPI()

# Lista de criptomonedas
symbols_whitelist = [
    'XRP/USDT', 'HBAR/USDT', 'XLM/USDT', 'DAG/USDT', 'PAW/USDT',
    'QUBIC/USDT', 'DOVU/USDT', 'XDC/USDT', 'ZBCN/USDT', 'DOGE/USDT',
    'XPL/USDT', 'SHX/USDT'
]

# Configurar exchange
exchange = ccxt.mexc({
    'enableRateLimit': True,
    'timeout': 10000
})

# Función Ichimoku
def calcular_ichimoku(df):
    df['tenkan'] = (df['high'].rolling(9).max() + df['low'].rolling(9).min()) / 2
    df['kijun'] = (df['high'].rolling(26).max() + df['low'].rolling(26).min()) / 2
    df['senkou_a'] = ((df['tenkan'] + df['kijun']) / 2).shift(26)
    df['senkou_b'] = ((df['high'].rolling(52).max() + df['low'].rolling(52).min()) / 2).shift(26)
    df['chikou'] = df['close'].shift(-26)
    return df

# Señales
def generar_senales(df):
    df['senal'] = None
    df.loc[(df['tenkan'] > df['kijun']) & (df['close'] > df['senkou_a']), 'senal'] = 'Compra'
    df.loc[(df['tenkan'] < df['kijun']) & (df['close'] < df['senkou_b']), 'senal'] = 'Venta'
    return df

# Crear gráfico Plotly
def crear_grafico(df, simbolo):
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close'],
        name='Velas'
    ))
    fig.add_trace(go.Scatter(x=df.index, y=df['tenkan'], mode='lines', name='Tenkan', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=df.index, y=df['kijun'], mode='lines', name='Kijun', line=dict(color='red')))
    fig.add_trace(go.Scatter(x=df.index, y=df['senkou_a'], mode='lines', name='Senkou A', line=dict(color='green')))
    fig.add_trace(go.Scatter(x=df.index, y=df['senkou_b'], mode='lines', name='Senkou B', line=dict(color='orange')))
    fig.add_trace(go.Scatter(x=df.index, y=df['chikou'], mode='lines', name='Chikou', line=dict(color='purple')))

    fig.add_trace(go.Scatter(
        x=df.index[df['senal'] == 'Compra'], y=df['close'][df['senal'] == 'Compra'],
        mode='markers', marker=dict(symbol='triangle-up', color='green', size=10),
        name='Señal Compra'
    ))
    fig.add_trace(go.Scatter(
        x=df.index[df['senal'] == 'Venta'], y=df['close'][df['senal'] == 'Venta'],
        mode='markers', marker=dict(symbol='triangle-down', color='red', size=10),
        name='Señal Venta'
    ))

    fig.update_layout(
        title=f'Ichimoku - {simbolo}',
        xaxis_title='Fecha',
        yaxis_title='Precio',
        xaxis_rangeslider_visible=False
    )
    return fig

# Endpoint principal
@app.get("/", response_class=HTMLResponse)
def home():
    datos = {}
    for simbolo in symbols_whitelist:
        try:
            ohlcv = exchange.fetch_ohlcv(simbolo, timeframe='1h', limit=200)
            df = pd.DataFrame(ohlcv, columns=['timestamp','open','high','low','close','volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            df = calcular_ichimoku(df)
            df = generar_senales(df)
            fig = crear_grafico(df, simbolo)
            datos[simbolo] = fig.to_html(full_html=False)
        except Exception as e:
            datos[simbolo] = f"<p>Error cargando {simbolo}: {e}</p>"

    # HTML principal con selector
    html = """
    <html><head><title>Ichimoku Criptos</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script></head><body>
    <h1>Gráficos Ichimoku</h1>
    <p>Selecciona una criptomoneda:</p>
    <select id="crypto_select" onchange="cambiarGrafico()">
    """
    for s in symbols_whitelist:
        html += f'<option value="{s}">{s}</option>'
    html += "</select><div id='grafico'></div><script>"
    html += f"var datos = {json.dumps(datos)};"
    html += """
    function cambiarGrafico(){
        var s = document.getElementById('crypto_select').value;
        document.getElementById('grafico').innerHTML = datos[s];
    }
    cambiarGrafico();
    </script></body></html>
    """
    return html
