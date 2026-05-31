import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data.prices import get_universe
from src.strategies.momentum_sma import screen_momentum_sma

st.set_page_config(page_title="RSI + SMA50 Screener", page_icon="📈", layout="wide")
st.title("📈 RSI + SMA50 Momentum Screener")

st.markdown("""
This screener finds stocks matching **multi-timeframe RSI momentum** with **SMA50 support**:

**RSI Criteria:**
- Monthly RSI ≥ 60 (strong long-term momentum)
- Weekly RSI ≥ 60 (strong medium-term momentum)
- Daily RSI between 48–65 (not overbought, good entry zone)

**SMA50 Criteria:**
- Stock is taking support on 50-day SMA, OR
- Stock has consolidated near SMA50 for 2–5 candles

These conditions identify stocks in a strong uptrend that are pulling back to a key support level — ideal swing trade entries.
""")

st.warning("⚠️ This screen fetches daily, weekly, and monthly data for each stock. It may take 5–10 minutes.")

if st.button("🚀 Run RSI + SMA50 Screen"):
    symbols = get_universe()
    with st.spinner(f"Screening {len(symbols)} stocks across 3 timeframes..."):
        results = screen_momentum_sma(symbols)

    if not results.empty:
        st.success(f"✅ Found {len(results)} stocks matching all criteria!")

        st.dataframe(
            results.style.format({
                "price": "₹{:.2f}",
                "sma50": "₹{:.2f}",
                "daily_rsi": "{:.1f}",
                "weekly_rsi": "{:.1f}",
                "monthly_rsi": "{:.1f}",
                "price_vs_sma50_pct": "{:+.2f}%",
            }),
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("---")
        st.subheader("📖 How to read this")
        st.markdown("""
        | Column | Meaning |
        |--------|---------|
        | `daily_rsi` | RSI(14) on daily chart (48–65 = healthy pullback zone) |
        | `weekly_rsi` | RSI(14) on weekly chart (≥60 = strong trend) |
        | `monthly_rsi` | RSI(14) on monthly chart (≥60 = macro uptrend) |
        | `sma50` | 50-day Simple Moving Average value |
        | `price_vs_sma50_pct` | How far price is from SMA50 (near 0% = at support) |
        """)

        csv = results.to_csv(index=False)
        st.download_button(
            label="📥 Download Results as CSV",
            data=csv,
            file_name="rsi_sma50_picks.csv",
            mime="text/csv",
        )
    else:
        st.info("No stocks currently match all RSI + SMA50 criteria. Try again when the market pulls back to support levels.")

st.markdown("---")
st.caption("Strategy: Multi-timeframe RSI confirms trend strength while SMA50 proximity identifies low-risk entry points.")
