import yfinance as yf
import pandas as pd
import numpy as np
import json
import os

DATA_DIR = "./data"
os.makedirs(DATA_DIR, exist_ok=True)

cryptos = {
    "XRP": "XRP-USD",
    "HBAR": "HBAR-USD",
    "XLM": "XLM-USD",
    "DAG": "DAG-USD",
    "PAW": "PAW-USD",   # ⚠️ puede que no esté en Yahoo
    "QUBIC": "QUBIC-USD", # ⚠️ puede que no esté en Yahoo
    "DOVU": "DOV-USD", # ⚠️ puede que no esté en Yahoo
    "XDC": "XDC-USD",
    "ZBCN": "ZBC-USD", # ⚠️ puede que no esté en Yahoo
    "DOGE": "DOGE-USD",
    "XPL": "XPL-USD",  # ⚠️ puede que no esté en Yahoo
    "SHX": "SHX-USD"   # ⚠️ puede que no esté en Yahoo
}

def ichimoku(df):
    high_9 = df['High'].rolling(window=9).max()
    low_9 = df['Low'].rolling(window=9).min()
    df['tenkan'] = (high_9 + low_9) / 2

    high_26 = df['High'].rolling(window=26).max()
    low_26 = df['Low'].rolling(window=26).min()
    df['kijun'] = (high_26 + low_26) / 2

    df['senkou_a'] = ((df['tenkan'] + df['kijun']) / 2).shift(26)
    high_52 = df['High'].rolling(window=52).max()
    low_52 = df['Low'].rolling(window=52).min()
    df['senkou_b'] = ((high_52 + low_52) / 2).shift(26)

    df['chikou'] = df['Close'].shift(-26)
    return df

def rsi(df, period=14):
    delta = df['Close'].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(window=period).mean()
    avg_loss = pd.Series(loss).rolling(window=period).mean()
    rs = avg_gain / avg_loss
    df['rsi'] = 100 - (100 / (1 + rs))
    return df

def ema(df, period=20):
    df['ema'] = df['Close'].ewm(span=period, adjust=False).mean()
    return df

def process_crypto(symbol, ticker):
    print(f"Descargando datos de {symbol} ({ticker})...")
    try:
        df = yf.download(ticker, period="3mo", interval="1h")
        if df.empty:
            print(f"⚠️ No se encontraron datos para {symbol}")
            return
        df = ichimoku(df)
        df = rsi(df)
        df = ema(df)

        records = []
        for idx, row in df.iterrows():
            records.append({
                "timestamp": idx.strftime("%Y-%m-%d %H:%M"),
                "close": round(row['Close'], 6),
                "tenkan": None if pd.isna(row['tenkan']) else round(row['tenkan'], 6),
                "kijun": None if pd.isna(row['kijun']) else round(row['kijun'], 6),
                "senkou_a": None if pd.isna(row['senkou_a']) else round(row['senkou_a'], 6),
                "senkou_b": None if pd.isna(row['senkou_b']) else round(row['senkou_b'], 6),
                "chikou": None if pd.isna(row['chikou']) else round(row['chikou'], 6),
                "rsi": None if pd.isna(row['rsi']) else round(row['rsi'], 2),
                "ema": None if pd.isna(row['ema']) else round(row['ema'], 6),
                "signal": "yellow"
            })

        with open(f"{DATA_DIR}/{symbol}.json", "w") as f:
            json.dump(records, f, indent=2)

        print(f"✅ Guardado {symbol}.json con {len(records)} registros.")

    except Exception as e:
        print(f"❌ Error con {symbol}: {e}")

if __name__ == "__main__":
    for symbol, ticker in cryptos.items():
        process_crypto(symbol, ticker)
