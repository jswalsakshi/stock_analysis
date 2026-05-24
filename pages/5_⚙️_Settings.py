import streamlit as st
import json
from pathlib import Path

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")
st.title("⚙️ Settings")

# Settings file
settings_path = Path("data/settings.json")


def load_settings():
    if settings_path.exists():
        with open(settings_path) as f:
            return json.load(f)
    return {
        "universe": "Nifty 50",
        "risk_profile": "Balanced",
        "email_recipients": "",
        "short_term_weights": {
            "momentum": 25, "volume": 15, "rsi": 15,
            "macd": 15, "sentiment": 15, "adx": 10, "vix": 5
        },
        "long_term_weights": {
            "dividend_yield": 30, "roce": 20, "roe": 15,
            "inv_pe": 15, "inv_de": 10, "ema_slope": 10
        }
    }


def save_settings(settings):
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2)


settings = load_settings()

st.header("📊 Universe Selection")
universe = st.selectbox(
    "Stock universe to scan:",
    ["Nifty 50", "Nifty 100", "Nifty 500", "Custom"],
    index=["Nifty 50", "Nifty 100", "Nifty 500", "Custom"].index(settings.get("universe", "Nifty 50"))
)
settings["universe"] = universe

if universe == "Custom":
    st.text_area("Custom symbols (comma-separated):",
                 placeholder="RELIANCE, TCS, HDFCBANK, INFY")

st.header("🎯 Risk Profile")
risk = st.selectbox(
    "Risk tolerance:",
    ["Conservative", "Balanced", "Aggressive"],
    index=["Conservative", "Balanced", "Aggressive"].index(settings.get("risk_profile", "Balanced"))
)
settings["risk_profile"] = risk

risk_descriptions = {
    "Conservative": "Tighter stop losses, higher quality gates, fewer picks. VIX gate at 18.",
    "Balanced": "Standard settings as described in the methodology. VIX gate at 20.",
    "Aggressive": "Wider stops, relaxed quality gates, more picks. VIX gate at 25."
}
st.info(risk_descriptions[risk])

st.header("📧 Email Settings")
st.markdown("Email credentials are stored in your `.env` file for security.")
st.code("""
# In your .env file:
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_16_char_app_password
RECIPIENTS=family1@gmail.com,family2@gmail.com
""", language="bash")
st.markdown("""
**Setup steps:**
1. Enable 2-Step Verification at [myaccount.google.com/security](https://myaccount.google.com/security)
2. Generate an App Password: Security → 2-Step Verification → App Passwords
3. Add the 16-character code to your `.env` file
""")

st.header("⚖️ Scoring Weights (Short-Term)")
st.caption("Adjust how much each factor matters in short-term pick ranking. Must sum to 100%.")
col1, col2 = st.columns(2)
sw = settings.get("short_term_weights", {})
with col1:
    sw["momentum"] = st.slider("5-day Momentum", 0, 50, sw.get("momentum", 25))
    sw["volume"] = st.slider("Volume Surge", 0, 50, sw.get("volume", 15))
    sw["rsi"] = st.slider("RSI Bounce", 0, 50, sw.get("rsi", 15))
    sw["macd"] = st.slider("MACD Slope", 0, 50, sw.get("macd", 15))
with col2:
    sw["sentiment"] = st.slider("News Sentiment", 0, 50, sw.get("sentiment", 15))
    sw["adx"] = st.slider("ADX Strength", 0, 50, sw.get("adx", 10))
    sw["vix"] = st.slider("VIX Penalty", 0, 50, sw.get("vix", 5))

total = sum(sw.values())
if total != 100:
    st.warning(f"Weights sum to {total}% — should be 100%")
else:
    st.success("Weights sum to 100% ✓")
settings["short_term_weights"] = sw

st.header("⚖️ Scoring Weights (Long-Term)")
col1, col2 = st.columns(2)
lw = settings.get("long_term_weights", {})
with col1:
    lw["dividend_yield"] = st.slider("Dividend Yield", 0, 50, lw.get("dividend_yield", 30))
    lw["roce"] = st.slider("ROCE", 0, 50, lw.get("roce", 20))
    lw["roe"] = st.slider("ROE", 0, 50, lw.get("roe", 15))
with col2:
    lw["inv_pe"] = st.slider("Inverse P/E (Value)", 0, 50, lw.get("inv_pe", 15))
    lw["inv_de"] = st.slider("Inverse D/E (Low Debt)", 0, 50, lw.get("inv_de", 10))
    lw["ema_slope"] = st.slider("EMA Slope (Stability)", 0, 50, lw.get("ema_slope", 10))

lt_total = sum(lw.values())
if lt_total != 100:
    st.warning(f"Long-term weights sum to {lt_total}% — should be 100%")
else:
    st.success("Long-term weights sum to 100% ✓")
settings["long_term_weights"] = lw

st.divider()
if st.button("💾 Save Settings"):
    save_settings(settings)
    st.success("Settings saved!")
    st.balloons()
