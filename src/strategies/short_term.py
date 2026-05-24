import pandas as pd
import pandas_ta as ta

from src.data.prices import get_price_data
from src.data.news import get_news_sentiment
from src.indicators.technicals import add_all_indicators, get_atr


def short_term_score(df, sentiment):
    """
    Score a single stock 0-100 for short-term swing trade.
    Higher = stronger buy signal.

    Scoring breakdown:
      25 pts — Trend: price > EMA(20) > EMA(50) (uptrend confirmed)
      20 pts — Momentum: MACD line > signal line (bullish crossover)
      15 pts — RSI: between 40-60 (not overbought, room to run)
      20 pts — Volume: today > 1.5x 20-day average (institutional interest)
      20 pts — Sentiment: positive news in last 24h
    """
    score = 0
    last = df.iloc[-1]

    # 1. Trend: price above EMA20 and EMA50
    if "EMA_20" in df.columns and "EMA_50" in df.columns:
        if last["Close"] > last["EMA_20"] and last["EMA_20"] > last["EMA_50"]:
            score += 25

    # 2. Momentum: MACD line crossed above signal
    macd_col = [c for c in df.columns if c.startswith("MACD_") and "h" not in c.lower() and "s" not in c.lower()]
    signal_col = [c for c in df.columns if "MACDs" in c]
    if macd_col and signal_col:
        if last[macd_col[0]] > last[signal_col[0]]:
            score += 20

    # 3. RSI bounce: between 40-60 (not overbought)
    rsi_col = [c for c in df.columns if "RSI" in c]
    rsi_val = last[rsi_col[0]] if rsi_col else 50
    if 40 < rsi_val < 60:
        score += 15

    # 4. Volume spike: today's volume > 1.5x 20-day average
    avg_vol = df["Volume"].tail(20).mean()
    if avg_vol > 0 and last["Volume"] > 1.5 * avg_vol:
        score += 20

    # 5. Positive news sentiment
    if sentiment > 0.1:
        score += 20

    return score


def screen_short_term(symbols, vix_value=None):
    """
    Scan all symbols, score each 0-100, return top picks ranked by score.
    """
    candidates = []

    for symbol in symbols:
        df = get_price_data(symbol, period="1y")
        if df.empty or len(df) < 200:
            continue

        # Add technical indicators
        df = add_all_indicators(df)

        # Get news sentiment
        avg_sentiment, _ = get_news_sentiment(symbol, max_results=5)

        # Score this stock
        score = short_term_score(df, avg_sentiment)

        # Only include if score is meaningful (at least 2 signals fired)
        if score < 35:
            continue

        # Calculate stop loss and target using ATR
        close = float(df["Close"].iloc[-1])
        atr = get_atr(df)
        atr_val = float(atr.iloc[-1]) if atr is not None and len(atr) > 0 else close * 0.02

        rsi_col = [c for c in df.columns if "RSI" in c]
        rsi_val = float(df[rsi_col[0]].iloc[-1]) if rsi_col else 50.0

        candidates.append({
            "symbol": symbol,
            "price": close,
            "score": score,
            "stop_loss": round(close - 1.5 * atr_val, 2),
            "target": round(close + 3.0 * atr_val, 2),
            "rsi": round(rsi_val, 1),
            "sentiment": round(avg_sentiment, 3),
            "vol_ratio": round(float(df["Volume"].iloc[-1] / df["Volume"].tail(20).mean()), 2),
        })

    if not candidates:
        return pd.DataFrame()

    df_out = pd.DataFrame(candidates)
    df_out = df_out.sort_values("score", ascending=False).reset_index(drop=True)
    return df_out


def get_short_term_reason(row):
    """Generate plain-English reason for the pick."""
    reasons = []
    score = row.get("score", 0)

    if score >= 80:
        reasons.append("all technical signals aligned")
    if row.get("vol_ratio", 0) > 1.5:
        reasons.append("volume surge (institutional buying)")
    if row.get("sentiment", 0) > 0.1:
        reasons.append("positive news sentiment")
    if 40 < row.get("rsi", 50) < 60:
        reasons.append("RSI in sweet spot (room to run)")

    if not reasons:
        reasons = ["multiple buy signals active"]

    return f"Score {score}/100 — {', '.join(reasons)}."

