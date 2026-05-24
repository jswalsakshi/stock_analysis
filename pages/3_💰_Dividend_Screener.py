import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data.prices import get_universe
from src.strategies.long_term import screen_long_term

st.set_page_config(page_title="Dividend Screener", page_icon="💰", layout="wide")
st.title("💰 Long-Term Dividend Screener")

st.markdown("""
This screen scores each stock on:
- **Dividend Yield** — higher yield = more income (25 pts)
- **ROCE > 12%** — capital efficiency (20 pts)
- **Low Debt/Equity** — financial safety (20 pts)
- **P/E < 30** — reasonable valuation (15 pts)
- **ROE > 10%** — shareholder returns (10 pts)
- **200-day EMA uptrend** — not a falling knife (10 pts)

Stocks are ranked by total score out of 100. Top scorers = best dividend picks.
""")

# Load from cache if available
picks_path = Path("data/latest_picks.json")

tab1, tab2 = st.tabs(["📋 Latest Screen Results", "🔄 Run Fresh Screen"])

with tab1:
    if picks_path.exists():
        import json
        with open(picks_path) as f:
            picks = json.load(f)
        long_term = picks.get("long_term", [])
        if long_term:
            df = pd.DataFrame(long_term)
            display_cols = ["symbol", "price", "dividend_per_share", "dividend_yield", "ROCE", "ROE",
                           "debt_to_equity", "trailing_PE", "sector"]
            available_cols = [c for c in display_cols if c in df.columns]
            st.dataframe(
                df[available_cols].style.format({
                    "price": "₹{:.2f}",
                    "dividend_per_share": "₹{:.2f}",
                    "dividend_yield": "{:.1f}%",
                    "ROCE": "{:.1f}%",
                    "ROE": "{:.1f}%",
                    "debt_to_equity": "{:.1f}",
                    "trailing_PE": "{:.1f}",
                }),
                use_container_width=True,
                hide_index=True,
            )

            # Year-wise dividend history
            div_year_cols = sorted([c for c in df.columns if c.startswith("Div_")])
            if div_year_cols:
                st.subheader("📅 Year-wise Annual Dividend Per Share (₹)")
                div_display = ["symbol"] + div_year_cols
                available_div = [c for c in div_display if c in df.columns]
                div_format = {c: "₹{:.2f}" for c in div_year_cols if c in df.columns}
                st.dataframe(
                    df[available_div].fillna(0).style.format(div_format),
                    use_container_width=True, hide_index=True
                )

            # Download CSV
            csv = df[available_cols].to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name="dividend_picks.csv",
                mime="text/csv"
            )
        else:
            st.info("No dividend picks in the latest run. Run a fresh screen below.")
    else:
        st.info("No cached results. Run the daily job or use the fresh screen tab.")

with tab2:
    st.warning("⚠️ Running a fresh screen takes several minutes due to rate-limited API calls.")
    if st.button("🚀 Run Dividend Screen Now"):
        symbols = get_universe()
        with st.spinner(f"Screening {len(symbols)} stocks... This may take 5-10 minutes."):
            results = screen_long_term(symbols)
        if not results.empty:
            st.success(f"Found {len(results)} stocks passing criteria!")

            # Main metrics table
            display_cols = ["symbol", "price", "score", "dividend_per_share", "dividend_yield", "ROCE", "ROE",
                           "debt_to_equity", "trailing_PE", "sector"]
            available_cols = [c for c in display_cols if c in results.columns]
            st.dataframe(results[available_cols], use_container_width=True, hide_index=True)

            # Year-wise dividend history table
            div_year_cols = sorted([c for c in results.columns if c.startswith("Div_")])
            if div_year_cols:
                st.subheader("📅 Year-wise Annual Dividend Per Share (₹)")
                div_display = ["symbol"] + div_year_cols
                div_format = {c: "₹{:.2f}" for c in div_year_cols}
                st.dataframe(
                    results[div_display].fillna(0).style.format(div_format),
                    use_container_width=True, hide_index=True
                )

            csv = results.to_csv(index=False)
            st.download_button(
                label="📥 Download Results",
                data=csv,
                file_name="dividend_screen_full.csv",
                mime="text/csv"
            )
        else:
            st.warning("No stocks passed all quality criteria.")

st.markdown("---")
st.caption("Screen methodology mirrors the Nifty Dividend Opportunities 50 index approach. "
           "Fundamentals from yfinance + Screener.in. Refresh weekly for best results.")
