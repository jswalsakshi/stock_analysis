import yfinance as yf
import pandas as pd
from pathlib import Path
import time

CACHE_DIR = Path(__file__).resolve().parents[2] / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get_universe():
    csv_path = Path(__file__).resolve().parents[1] / "universe" / "nifty50.csv"
    df = pd.read_csv(csv_path)
    return df["Symbol"].unique().tolist()


def get_price_data(symbol, period="1y", interval="1d", use_cache=True):
    ticker = f"{symbol}.NS"
    cache_file = CACHE_DIR / f"{symbol}_prices.parquet"

    if use_cache and cache_file.exists():
        cached = pd.read_parquet(cache_file)
        if len(cached) > 0:
            last_date = cached.index[-1]
            if (pd.Timestamp.now() - last_date).days < 1:
                return cached

    try:
        df = yf.download(ticker, period=period, interval=interval, auto_adjust=True, progress=False)
        if df.empty:
            return pd.DataFrame()
        # Flatten multi-level columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.to_parquet(cache_file)
        return df
    except Exception:
        if cache_file.exists():
            return pd.read_parquet(cache_file)
        return pd.DataFrame()


def get_bulk_prices(symbols=None, period="1y"):
    if symbols is None:
        symbols = get_universe()

    all_data = {}
    for symbol in symbols:
        df = get_price_data(symbol, period=period)
        if not df.empty:
            all_data[symbol] = df
        time.sleep(0.2)
    return all_data


def get_current_price(symbol):
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        info = ticker.info
        return info.get("currentPrice") or info.get("regularMarketPrice")
    except Exception:
        return None


def get_index_data(index="^NSEI", period="1y"):
    try:
        df = yf.download(index, period=period, interval="1d", auto_adjust=True, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception:
        return pd.DataFrame()
