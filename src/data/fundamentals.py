import yfinance as yf
import requests
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path
import time

CACHE_DIR = Path(__file__).resolve().parents[2] / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
FUNDAMENTALS_CACHE = CACHE_DIR / "fundamentals.parquet"


def get_yfinance_fundamentals(symbol):
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        info = ticker.info
        return {
            "symbol": symbol,
            "trailingPE": info.get("trailingPE"),
            "forwardPE": info.get("forwardPE"),
            "returnOnEquity": info.get("returnOnEquity"),
            "debtToEquity": info.get("debtToEquity"),
            "dividendYield": info.get("dividendYield"),
            "trailingEps": info.get("trailingEps"),
            "marketCap": info.get("marketCap"),
            "bookValue": info.get("bookValue"),
            "priceToBook": info.get("priceToBook"),
            "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh"),
            "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow"),
            "beta": info.get("beta"),
            "dividendRate": info.get("dividendRate"),
            "payoutRatio": info.get("payoutRatio"),
            "currentPrice": info.get("currentPrice") or info.get("regularMarketPrice"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
        }
    except Exception:
        return {"symbol": symbol}


def get_screener_ratios(symbol):
    url = f"https://www.screener.in/company/{symbol}/consolidated/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, "html.parser")
        ratios = {}
        top_ratios = soup.select("ul#top-ratios li")
        for li in top_ratios:
            key_el = li.select_one("span.name")
            val_el = li.select_one("span.number")
            if key_el and val_el:
                key = key_el.get_text(strip=True)
                val = val_el.get_text(strip=True)
                ratios[key] = val
        return ratios
    except Exception:
        return {}


def parse_screener_value(val_str):
    if not val_str:
        return None
    val_str = val_str.replace(",", "").replace("%", "").strip()
    try:
        return float(val_str)
    except ValueError:
        return None


def get_full_fundamentals(symbol):
    yf_data = get_yfinance_fundamentals(symbol)
    time.sleep(2)
    screener_data = get_screener_ratios(symbol)

    # Use Screener ROCE/ROE/Book Value as authoritative for Indian stocks
    if screener_data:
        roce_val = parse_screener_value(screener_data.get("ROCE"))
        roe_val = parse_screener_value(screener_data.get("ROE"))
        book_val = parse_screener_value(screener_data.get("Book Value"))
        stock_pe = parse_screener_value(screener_data.get("Stock P/E"))

        if roce_val is not None:
            yf_data["ROCE"] = roce_val
        if roe_val is not None:
            yf_data["ROE_screener"] = roe_val
        if book_val is not None:
            yf_data["bookValue_screener"] = book_val
        if stock_pe is not None:
            yf_data["PE_screener"] = stock_pe

    return yf_data


def get_bulk_fundamentals(symbols, use_cache=True):
    if use_cache and FUNDAMENTALS_CACHE.exists():
        cached = pd.read_parquet(FUNDAMENTALS_CACHE)
        cache_age = (pd.Timestamp.now() - pd.Timestamp(FUNDAMENTALS_CACHE.stat().st_mtime, unit="s"))
        if cache_age.days < 7:
            return cached

    all_fundamentals = []
    for symbol in symbols:
        data = get_full_fundamentals(symbol)
        all_fundamentals.append(data)
        time.sleep(2)

    df = pd.DataFrame(all_fundamentals)
    df.to_parquet(FUNDAMENTALS_CACHE, index=False)
    return df


def get_dividend_history(symbol, years=5):
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        dividends = ticker.dividends
        if dividends.empty:
            return False, 0
        # Make timezone-naive for comparison
        dividends.index = dividends.index.tz_localize(None) if dividends.index.tz is None else dividends.index.tz_convert(None)
        cutoff = pd.Timestamp.now() - pd.DateOffset(years=years)
        recent = dividends[dividends.index >= cutoff]
        years_with_div = recent.groupby(recent.index.year).sum()
        consistent = len(years_with_div[years_with_div > 0]) >= years
        return consistent, len(years_with_div[years_with_div > 0])
    except Exception:
        return False, 0


def get_yearly_dividends(symbol, years=5):
    """
    Returns a dict of {year: total_dividend_per_share} for the last N years.
    e.g., {2022: 10.5, 2023: 12.0, 2024: 16.0, 2025: 16.0}
    """
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        dividends = ticker.dividends
        if dividends.empty:
            return {}
        # Make timezone-naive for comparison
        dividends.index = dividends.index.tz_localize(None) if dividends.index.tz is None else dividends.index.tz_convert(None)
        cutoff = pd.Timestamp.now() - pd.DateOffset(years=years)
        recent = dividends[dividends.index >= cutoff]
        yearly = recent.groupby(recent.index.year).sum()
        return {int(year): round(float(amount), 2) for year, amount in yearly.items() if amount > 0}
    except Exception:
        return {}
