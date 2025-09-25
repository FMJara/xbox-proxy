import ccxt
import pandas as pd
import plotly.graph_objects as go
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Lista de criptos
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

# Función para calcular Ichimoku
def calcular_ichimoku(df):
    df['tenkan'] = (df['high'].rolling(9).max() + df['low'].rolling(9).min()) / 2
    df['kijun'] = (df['high'].rolling(26).max() + df['low'].rolling(26).min()) / 2
    df['senkou_a'] = ((df['tenkan'] + df['kijun']) / 2).shift(26)
    df['senkou_b'] = ((df['high'].rolling(52).max() + df['low'].rolling(52).min()) / 2).shift(26)
    df['chikou'] = df['close'].shift(-26)
    return df

# Generar señales
def generar_senales(df):
    df['senal'] = None
    df.loc[(df['tenkan'] > df['kijun']) & (df['close'] > df['senkou_a']) & (df['chikou'] > df['close'].shift(26)), 'senal'] = 'Compra'
    df.loc[(df['tenkan'] < df['kijun']) & (df['close'] < df['senkou_b']) & (df['chikou'] < df['close'].shift(26)), 'senal'] = 'Venta'
    return df

# Crear gráfico Plotly
def crear_grafico(df, simbolo):
    fig = go.Figure()

    # Velas
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close'],
        name='Velas'
    ))

    # Ichimoku
    fig.add_trace(go.Scatter(x=df.index, y=df['tenkan'], mode='lines', name='Tenkan', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=df.index, y=df['kijun'], mode='lines', name='Kijun', line=dict(color='red')))
    fig.add_trace(go.Scatter(x=df.index, y=df['senkou_a'], mode='lines', name='Senkou A', line=dict(color='green')))
    fig.add_trace(go.Scatter(x=df.index, y=df['senkou_b'], mode='lines', name='Senkou B', line=dict(color='orange')))
    fig.add_trace(go.Scatter(x=df.index, y=df['chikou'], mode='lines', name='Chikou', line=dict(color='purple')))

    # Señales
    fig.add_trace(go.Scatter(
        x=df.index[df['senal']=='Compra'], y=df['close'][df['senal']=='Compra'],
        mode='markers', marker=dict(symbol='triangle-up', color='green', size=10), name='Compra'
    ))
    fig.add_trace(go.Scatter(
        x=df.index[df['senal']=='Venta'], y=df['close'][df['senal']=='Venta'],
        mode='markers', marker=dict(symbol='triangle-down', color='red', size=10), name='Venta'
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
async def home(request: Request):
    # Obtener parámetro ?symbol=
    symbol = request.query_params.get("symbol", "XRP/USDT")
    if symbol not in symbols_whitelist:
        symbol = "XRP/USDT"

    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=200)
        df = pd.DataFrame(ohlcv, columns=['timestamp','open','high','low','close','volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        df = calcular_ichimoku(df)
        df = generar_senales(df)
        grafico_html = crear_grafico(df, symbol).to_html(full_html=False)
    except Exception as e:
        grafico_html = f"<p>Error cargando {symbol}: {e}</p>"

    # HTML con selector
    html = f"""
    <html>
    <head>
        <title>Ichimoku Criptos</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    </head>
    <body style="background-color:#1c1c1c; color:#f0f0f0; font-family:Arial;">
        <h1>Ichimoku Criptos</h1>
        <p>Selecciona una criptomoneda:</p>
        <select id="crypto_select" onchange="cambiarGrafico()">
    """
    for s in symbols_whitelist:
        selected = "selected" if s==symbol else ""
        html += f'<option value="{s}" {selected}>{s}</option>'
    html += "</select><div id='grafico'>" + grafico_html + "</div>"

    # Script para cambiar gráfico
    html += """
    <script>
    function cambiarGrafico(){
        var s = document.getElementById('crypto_select').value;
        window.location.href = "/?symbol=" + s;
    }
    </script>
    </body></html>
    """
    return html
