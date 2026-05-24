import streamlit as st

st.set_page_config(page_title="Glossary", page_icon="📚", layout="wide")
st.title("📚 Glossary – Plain English Financial Terms")

st.markdown("""
Understanding stock market terms doesn't need to be complicated.
Here's every term used in this app, explained in one sentence each.
""")

glossary = {
    "Price & Market": {
        "NSE": "National Stock Exchange of India — the main stock exchange where most Indian stocks trade.",
        "BSE": "Bombay Stock Exchange — India's oldest stock exchange; some stocks trade only here.",
        "Nifty 50": "An index of the 50 largest companies on NSE — the benchmark for Indian markets.",
        "Sensex": "An index of 30 large BSE companies — like Nifty but smaller and older.",
        "Market Cap": "Total value of all a company's shares — big number means big company.",
        "52-Week High/Low": "The highest and lowest price a stock reached in the past year.",
        "Volume": "Number of shares traded today — high volume means lots of interest.",
        "Bull Market": "When prices are generally rising over time.",
        "Bear Market": "When prices are generally falling over time.",
    },
    "Valuation (Is it expensive?)": {
        "P/E Ratio (Price-to-Earnings)": "How much you pay for ₹1 of company profit — lower is cheaper.",
        "P/B Ratio (Price-to-Book)": "How much you pay for ₹1 of company assets — below 1 may be undervalued.",
        "EPS (Earnings Per Share)": "Profit divided by number of shares — higher means more profitable per share.",
        "Dividend Yield": "Annual dividend as a % of share price — like the 'interest rate' you earn for holding.",
        "Payout Ratio": "What % of profits a company pays as dividends — above 70% may not be sustainable.",
    },
    "Quality (Is it a good company?)": {
        "ROE (Return on Equity)": "How well the company uses shareholder money to make profit — above 15% is good.",
        "ROCE (Return on Capital Employed)": "How well the company uses ALL its capital (debt + equity) — the Indian investor's favourite metric.",
        "Debt/Equity Ratio": "How much borrowed money vs own money — below 1 is conservative, above 2 is risky.",
        "Free Cash Flow": "Cash left after running the business and buying equipment — positive is healthy.",
    },
    "Technical Indicators (Timing)": {
        "EMA (Exponential Moving Average)": "A smoothed average of recent prices — price above EMA = uptrend.",
        "RSI (Relative Strength Index)": "Measures how fast price moved recently (0-100) — above 70 = overbought, below 30 = oversold.",
        "MACD": "Shows when short-term momentum crosses long-term — a 'buy' signal when MACD crosses above its signal line.",
        "Bollinger Bands": "A channel around price — when price touches the lower band, it may bounce back up.",
        "ADX (Average Directional Index)": "Measures trend strength (not direction) — above 25 means strong trend.",
        "ATR (Average True Range)": "How much a stock typically moves per day — used to set stop losses.",
        "OBV (On-Balance Volume)": "Tracks whether volume flows in (buying) or out (selling).",
    },
    "Strategy Terms": {
        "Stop Loss": "A price where you sell to limit losses — like a safety net.",
        "Target Price": "The price where you plan to take profits.",
        "Risk-Reward Ratio": "Potential profit divided by potential loss — we target at least 2:1 (gain twice what you risk).",
        "Swing Trade": "Holding a stock for 1-10 days to profit from short price moves.",
        "Value Investing": "Buying quality companies when they're cheap and holding long-term.",
    },
    "Sentiment & News": {
        "India VIX": "The 'fear gauge' — above 20 means markets are nervous, below 15 means calm.",
        "Sentiment Score": "A number from -1 to +1 based on news headlines — positive means good news.",
        "VADER": "The algorithm we use to score sentiment from text — fast but not perfect.",
    },
    "Risk & Tax (India-specific)": {
        "STCG (Short-Term Capital Gains)": "15% tax on stocks sold within 1 year of buying.",
        "LTCG (Long-Term Capital Gains)": "10% tax on gains above ₹1 lakh if held more than 1 year.",
        "STT (Securities Transaction Tax)": "A small tax charged on every buy/sell — already included in your broker's bill.",
        "SEBI": "Securities and Exchange Board of India — the market regulator (like the referee).",
    },
}

for category, terms in glossary.items():
    st.subheader(category)
    for term, definition in terms.items():
        st.markdown(f"**{term}** — {definition}")
    st.divider()

st.caption("💡 Tip: If a family member asks 'what does this number mean?', send them this page!")
