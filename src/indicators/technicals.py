import pandas as pd
import numpy as np


# ─── Pure pandas/numpy indicator implementations ───────────────────────────────

def _ema(series, length):
    """Exponential Moving Average."""
    return series.ewm(span=length, adjust=False).mean()


def _rsi(series, length=14):
    """Relative Strength Index."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1/length, min_periods=length, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/length, min_periods=length, adjust=False).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def _macd(series, fast=12, slow=26, signal=9):
    """MACD: returns DataFrame with MACD line, signal, histogram."""
    ema_fast = _ema(series, fast)
    ema_slow = _ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = _ema(macd_line, signal)
    histogram = macd_line - signal_line
    result = pd.DataFrame({
        f"MACD_{fast}_{slow}_{signal}": macd_line,
        f"MACDs_{fast}_{slow}_{signal}": signal_line,
        f"MACDh_{fast}_{slow}_{signal}": histogram,
    }, index=series.index)
    return result


def _bbands(series, length=20, std=2):
    """Bollinger Bands: returns DataFrame with lower, mid, upper."""
    mid = series.rolling(window=length).mean()
    stdev = series.rolling(window=length).std()
    upper = mid + std * stdev
    lower = mid - std * stdev
    result = pd.DataFrame({
        f"BBL_{length}_{std}.0": lower,
        f"BBM_{length}_{std}.0": mid,
        f"BBU_{length}_{std}.0": upper,
    }, index=series.index)
    return result


def _adx(high, low, close, length=14):
    """Average Directional Index."""
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    up_move = high - high.shift(1)
    down_move = low.shift(1) - low

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    plus_dm = pd.Series(plus_dm, index=high.index)
    minus_dm = pd.Series(minus_dm, index=high.index)

    atr = tr.ewm(alpha=1/length, min_periods=length, adjust=False).mean()
    plus_di = 100 * (plus_dm.ewm(alpha=1/length, min_periods=length, adjust=False).mean() / atr)
    minus_di = 100 * (minus_dm.ewm(alpha=1/length, min_periods=length, adjust=False).mean() / atr)

    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    adx = dx.ewm(alpha=1/length, min_periods=length, adjust=False).mean()

    result = pd.DataFrame({
        f"ADX_{length}": adx,
        f"DMP_{length}": plus_di,
        f"DMN_{length}": minus_di,
    }, index=high.index)
    return result


def _atr(high, low, close, length=14):
    """Average True Range."""
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.ewm(alpha=1/length, min_periods=length, adjust=False).mean()


def _obv(close, volume):
    """On-Balance Volume."""
    sign = np.sign(close.diff())
    sign.iloc[0] = 0
    return (sign * volume).cumsum()


# ─── Public API ─────────────────────────────────────────────────────────────────

def add_all_indicators(df):
    if df.empty or len(df) < 200:
        return df

    df = df.copy()

    # RSI
    df["RSI_14"] = _rsi(df["Close"], 14)

    # MACD
    macd_df = _macd(df["Close"], 12, 26, 9)
    df = pd.concat([df, macd_df], axis=1)

    # Bollinger Bands
    bb_df = _bbands(df["Close"], 20, 2)
    df = pd.concat([df, bb_df], axis=1)

    # EMAs
    df["EMA_20"] = _ema(df["Close"], 20)
    df["EMA_50"] = _ema(df["Close"], 50)
    df["EMA_200"] = _ema(df["Close"], 200)

    # ADX
    adx_df = _adx(df["High"], df["Low"], df["Close"], 14)
    df = pd.concat([df, adx_df], axis=1)

    # OBV
    df["OBV"] = _obv(df["Close"], df["Volume"])

    # ATR
    df["ATRr_14"] = _atr(df["High"], df["Low"], df["Close"], 14)

    return df


def get_rsi(df, length=14):
    return _rsi(df["Close"], length=length)


def get_macd(df, fast=12, slow=26, signal=9):
    return _macd(df["Close"], fast=fast, slow=slow, signal=signal)


def get_bollinger_bands(df, length=20, std=2):
    return _bbands(df["Close"], length=length, std=std)


def get_ema(df, length=20):
    return _ema(df["Close"], length=length)


def get_adx(df, length=14):
    return _adx(df["High"], df["Low"], df["Close"], length=length)


def get_atr(df, length=14):
    return _atr(df["High"], df["Low"], df["Close"], length=length)


def check_trend_filter(df):
    """Close > EMA(50) AND EMA(20) > EMA(50)"""
    if len(df) < 50:
        return False
    ema20 = _ema(df["Close"], length=20)
    ema50 = _ema(df["Close"], length=50)
    if ema20 is None or ema50 is None:
        return False
    latest_close = df["Close"].iloc[-1]
    return bool(latest_close > ema50.iloc[-1] and ema20.iloc[-1] > ema50.iloc[-1])


def check_macd_momentum(df):
    """MACD line > signal AND histogram rising for 2 consecutive days"""
    macd_df = _macd(df["Close"], fast=12, slow=26, signal=9)
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
    rsi = _rsi(df["Close"], length=14)
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
    ema = _ema(df["Close"], length=length)
    if ema is None or len(ema) < lookback + 1:
        return 0.0
    slope = (ema.iloc[-1] - ema.iloc[-lookback]) / lookback
    return float(slope)
