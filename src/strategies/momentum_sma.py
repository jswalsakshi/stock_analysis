import pandas as pd
import yfinance as yf

from src.data.prices import get_price_data, get_weekly_data, get_monthly_data
from src.indicators.technicals import _rsi, _sma, check_sma50_support


# Extended universe: popular momentum stocks beyond Nifty50
EXTENDED_MOMENTUM_STOCKS = [
    "HAL", "IRFC", "PFC", "RECLTD", "NHPC", "CANBK", "BANKBARODA",
    "IOC", "GAIL", "VEDL", "SAIL", "NMDC", "IRCTC", "INDIANB",
    "POLYCAB", "PIIND", "PERSISTENT", "COFORGE", "MPHASIS",
    "MAXHEALTH", "FORTIS", "LALPATHLAB", "AUROPHARMA", "BIOCON",
    "TVSMOTOR", "MOTHERSON", "MRF", "ESCORTS",
    "PAGEIND", "DMART", "NAUKRI", "ZYDUSLIFE", "TORNTPHARM",
    "RVNL", "MAZAGON", "COCHINSHIP",
    "DEEPAKNTR", "ATUL", "FLUOROCHEM", "KPITTECH",
]


def get_extended_universe():
    """Get Nifty50 + extended momentum stocks for broader scanning."""
    from src.data.prices import get_universe
    base = get_universe()
    extended = list(set(base + EXTENDED_MOMENTUM_STOCKS))
    return extended


def compute_rsi_scores(symbol):
    """
    Compute RSI across 3 timeframes and return a score + details.

    Scoring (out of 100):
      - Monthly RSI >= 60: 30 pts (>= 55: 15 pts)
      - Weekly RSI >= 60: 30 pts (>= 55: 15 pts)
      - Daily RSI 48-65: 30 pts (40-70: 15 pts)
      - SMA50 proximity bonus: 10 pts
    """
    # Daily data
    daily = get_price_data(symbol, period="1y")
    if daily.empty or len(daily) < 50:
        return 0, {}

    daily_rsi_series = _rsi(daily["Close"], 14)
    if daily_rsi_series.isna().iloc[-1]:
        return 0, {}
    daily_rsi = float(daily_rsi_series.iloc[-1])

    # Weekly data
    weekly = get_weekly_data(symbol, period="1y")
    if weekly.empty or len(weekly) < 14:
        return 0, {}

    weekly_rsi_series = _rsi(weekly["Close"], 14)
    if weekly_rsi_series.isna().iloc[-1]:
        return 0, {}
    weekly_rsi = float(weekly_rsi_series.iloc[-1])

    # Monthly data
    monthly = get_monthly_data(symbol, period="2y")
    if monthly.empty or len(monthly) < 14:
        return 0, {}

    monthly_rsi_series = _rsi(monthly["Close"], 14)
    if monthly_rsi_series.isna().iloc[-1]:
        return 0, {}
    monthly_rsi = float(monthly_rsi_series.iloc[-1])

    # --- Scoring ---
    score = 0

    # Monthly RSI
    if monthly_rsi >= 60:
        score += 30
    elif monthly_rsi >= 55:
        score += 15

    # Weekly RSI
    if weekly_rsi >= 60:
        score += 30
    elif weekly_rsi >= 55:
        score += 15

    # Daily RSI (sweet spot = 48-65)
    if 48 <= daily_rsi <= 65:
        score += 30
    elif 40 <= daily_rsi <= 70:
        score += 15

    # SMA50 proximity bonus
    sma50 = _sma(daily["Close"], 50)
    price = float(daily["Close"].iloc[-1])
    sma50_val = float(sma50.iloc[-1]) if not sma50.isna().iloc[-1] else 0

    price_vs_sma = 0
    if sma50_val > 0:
        price_vs_sma = ((price - sma50_val) / sma50_val) * 100
        if abs(price_vs_sma) <= 3:
            score += 10
        elif abs(price_vs_sma) <= 5:
            score += 5

    # SMA50 support pattern check
    sma_support = check_sma50_support(daily, tolerance_pct=3.0, min_candles=2, max_candles=5)

    details = {
        "daily_rsi": round(daily_rsi, 1),
        "weekly_rsi": round(weekly_rsi, 1),
        "monthly_rsi": round(monthly_rsi, 1),
        "price": round(price, 2),
        "sma50": round(sma50_val, 2),
        "price_vs_sma50_pct": round(price_vs_sma, 2),
        "sma50_support": sma_support,
    }

    return score, details


def screen_momentum_sma(symbols=None, min_score=50, use_extended=True):
    """
    Screen stocks using RSI multi-timeframe + SMA50 scoring.

    Scoring (0-100):
      - 90-100: Perfect setup
      - 70-89: Strong setup
      - 50-69: Moderate / watchlist

    Returns DataFrame sorted by score.
    """
    if symbols is None:
        from src.data.prices import get_universe
        symbols = get_extended_universe() if use_extended else get_universe()

    candidates = []

    for symbol in symbols:
        score, details = compute_rsi_scores(symbol)

        if score < min_score:
            continue

        if score >= 90:
            signal = "Perfect"
        elif score >= 70:
            signal = "Strong"
        else:
            signal = "Moderate"

        candidates.append({
            "symbol": symbol,
            "score": score,
            "signal": signal,
            "price": details["price"],
            "daily_rsi": details["daily_rsi"],
            "weekly_rsi": details["weekly_rsi"],
            "monthly_rsi": details["monthly_rsi"],
            "sma50": details["sma50"],
            "price_vs_sma50_pct": details["price_vs_sma50_pct"],
            "at_sma50_support": details["sma50_support"],
        })

    if not candidates:
        return pd.DataFrame()

    df = pd.DataFrame(candidates)
    df = df.sort_values("score", ascending=False).reset_index(drop=True)
    return df
