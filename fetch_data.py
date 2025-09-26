import yfinance as yf
import pandas as pd
import json
import os

DATA_DIR = "./data"
os.makedirs(DATA_DIR, exist_ok=True)

cryptos = ["XRP","HBAR","XLM","DAG","PAW","QUBIC","DOVU","XDC","ZBCN","DOGE","XPL","SHX"]

def compute_indicators(df):
    # Tenkan-sen (9 periodos)
    high_9 = df['High'].rolling(window=9).max()
    low_9 = df['Low'].rolling(window=9).min()
    df['tenkan'] = (high_9 + low_9) / 2

    # Kijun-sen (26 periodos)
    high_26 = df['High'].rolling(window=26).max()
    low_26 = df['Low'].rolling(window=26).min()
    df['kijun'] = (high_26 + low_26) / 2

    # Senkou Span A (26 adelante)
    df['senkou_a'] = ((df['tenkan'] + df['kijun']) / 2).shift(26)

    # Senkou Span B (52 adelante)
    high_52 = df['High'].rolling(window=52).max()
    low_52 = df['Low'].rolling(window=52).min()
    df['senkou_b'] = ((high_52 + low_52) / 2).shift(26)

    # Chikou Span (26 atrás)
    df['chikou'] = df['Close'].shift(-26)

    # RSI (14 periodos)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # EMA (20 periodos)
    df['ema'] = df['Close'].ewm(span=20, adjust=False).mean()

    return df

for crypto in cryptos:
    ticker = f"{crypto}-USD"
    print(f"Descargando datos de {crypto} ({ticker})...")

    try:
        df = yf.download(ticker, period="3mo", interval="1h", auto_adjust=True)
        if df.empty:
            print(f"❌ No se encontraron datos para {crypto}")
            continue

        df = compute_indicators(df)

        # Armamos JSON
        data = []
        for i, row in df.iterrows():
            data.append({
                "timestamp": i.strftime("%Y-%m-%d %H:%M"),
                "close": round(float(row['Close']), 5),  # <- Forzamos 1D float
                "tenkan": round(float(row['tenkan']), 5) if pd.notna(row['tenkan']) else None,
                "kijun": round(float(row['kijun']), 5) if pd.notna(row['kijun']) else None,
                "senkou_a": round(float(row['senkou_a']), 5) if pd.notna(row['senkou_a']) else None,
                "senkou_b": round(float(row['senkou_b']), 5) if pd.notna(row['senkou_b']) else None,
                "chikou": round(float(row['chikou']), 5) if pd.notna(row['chikou']) else None,
                "rsi": round(float(row['rsi']), 2) if pd.notna(row['rsi']) else None,
                "ema": round(float(row['ema']), 5) if pd.notna(row['ema']) else None,
                "signal": "yellow"  # por defecto
            })

        with open(f"{DATA_DIR}/{crypto}.json", "w") as f:
            json.dump(data, f, indent=2)

        print(f"✅ Guardado {crypto}.json con {len(data)} registros")

    except Exception as e:
        print(f"❌ Error con {crypto}: {e}")
