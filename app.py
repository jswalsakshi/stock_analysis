import streamlit as st
import json
from pathlib import Path
import pandas as pd

st.set_page_config(
    page_title="Indian Stock Agent",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📈 Indian Stock Analysis Agent")
st.caption("Free, family-friendly stock picks for NSE/BSE")

# Load latest picks
picks_path = Path("data/latest_picks.json")


@st.cache_data(ttl=300)
def load_picks():
    if picks_path.exists():
        with open(picks_path) as f:
            return json.load(f)
    return None


picks = load_picks()

if picks:
    last_updated = picks.get("date", "Unknown")
    st.info(f"Last updated: {last_updated[:10] if len(last_updated) > 10 else last_updated}")

    market = picks.get("market_summary", {})
    if market:
        col1, col2, col3 = st.columns(3)
        with col1:
            nifty_change = market.get("nifty_change", 0)
            st.metric("Nifty 50", f"{nifty_change:+.2f}%",
                      delta=f"{nifty_change:.2f}%",
                      delta_color="normal")
        with col2:
            sent = market.get("market_sentiment", 0)
            sent_label = "Positive" if sent > 0.1 else "Negative" if sent < -0.1 else "Neutral"
            st.metric("Market Sentiment", sent_label, delta=f"{sent:.2f}")
        with col3:
            st.metric("Headlines", f"{len(market.get('headlines', []))} today")

    st.divider()

    # Short-term picks
    st.header("⚡ Top 5 Short-Term Picks (1-10 days)")
    short_term = picks.get("short_term", [])
    if short_term:
        for pick in short_term[:5]:
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 3])
                with col1:
                    st.subheader(pick["symbol"])
                    st.write(f"₹{pick['price']:.2f}")
                with col2:
                    st.write("**Stop Loss**")
                    st.write(f"₹{pick['stop_loss']:.2f}")
                with col3:
                    st.write("**Target**")
                    st.write(f"₹{pick['target']:.2f}")
                with col4:
                    from src.strategies.short_term import get_short_term_reason
                    st.write("**Why?**")
                    st.write(get_short_term_reason(pick))
                st.divider()
    else:
        st.warning("No short-term picks today. Market conditions may be unfavorable.")

    # Long-term picks
    st.header("💰 Top 5 Long-Term Dividend Picks (12+ months)")
    long_term = picks.get("long_term", [])
    if long_term:
        for pick in long_term[:5]:
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 3])
                with col1:
                    st.subheader(pick["symbol"])
                    st.write(f"₹{pick.get('price', 0):.2f}")
                with col2:
                    st.write("**Yield**")
                    st.write(f"{pick.get('dividend_yield', 0):.1f}%")
                with col3:
                    st.write("**ROCE**")
                    st.write(f"{pick.get('ROCE', 0):.1f}%")
                with col4:
                    from src.strategies.long_term import get_long_term_reason
                    st.write("**Why?**")
                    st.write(get_long_term_reason(pick))
                st.divider()
    else:
        st.warning("No long-term picks meeting all quality criteria today.")

    # Market headlines
    if market.get("headlines"):
        st.header("📰 Top Headlines")
        for headline in market["headlines"][:5]:
            st.write(f"• {headline}")

else:
    st.warning("No picks data available yet. Run `python jobs/daily_picks.py` to generate picks.")
    st.markdown("""
    ### Getting Started
    1. Set up your `.env` file with email credentials
    2. Run `python jobs/daily_picks.py` to generate your first set of picks
    3. The picks will appear here automatically

    ### Pages
    - **🔍 Stock Deep Dive** — Analyze any individual stock
    - **📰 News & Sentiment** — Latest market news with sentiment scores
    - **💰 Dividend Screener** — Full dividend quality screen
    - **📚 Glossary** — Plain-English financial terms
    - **⚙️ Settings** — Configure your preferences
    """)

# Disclaimer
st.markdown("---")
st.caption("⚠️ This is an automated screener for educational purposes only, not investment advice. "
           "Verify independently and consult a SEBI-registered advisor before investing.")
