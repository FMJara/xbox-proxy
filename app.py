from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import os
import joblib
import pandas as pd

app = FastAPI()

# Servir carpeta data
app.mount("/data", StaticFiles(directory="data"), name="data")

# Cargar modelo entrenado
MODEL_PATH = "model.pkl"
model = joblib.load(MODEL_PATH) if os.path.exists(MODEL_PATH) else None

@app.get("/", response_class=HTMLResponse)
def home():
    html = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
      <meta charset="UTF-8">
      <title>Cripto Ichimoku + ML</title>
      <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
      <style>
        body { font-family: Arial; background: #1c1c1c; color: #f0f0f0; margin:0; padding:10px; }
        #chart { width:75%; height:600px; display:inline-block; }
        #panel { width:23%; display:inline-block; vertical-align:top; margin-left:2%; }
        .button-i { cursor:pointer; color:#0f0; font-weight:bold; margin-left:5px; }
        .signal-box { margin-top:20px; padding:10px; border-radius:5px; font-weight:bold; }
        .green { background:rgba(0,255,0,0.2); }
        .red { background:rgba(255,0,0,0.2); }
        .yellow { background:rgba(255,255,0,0.2); }
        select { font-size:1rem; padding:3px; margin-bottom:10px; width:100%; }
      </style>
    </head>
    <body>
      <h2>Dashboard Cripto (Ichimoku + ML)</h2>
      <select id="cryptoSelect">
        <option value="XRP">XRP</option>
        <option value="HBAR">HBAR</option>
        <option value="XLM">XLM</option>
        <option value="DAG">DAG</option>
        <option value="PAW">PAW</option>
        <option value="QUBIC">QUBIC</option>
        <option value="DOVU">DOVU</option>
        <option value="XDC">XDC</option>
        <option value="ZBCN">ZBCN</option>
        <option value="DOGE">DOGE</option>
        <option value="XPL">XPL</option>
        <option value="SHX">SHX</option>
      </select>

      <div id="chart"></div>
      <div id="panel">
        <h3>Señales Ichimoku</h3>
        <div>Tenkan <span class="button-i" onclick="showInfo('tenkan')">(i)</span></div>
        <div>Kijun <span class="button-i" onclick="showInfo('kijun')">(i)</span></div>
        <div>Senkou <span class="button-i" onclick="showInfo('senkou')">(i)</span></div>
        <div>Chikou <span class="button-i" onclick="showInfo('chikou')">(i)</span></div>
        <div id="infoBox" style="margin-top:10px;"></div>
        <div id="mlBox" class="signal-box yellow">Cargando señal ML...</div>
      </div>

      <script>
        let currentData = null;

        async function loadCrypto(sym){
            try {
                const res = await fetch('/data/' + sym + '.json');
                const data = await res.json();
                currentData = data;
                drawChart(data);
                fetchSignal(data);
            } catch(e){
                alert("No se pudo cargar datos para " + sym);
            }
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
                {x:x, y:close, type:'scatter', mode:'lines', name:'Precio', line:{color:'#00BFFF',width:2}},
                {x:x, y:tenkan, type:'scatter', mode:'lines', name:'Tenkan', line:{color:'lime',width:1}},
                {x:x, y:kijun, type:'scatter', mode:'lines', name:'Kijun', line:{color:'orange',width:1}},
                {x:x, y:senkou_a, type:'scatter', mode:'lines', name:'Senkou A', line:{color:'pink',width:1}, fill:'tonexty'},
                {x:x, y:senkou_b, type:'scatter', mode:'lines', name:'Senkou B', line:{color:'magenta',width:1}},
                {x:x, y:chikou, type:'scatter', mode:'lines', name:'Chikou', line:{color:'yellow',width:1}}
            ];

            Plotly.newPlot('chart', traces, {margin:{t:20}});
        }

        function showInfo(key){
            const infoBox = document.getElementById('infoBox');
            let infoText = '';
            if(key==='tenkan') infoText = "Tenkan cruza por arriba de Kijun = señal alcista; por debajo = bajista";
            if(key==='kijun') infoText = "Kijun: línea base, referencia de tendencia";
            if(key==='senkou') infoText = "Precio vs Nube: arriba = alcista, abajo = bajista, dentro = neutral";
            if(key==='chikou') infoText = "Chikou: confirmación de tendencia según posición respecto al precio pasado";
            infoBox.innerText = infoText;
        }

        async function fetchSignal(data){
            const last = data[data.length-1];
            const res = await fetch('/predict', {
                method:'POST',
                headers:{'Content-Type':'application/json'},
                body: JSON.stringify(last)
            });
            const result = await res.json();
            const box = document.getElementById('mlBox');
            box.className = 'signal-box ' + result.color;
            box.innerText = "Señal ML: " + result.signal.toUpperCase();
        }

        document.getElementById('cryptoSelect').addEventListener('change', e=>{
            loadCrypto(e.target.value);
        });

        loadCrypto('XRP'); // carga inicial
      </script>
    </body>
    </html>
    """
    return HTMLResponse(html)

@app.post("/predict")
async def predict(data: dict):
    if not model:
        return {"signal":"unknown","color":"yellow"}
    X = pd.DataFrame([[
        data["tenkan"], data["kijun"], data["senkou_a"], data["senkou_b"],
        data["chikou"], data["rsi"], data["ema"]
    ]], columns=["tenkan","kijun","senkou_a","senkou_b","chikou","rsi","ema"])
    pred = model.predict(X)[0]
    signal = "alcista" if pred==1 else "bajista"
    color = "green" if pred==1 else "red"
    return {"signal":signal,"color":color}
