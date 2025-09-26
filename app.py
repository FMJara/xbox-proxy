from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/data", StaticFiles(directory="data"), name="data")

@app.get("/", response_class=HTMLResponse)
def home():
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
            <option value="ZBCN_USDT">ZBCN</option>
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
            <div id="semaforo" style="margin-top:10px; font-size:1.2rem;">
                Señal actual: <span id="signalColor">⚪</span>
            </div>
            <div id="infoBox" style="margin-top:10px;"></div>
        </div>

        <script>
            let currentData = null;

            async function loadCrypto(sym){
                try {
                    const res = await fetch('/data/' + sym + '_ichimoku.json');
                    const data = await res.json();
                    currentData = data;
                    drawChart(data);
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
                    {x:x, y:close, type:'scatter', mode:'lines', name:'Close', line:{color:'#00BFFF',width:2}},
                    {x:x, y:tenkan, type:'scatter', mode:'lines', name:'Tenkan', line:{color:'lime',width:1}},
                    {x:x, y:kijun, type:'scatter', mode:'lines', name:'Kijun', line:{color:'orange',width:1}},
                    {x:x, y:senkou_a, type:'scatter', mode:'lines', name:'Senkou A',
                        line:{color:'pink',width:1}, fill:'tonexty', fillcolor:'rgba(255,192,203,0.3)'},
                    {x:x, y:senkou_b, type:'scatter', mode:'lines', name:'Senkou B',
                        line:{color:'magenta',width:1}},
                    {x:x, y:chikou, type:'scatter', mode:'lines', name:'Chikou', line:{color:'yellow',width:1}}
                ];

                Plotly.newPlot('chart', traces, {margin:{t:20}});

                // Actualizar semáforo
                const lastSignal = data[data.length-1].signal;
                const signalIcon = document.getElementById('signalColor');
                if(lastSignal === "green") signalIcon.textContent = "🟢";
                else if(lastSignal === "yellow") signalIcon.textContent = "🟡";
                else if(lastSignal === "red") signalIcon.textContent = "🔴";
                else signalIcon.textContent = "⚪";
            }

            function showInfo(key){
                const infoBox = document.getElementById('infoBox');
                let infoText = '';
                if(key==='tenkan') infoText = "Tenkan cruza por arriba de Kijun = señal alcista; por debajo = bajista";
                if(key==='kijun') infoText = "Kijun: línea base, referencia de tendencia";
                if(key==='senkou') infoText = "Precio vs Nube: arriba = alcista, abajo = bajista, dentro = neutral";
                if(key==='chikou') infoText = "Chikou: por encima del precio hace 26 períodos = confirmación alcista; debajo = bajista";
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
    return HTMLResponse(html)
