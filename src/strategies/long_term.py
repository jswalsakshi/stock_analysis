import pandas as pd

from src.data.prices import get_price_data
from src.data.fundamentals import get_yfinance_fundamentals, get_screener_ratios, parse_screener_value, get_dividend_history, get_yearly_dividends
from src.indicators.technicals import get_ema_slope


def normalize_dividend_yield(raw_yield):
    """
    yfinance returns dividendYield for .NS tickers already as a percentage.
    e.g., ITC = 5.3 (meaning 5.3%), Reliance = 0.41 (meaning 0.41%).
    
    We just pass through the value as-is (it's already in % form).
    If somehow a decimal fraction slips in (< 0.01 and stock actually pays),
    multiply by 100 as a safety net.
    """
    if raw_yield is None:
        return 0.0
    # yfinance .NS returns values like 5.3 for 5.3%, 0.41 for 0.41%
    # Only multiply if it looks like a true decimal fraction (e.g., 0.0041)
    if raw_yield < 0.01 and raw_yield > 0:
        return float(raw_yield * 100)
    return float(raw_yield)


def long_term_score(info, screener, ema_slope=0):
    """
    Score a single stock 0-100 for long-term dividend investing.
    Higher = better quality income stock.

    Scoring breakdown:
      25 pts — Dividend yield > 2% (you're getting paid to hold)
      20 pts — ROCE > 12% (company uses capital efficiently)
      20 pts — Low debt: D/E < 1 (won't go bankrupt)
      15 pts — Reasonable P/E < 30 (not overvalued)
      10 pts — ROE > 10% (good shareholder returns)
      10 pts — Price in uptrend (200-day EMA rising)
    """
    score = 0

    # 1. Dividend yield scoring (graduated) — dy is in % (e.g., 3.3 = 3.3%)
    dy = normalize_dividend_yield(info.get("dividendYield"))
    if dy > 4:
        score += 25  # Excellent yield (>4%)
    elif dy > 2:
        score += 20  # Good yield (>2%)
    elif dy > 1:
        score += 10  # Modest yield (>1%)

    # 2. Quality: ROCE (from Screener.in)
    roce_str = screener.get("ROCE", "0")
    roce = parse_screener_value(roce_str)
    if roce is not None and roce > 20:
        score += 20  # Excellent ROCE
    elif roce is not None and roce > 12:
        score += 15  # Good ROCE

    # 3. Low debt: D/E (yfinance uses percent-scale, so 100 = 1.0 ratio)
    de = info.get("debtToEquity") or 999
    if de < 50:
        score += 20  # Very low debt
    elif de < 100:
        score += 15  # Moderate debt
    elif de < 150:
        score += 5   # Acceptable for utilities/banks

    # 4. Reasonable valuation: P/E
    pe = info.get("trailingPE") or 999
    if pe < 15:
        score += 15  # Great value
    elif pe < 25:
        score += 12  # Fair value
    elif pe < 30:
        score += 5   # Slightly expensive but acceptable

    # 5. ROE
    roe = info.get("returnOnEquity") or 0
    if roe > 0.15:
        score += 10
    elif roe > 0.10:
        score += 5

    # 6. Price stability (EMA slope)
    if ema_slope > 0:
        score += 10

    return score


def screen_long_term(symbols):
    """
    Scan all symbols, score each 0-100, return ranked dividend picks.

    Hard filters (relaxed to allow more stocks through):
      - Must pay SOME dividend (yield > 0.5%)
      - Must have at least 1 year of price data
    
    Everything else is scored — higher score = better pick.
    """
    candidates = []

    for symbol in symbols:
        # Get fundamentals from yfinance
        info = get_yfinance_fundamentals(symbol)

        # Hard filter: must pay some dividend (>0.5%)
        raw_yield = info.get("dividendYield")
        div_yield_pct = normalize_dividend_yield(raw_yield)
        if div_yield_pct < 0.5:
            continue

        # Get price data
        df = get_price_data(symbol, period="1y")
        if df.empty or len(df) < 50:
            continue

        # Calculate EMA slope (not a hard filter anymore — just a scoring bonus)
        ema_slope = 0
        if len(df) >= 200:
            ema_slope = get_ema_slope(df, length=200, lookback=20)

        # Get ROCE from Screener.in (may fail — that's OK)
        screener = get_screener_ratios(symbol)

        # Score this stock
        score = long_term_score(info, screener, ema_slope)

        # Only include if score is decent (at least some criteria met)
        if score < 30:
            continue

        # Check dividend history (bonus info, not a hard filter)
        _, years_paid = get_dividend_history(symbol, years=5)

        # Year-wise dividend per share (last 5 years)
        yearly_divs = get_yearly_dividends(symbol, years=5)

        # Extract values for display
        roce = parse_screener_value(screener.get("ROCE"))
        roe = info.get("returnOnEquity")
        de = info.get("debtToEquity")
        pe = info.get("trailingPE")
        price = info.get("currentPrice") or float(df["Close"].iloc[-1])

        # Annual dividend per share in ₹
        div_per_share = info.get("dividendRate") or 0

        candidate = {
            "symbol": symbol,
            "price": float(price) if price else 0,
            "score": score,
            "dividend_yield": round(div_yield_pct, 2),
            "dividend_per_share": round(float(div_per_share), 2),
            "ROCE": round(float(roce), 1) if roce else 0,
            "ROE": round(float(roe * 100), 1) if roe else 0,
            "debt_to_equity": round(float(de), 1) if de else 0,
            "trailing_PE": round(float(pe), 1) if pe else 0,
            "years_dividend": years_paid,
            "sector": info.get("sector", "Unknown"),
        }

        # Add year-wise dividend columns (e.g., "Div_2022": ₹10.5)
        for year, amount in yearly_divs.items():
            candidate[f"Div_{year}"] = amount

        candidates.append(candidate)

    if not candidates:
        return pd.DataFrame()

    df_out = pd.DataFrame(candidates)
    df_out = df_out.sort_values("score", ascending=False).reset_index(drop=True)

    # Sector cap: max 3 from same sector (diversification)
    sector_counts = {}
    keep = []
    for _, row in df_out.iterrows():
        sector = row["sector"]
        sector_counts[sector] = sector_counts.get(sector, 0) + 1
        keep.append(sector_counts[sector] <= 3)
    df_out = df_out[keep].reset_index(drop=True)

    return df_out


def get_long_term_reason(row):
    """Generate plain-English reason for the pick."""
    reasons = []
    score = row.get("score", 0)

    dy = row.get("dividend_yield", 0)
    if dy > 4:
        reasons.append(f"high dividend yield ({dy:.1f}%)")
    elif dy > 2:
        reasons.append(f"solid dividend yield ({dy:.1f}%)")

    if row.get("ROCE", 0) > 12:
        reasons.append(f"efficient capital use (ROCE {row['ROCE']:.0f}%)")
    if row.get("debt_to_equity", 999) < 100:
        reasons.append("low debt")
    if row.get("trailing_PE", 999) < 25:
        reasons.append(f"reasonable valuation (P/E {row['trailing_PE']:.0f})")
    if row.get("ROE", 0) > 10:
        reasons.append(f"good returns (ROE {row['ROE']:.0f}%)")

    if not reasons:
        reasons = ["quality dividend stock"]

    return f"Score {score}/100 — {', '.join(reasons)}."
