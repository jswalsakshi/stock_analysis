import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data.prices import get_price_data
from src.data.fundamentals import get_yfinance_fundamentals, get_screener_ratios, parse_screener_value
from src.indicators.technicals import add_all_indicators

st.set_page_config(page_title="Stock Deep Dive", page_icon="🔍", layout="wide")
st.title("🔍 Stock Deep Dive")

symbol = st.text_input("Enter NSE Symbol (e.g., RELIANCE, TCS, HDFCBANK):", value="RELIANCE").upper().strip()

if symbol:
    with st.spinner(f"Loading data for {symbol}..."):
        df = get_price_data(symbol, period="1y")

    if df.empty:
        st.error(f"Could not fetch data for {symbol}. Check if the symbol is correct.")
    else:
        df = add_all_indicators(df)

        # Current price and change
        current = df["Close"].iloc[-1]
        prev = df["Close"].iloc[-2] if len(df) > 1 else current
        change_pct = ((current - prev) / prev) * 100

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Current Price", f"₹{current:.2f}", f"{change_pct:+.2f}%")
        col2.metric("52W High", f"₹{df['High'].max():.2f}")
        col3.metric("52W Low", f"₹{df['Low'].min():.2f}")
        col4.metric("Avg Volume (20d)", f"{df['Volume'].tail(20).mean()/1e6:.1f}M")

        # Price chart with EMAs and Bollinger Bands
        st.subheader("📊 Price Chart with Technical Indicators")

        fig = make_subplots(
            rows=3, cols=1, shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.6, 0.2, 0.2],
            subplot_titles=("Price + EMAs + Bollinger Bands", "RSI (14)", "MACD")
        )

        # Candlestick
        fig.add_trace(go.Candlestick(
            x=df.index, open=df["Open"], high=df["High"],
            low=df["Low"], close=df["Close"], name="Price"
        ), row=1, col=1)

        # EMAs
        ema_cols = {"EMA_20": "blue", "EMA_50": "orange", "EMA_200": "red"}
        for col, color in ema_cols.items():
            if col in df.columns:
                fig.add_trace(go.Scatter(
                    x=df.index, y=df[col], name=col,
                    line=dict(color=color, width=1)
                ), row=1, col=1)

        # Bollinger Bands
        bb_cols = [c for c in df.columns if "BBL" in c or "BBU" in c or "BBM" in c]
        for col in bb_cols:
            fig.add_trace(go.Scatter(
                x=df.index, y=df[col], name=col,
                line=dict(dash="dot", width=1), opacity=0.5
            ), row=1, col=1)

        # RSI
        rsi_col = [c for c in df.columns if "RSI" in c]
        if rsi_col:
            fig.add_trace(go.Scatter(
                x=df.index, y=df[rsi_col[0]], name="RSI",
                line=dict(color="purple")
            ), row=2, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

        # MACD
        macd_cols = [c for c in df.columns if "MACD" in c and "h" not in c.lower() and "s" not in c.lower()]
        signal_cols = [c for c in df.columns if "MACDs" in c]
        hist_cols = [c for c in df.columns if "MACDh" in c]

        if macd_cols:
            fig.add_trace(go.Scatter(
                x=df.index, y=df[macd_cols[0]], name="MACD",
                line=dict(color="blue")
            ), row=3, col=1)
        if signal_cols:
            fig.add_trace(go.Scatter(
                x=df.index, y=df[signal_cols[0]], name="Signal",
                line=dict(color="orange")
            ), row=3, col=1)
        if hist_cols:
            colors = ["green" if v >= 0 else "red" for v in df[hist_cols[0]].fillna(0)]
            fig.add_trace(go.Bar(
                x=df.index, y=df[hist_cols[0]], name="Histogram",
                marker_color=colors
            ), row=3, col=1)

        fig.update_layout(height=800, showlegend=True, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

        # Fundamentals panel
        st.subheader("📋 Fundamentals at a Glance")
        with st.spinner("Loading fundamentals..."):
            yf_data = get_yfinance_fundamentals(symbol)
            screener_data = get_screener_ratios(symbol)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.write("**Valuation**")
            pe = yf_data.get("trailingPE")
            st.write(f"P/E Ratio: {pe:.1f}" if pe else "P/E: N/A")
            pb = yf_data.get("priceToBook")
            st.write(f"P/B Ratio: {pb:.2f}" if pb else "P/B: N/A")
            mcap = yf_data.get("marketCap")
            st.write(f"Market Cap: ₹{mcap/1e7:.0f} Cr" if mcap else "Market Cap: N/A")

        with col2:
            st.write("**Quality**")
            roe = yf_data.get("returnOnEquity")
            st.write(f"ROE: {roe*100:.1f}%" if roe else "ROE: N/A")
            roce = parse_screener_value(screener_data.get("ROCE"))
            st.write(f"ROCE: {roce:.1f}%" if roce else "ROCE: N/A")
            de = yf_data.get("debtToEquity")
            st.write(f"Debt/Equity: {de:.1f}" if de else "D/E: N/A")

        with col3:
            st.write("**Income**")
            dy = yf_data.get("dividendYield")
            st.write(f"Dividend Yield: {dy*100:.2f}%" if dy else "Div Yield: N/A")
            eps = yf_data.get("trailingEps")
            st.write(f"EPS: ₹{eps:.2f}" if eps else "EPS: N/A")
            beta = yf_data.get("beta")
            st.write(f"Beta: {beta:.2f}" if beta else "Beta: N/A")

        # Technical summary
        st.subheader("🎯 Technical Summary")
        adx_col = [c for c in df.columns if "ADX" in c and "DM" not in c]
        latest = df.iloc[-1]

        signals = []
        if rsi_col and latest[rsi_col[0]] > 70:
            signals.append("⚠️ RSI overbought (>70) — potential pullback")
        elif rsi_col and latest[rsi_col[0]] < 30:
            signals.append("🟢 RSI oversold (<30) — potential bounce")
        elif rsi_col:
            signals.append(f"RSI: {latest[rsi_col[0]]:.1f} (neutral)")

        if "EMA_50" in df.columns:
            if current > latest["EMA_50"]:
                signals.append("🟢 Price above EMA(50) — uptrend")
            else:
                signals.append("🔴 Price below EMA(50) — downtrend")

        if adx_col and latest[adx_col[0]] > 25:
            signals.append(f"📈 ADX {latest[adx_col[0]]:.0f} — strong trend")
        elif adx_col:
            signals.append(f"ADX {latest[adx_col[0]]:.0f} — weak/no trend")

        for s in signals:
            st.write(s)
