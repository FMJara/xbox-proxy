# fetch_data.py
import os
import requests
import pandas as pd
import yfinance as yf

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# Lista de criptos
TICKERS = {
    "BTC": "BTC-USD",
    "ETH": "ETH-USD",
    "DOGE": "DOGE-USD",
    "ZBC": "ZBCUSDT",
    "SHX": "SHXUSDT",
    "XPL": "XPLUSDT",
}

def fetch_yahoo(symbol, name):
    """Descarga datos de Yahoo Finance"""
    try:
        print(f"📥 Yahoo → {name} ({symbol})")
        df = yf.download(symbol, period="3mo", interval="1h")
        if df.empty:
            print(f"⚠️ No hay datos en Yahoo para {name}")
            return None
        df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
        df.reset_index(inplace=True)
        return df
    except Exception as e:
        print(f"❌ Error Yahoo {name}: {e}")
        return None

def fetch_mexc(symbol, name, interval="1h", limit=1000):
    """Descarga datos de MEXC API"""
    try:
        print(f"📥 MEXC → {name} ({symbol})")
        url = "https://api.mexc.com/api/v3/klines"
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        r = requests.get(url, params=params, timeout=10)
        data = r.json()

        if isinstance(data, dict) and "code" in data:
            print(f"❌ Error MEXC {name}: {data.get('msg', 'Desconocido')}")
            return None

        cols = ["timestamp", "open", "high", "low", "close", "volume",
                "close_time", "quote_asset_volume", "trades",
                "taker_base_vol", "taker_quote_vol", "ignore"]

        df = pd.DataFrame(data, columns=cols)
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)

        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df[["open", "high", "low", "close", "volume"]].copy()
        df.reset_index(inplace=True)
        return df
    except Exception as e:
        print(f"❌ Error MEXC {name}: {e}")
        return None

def save_data(df, name):
    """Guarda datos en CSV"""
    file_path = os.path.join(DATA_DIR, f"{name}.csv")
    df.to_csv(file_path, index=False)
    print(f"✅ Guardado {file_path}")

def main():
    for name, symbol in TICKERS.items():
        df = None
        if "-USD" in symbol:  # Yahoo
            df = fetch_yahoo(symbol, name)
        else:  # MEXC
            df = fetch_mexc(symbol, name)

        if df is not None and not df.empty:
            save_data(df, name)
        else:
            print(f"⚠️ {name}: sin datos válidos")

if __name__ == "__main__":
    main()
