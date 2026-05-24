import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data.news import get_news_sentiment, get_market_sentiment, score_sentiment

st.set_page_config(page_title="News & Sentiment", page_icon="📰", layout="wide")
st.title("📰 News & Sentiment")

# Market-wide sentiment
st.header("🌍 Market Sentiment")
with st.spinner("Fetching market news..."):
    market_avg, market_articles = get_market_sentiment()

if market_avg > 0.1:
    sentiment_color = "🟢"
    sentiment_text = "Positive"
elif market_avg < -0.1:
    sentiment_color = "🔴"
    sentiment_text = "Negative"
else:
    sentiment_color = "🟡"
    sentiment_text = "Neutral"

col1, col2 = st.columns([1, 3])
with col1:
    st.metric("Market Mood", f"{sentiment_color} {sentiment_text}", f"Score: {market_avg:.3f}")
with col2:
    st.progress(min(max((market_avg + 1) / 2, 0.0), 1.0))
    st.caption("← Negative | Neutral | Positive →")

if market_articles:
    st.subheader("Top Market Headlines")
    for article in market_articles[:10]:
        sent = article["sentiment"]
        icon = "🟢" if sent > 0.1 else "🔴" if sent < -0.1 else "🟡"
        st.write(f"{icon} **{article['title']}**")
        st.caption(f"Source: {article['source']} | Sentiment: {sent:.3f}")

st.divider()

# Stock-specific sentiment
st.header("🔍 Stock-Specific News")
symbol = st.text_input("Enter NSE Symbol:", value="RELIANCE").upper().strip()

if symbol:
    with st.spinner(f"Fetching news for {symbol}..."):
        avg_sent, articles = get_news_sentiment(symbol, max_results=10)

    if articles:
        if avg_sent > 0.1:
            st.success(f"Overall sentiment for {symbol}: Positive ({avg_sent:.3f})")
        elif avg_sent < -0.1:
            st.error(f"Overall sentiment for {symbol}: Negative ({avg_sent:.3f})")
        else:
            st.info(f"Overall sentiment for {symbol}: Neutral ({avg_sent:.3f})")

        st.subheader(f"Latest Headlines for {symbol}")
        for article in articles:
            sent = article["sentiment"]
            icon = "🟢" if sent > 0.1 else "🔴" if sent < -0.1 else "🟡"
            st.write(f"{icon} **{article['title']}**")
            col1, col2 = st.columns([3, 1])
            with col1:
                st.caption(f"Source: {article['source']} | {article['published']}")
            with col2:
                st.caption(f"Sentiment: {sent:.3f}")
    else:
        st.warning(f"No recent news found for {symbol}.")

st.markdown("---")
st.caption("Sentiment is computed using NLTK's VADER model on news headlines. "
           "Score ranges from -1 (very negative) to +1 (very positive). "
           "This is one signal among many — do not trade on sentiment alone.")
