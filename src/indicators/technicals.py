import pandas as pd
import pandas_ta as ta


def add_all_indicators(df):
    if df.empty or len(df) < 200:
        return df

    df = df.copy()
    df.ta.rsi(length=14, append=True)
    df.ta.macd(fast=12, slow=26, signal=9, append=True)
    df.ta.bbands(length=20, std=2, append=True)
    df.ta.ema(length=20, append=True)
    df.ta.ema(length=50, append=True)
    df.ta.ema(length=200, append=True)
    df.ta.adx(length=14, append=True)
    df.ta.obv(append=True)
    df.ta.atr(length=14, append=True)
    return df


def get_rsi(df, length=14):
    return ta.rsi(df["Close"], length=length)


def get_macd(df, fast=12, slow=26, signal=9):
    return ta.macd(df["Close"], fast=fast, slow=slow, signal=signal)


def get_bollinger_bands(df, length=20, std=2):
    return ta.bbands(df["Close"], length=length, std=std)


def get_ema(df, length=20):
    return ta.ema(df["Close"], length=length)


def get_adx(df, length=14):
    return ta.adx(df["High"], df["Low"], df["Close"], length=length)


def get_atr(df, length=14):
    return ta.atr(df["High"], df["Low"], df["Close"], length=length)


def check_trend_filter(df):
    """Close > EMA(50) AND EMA(20) > EMA(50)"""
    if len(df) < 50:
        return False
    ema20 = ta.ema(df["Close"], length=20)
    ema50 = ta.ema(df["Close"], length=50)
    if ema20 is None or ema50 is None:
        return False
    latest_close = df["Close"].iloc[-1]
    return bool(latest_close > ema50.iloc[-1] and ema20.iloc[-1] > ema50.iloc[-1])


def check_macd_momentum(df):
    """MACD line > signal AND histogram rising for 2 consecutive days"""
    macd_df = ta.macd(df["Close"], fast=12, slow=26, signal=9)
    if macd_df is None or len(macd_df) < 3:
        return False
    hist_col = [c for c in macd_df.columns if "h" in c.lower() or "hist" in c.lower()]
    macd_col = [c for c in macd_df.columns if c.startswith("MACD_") and "h" not in c.lower() and "s" not in c.lower()]
    signal_col = [c for c in macd_df.columns if "s" in c.lower() and "MACD" in c]

    if not hist_col or not macd_col or not signal_col:
        return False

    hist = macd_df[hist_col[0]]
    macd_line = macd_df[macd_col[0]]
    signal_line = macd_df[signal_col[0]]

    macd_above_signal = macd_line.iloc[-1] > signal_line.iloc[-1]
    hist_rising = hist.iloc[-1] > hist.iloc[-2] and hist.iloc[-2] > hist.iloc[-3]
    return bool(macd_above_signal and hist_rising)


def check_rsi_bounce(df):
    """RSI crossed back above 40 from below 40 within last 3 bars"""
    rsi = ta.rsi(df["Close"], length=14)
    if rsi is None or len(rsi) < 4:
        return False
    recent = rsi.iloc[-4:]
    was_below = any(recent.iloc[:-1] < 40)
    now_above = recent.iloc[-1] >= 40
    return bool(was_below and now_above)


def check_volume_surge(df, threshold=1.5):
    """Today's volume > threshold × 20-day average volume"""
    if len(df) < 21:
        return False
    avg_vol = df["Volume"].iloc[-21:-1].mean()
    if avg_vol == 0:
        return False
    return bool(df["Volume"].iloc[-1] > threshold * avg_vol)


def get_ema_slope(df, length=200, lookback=20):
    """Returns the slope of the EMA over lookback period (positive = uptrend)"""
    ema = ta.ema(df["Close"], length=length)
    if ema is None or len(ema) < lookback + 1:
        return 0.0
    slope = (ema.iloc[-1] - ema.iloc[-lookback]) / lookback
    return float(slope)
