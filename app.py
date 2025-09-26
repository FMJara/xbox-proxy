import ccxt
import pandas as pd
import numpy as np
import json
from datetime import datetime
import pandas_ta as pta
from ta.trend import ichimoku_conversion_line, ichimoku_base_line

# Lista de cripto
cryptos = ['XRP/USDT','HBAR/USDT','XLM/USDT','DAG/USDT','PAW/USDT','QUBIC/USDT',
           'DOVU/USDT','XDC/USDT','ZBCN/USDT','DOGE/USDT','XPL/USDT','SHX/USDT']

exchange = ccxt.mexc({'enableRateLimit': True, 'asyncio_loop': False, 'timeout': 10000})

def fetch_ohlcv_safe(symbol, timeframe='1h', limit=200):
    for _ in range(3):
        try:
            return exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        except:
            import time; time.sleep(2)
    raise Exception(f"No se pudo obtener {symbol}")

def calcular_ichimoku(df):
    df['tenkan'] = ichimoku_conversion_line(df['high'], df['low'], 9)
    df['kijun'] = ichimoku_base_line(df['high'], df['low'], 26)
    df['senkou_a'] = df['tenkan'].shift(26)
    df['senkou_b'] = df['kijun'].shift(26)
    df['chikou'] = df['close'].shift(-26)
    df['cloud'] = df['senkou_a'] > df['senkou_b']
    return df

def generar_senales(df):
    # Cruce Tenkan/Kijun
    df['signal_cross'] = np.where(df['tenkan'] > df['kijun'], 'alcista', 'bajista')
    # Precio vs nube
    df['signal_cloud'] = np.where(df['close'] > df[['senkou_a','senkou_b']].max(axis=1),'alcista',
                          np.where(df['close'] < df[['senkou_a','senkou_b']].min(axis=1),'bajista','neutral'))
    # Chikou
    df['signal_chikou'] = np.where(df['chikou'] > df['close'].shift(26),'alcista','bajista')
    return df

# Pre-calculo cada 10 min (simulado aquí)
data_folder = 'data'
import os
os.makedirs(data_folder, exist_ok=True)

for sym in cryptos:
    ohlcv = fetch_ohlcv_safe(sym, limit=200)
    df = pd.DataFrame(ohlcv, columns=['timestamp','open','high','low','close','volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = calcular_ichimoku(df)
    df = generar_senales(df)
    df.to_json(f"{data_folder}/{sym.replace('/','_')}_ichimoku.json", orient='records', date_format='iso')
    print(f"{sym} guardado.")

# ------------------------------
# Generación HTML interactivo
# ------------------------------
html = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Ichimoku Interactivo</title>
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
<style>
body { font-family: Arial; background: #1c1c1c; color: #f0f0f0; margin:0; padding:10px; }
#chart { width:75%; height:600px; display:inline-block; }
#panel { width:23%; display:inline-block; vertical-align:top; margin-left:2%; }
.button-i { cursor:pointer; color:#0f0; font-weight:bold; margin-left:5px; }
.signal-active { background-color: rgba(255,255,0,0.2); }
select { font-size:1rem; padding:3px; margin-bottom:10px; width:100%; }
</style>
</head>
<body>
<select id="cryptoSelect">
  <option value="XRP_USDT">XRP</option>
  <option value="HBAR_USDT">HBAR</option>
  <option value="XLM_USDT">XLM</option>
  <option value="DAG_USDT">DAG</option>
  <option value="PAW_USDT">PAW</option>
  <option value="QUBIC_USDT">QUBIC</option>
  <option value="DOVU_USDT">DOVU</option>
  <option value="XDC_USDT">XDC</option>
  <option value="ZBNC_USDT">ZBNC</option>
  <option value="DOGE_USDT">DOGE</option>
  <option value="XPL_USDT">XPL</option>
  <option value="SHX_USDT">SHX</option>
</select>

<div id="chart"></div>
<div id="panel">
<h3>Señales Ichimoku</h3>
<div>Tenkan <span class="button-i" onclick="showInfo('tenkan')">(i)</span></div>
<div>Kijun <span class="button-i" onclick="showInfo('kijun')">(i)</span></div>
<div>Senkou <span class="button-i" onclick="showInfo('senkou')">(i)</span></div>
<div>Chikou <span class="button-i" onclick="showInfo('chikou')">(i)</span></div>
<div id="infoBox" style="margin-top:10px;"></div>
</div>

<script>
let currentData = null;
async function loadCrypto(sym){
    const res = await fetch('data/' + sym + '_ichimoku.json');
    const data = await res.json();
    currentData = data;
    drawChart(data);
}

function drawChart(data){
    const x = data.map(d=>d.timestamp);
    const close = data.map(d=>d.close);
    const tenkan = data.map(d=>d.tenkan);
    const kijun = data.map(d=>d.kijun);
    const senkou_a = data.map(d=>d.senkou_a);
    const senkou_b = data.map(d=>d.senkou_b);
    const chikou = data.map(d=>d.chikou);

    const traces = [
        {x:x, y:close, type:'scatter', mode:'lines', name:'Close', line:{color:'#00BFFF',width:2}},
        {x:x, y:tenkan, type:'scatter', mode:'lines', name:'Tenkan', line:{color:'lime',width:1}, visible:true},
        {x:x, y:kijun, type:'scatter', mode:'lines', name:'Kijun', line:{color:'orange',width:1}, visible:true},
        {x:x, y:senkou_a, type:'scatter', mode:'lines', name:'Senkou A', line:{color:'pink',width:1}, fill:'tonexty', visible:true},
        {x:x, y:senkou_b, type:'scatter', mode:'lines', name:'Senkou B', line:{color:'magenta',width:1}, visible:true},
        {x:x, y:chikou, type:'scatter', mode:'lines', name:'Chikou', line:{color:'yellow',width:1}, visible:true}
    ];

    Plotly.newPlot('chart', traces, {margin:{t:20}});
}

function showInfo(key){
    const infoBox = document.getElementById('infoBox');
    let infoText = '';
    if(key==='tenkan') infoText = "Cruce Tenkan/Kijun: arriba=alcista, abajo=bajista";
    if(key==='kijun') infoText = "Kijun: línea base para tendencias";
    if(key==='senkou') infoText = "Precio vs Nube: arriba=alcista, debajo=bajista, dentro=n. neutral";
    if(key==='chikou') infoText = "Chikou: por encima del precio 26p = confirm alcista, debajo=bajista";
    infoBox.innerText = infoText;
}

document.getElementById('cryptoSelect').addEventListener('change', e=>{
    loadCrypto(e.target.value);
});

// Cargar inicial
loadCrypto('XRP_USDT');
</script>
</body>
</html>
"""

with open("ichimoku_dashboard.html","w",encoding="utf-8") as f:
    f.write(html)

print("HTML interactivo generado: ichimoku_dashboard.html")
