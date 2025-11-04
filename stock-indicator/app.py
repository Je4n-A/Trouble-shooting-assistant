from __future__ import annotations
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date, timedelta

from data import fetch_prices
from indicators import compute_indicators
from backtestor import run_backtest
from db import get_connection, upsert_prices, read_prices

st.set_page_config(page_title="Stock Indicator (RSI+MACD+BB)", layout="wide")

st.title("📈 Stock Indicator App — RSI + MACD + Bollinger Bands")

with st.sidebar:
    st.header("⚙️ Settings")
    ticker = st.text_input("Ticker", value="AAPL").strip().upper()
    col1, col2 = st.columns(2)
    with col1:
        start = st.date_input("Start", value=date.today()-timedelta(days=365))
    with col2:
        end = st.date_input("End", value=date.today())

    interval = st.selectbox("Interval", ["1d", "1h", "30m", "15m", "5m", "1m"], index=0)

    st.markdown("---")
    st.subheader("Indicators")
    rsi_len = st.number_input("RSI length", min_value=2, max_value=100, value=14, step=1)
    macd_fast = st.number_input("MACD fast", min_value=2, max_value=100, value=12, step=1)
    macd_slow = st.number_input("MACD slow", min_value=2, max_value=200, value=26, step=1)
    macd_signal = st.number_input("MACD signal", min_value=2, max_value=100, value=9, step=1)
    bb_len = st.number_input("BB length", min_value=5, max_value=200, value=20, step=1)
    bb_std = st.number_input("BB std dev", min_value=0.5, max_value=5.0, value=2.0, step=0.5, format="%.1f")

    st.markdown("---")
    use_duck = st.checkbox("Use DuckDB cache", value=False)

    run_bt = st.button("▶️ Run Backtest")

@st.cache_data(show_spinner=False)
def load_prices_cached(t, s, e, i):
    return fetch_prices(t, start=str(s), end=str(e), interval=i)

def get_prices(ticker, start, end, interval, use_duckdb=False):
    if use_duckdb:
        con = get_connection()
        df_web = load_prices_cached(ticker, start, end, interval)
        upsert_prices(df_web, ticker, con)
        df = read_prices(ticker, str(start), str(end), con)
        return df
    else:
        return load_prices_cached(ticker, start, end, interval)

df = get_prices(ticker, start, end, interval, use_duck)

if df is None or df.empty:
    st.warning("No data returned. Try a different ticker or date range.")
    st.stop()

idf = compute_indicators(df, rsi_len, macd_fast, macd_slow, macd_signal, bb_len, bb_std)

# Current signal
current = idf.iloc[-1]
signal = "Long / Holding" if current["position"] == 1 else "Flat"
sig_emoji = "🟢" if current["position"] == 1 else "⚪"
st.markdown(f"### {sig_emoji} Current Signal: **{signal}**  \nClose: **{current['Close']:.2f}**  |  RSI: **{current['RSI']:.1f}**  |  MACD hist: **{current['MACD_hist']:.3f}**")

# Plotly chart with subplots
fig = make_subplots(
    rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.02,
    row_heights=[0.6, 0.2, 0.2],
    subplot_titles=(f"{ticker} — Price & Bollinger Bands", "RSI", "MACD")
)

# Candlestick
fig.add_trace(go.Candlestick(
    x=idf.index, open=idf["Open"], high=idf["High"], low=idf["Low"], close=idf["Close"],
    name="OHLC"), row=1, col=1)

# BB
fig.add_trace(go.Scatter(x=idf.index, y=idf["BBU"], name="BBU", mode="lines"), row=1, col=1)
fig.add_trace(go.Scatter(x=idf.index, y=idf["BBM"], name="BBM", mode="lines"), row=1, col=1)
fig.add_trace(go.Scatter(x=idf.index, y=idf["BBL"], name="BBL", mode="lines"), row=1, col=1)

# Buy/Sell markers (close)
entries = idf[idf["entry"]]
exits = idf[idf["exit"]]
fig.add_trace(go.Scatter(
    x=entries.index, y=entries["Close"],
    mode="markers", marker_symbol="triangle-up", marker_size=10, name="Buy"), row=1, col=1)
fig.add_trace(go.Scatter(
    x=exits.index, y=exits["Close"],
    mode="markers", marker_symbol="triangle-down", marker_size=10, name="Sell"), row=1, col=1)

# RSI
fig.add_trace(go.Scatter(x=idf.index, y=idf["RSI"], name="RSI", mode="lines"), row=2, col=1)
fig.add_hline(y=70, line_dash="dot", row=2, col=1)
fig.add_hline(y=30, line_dash="dot", row=2, col=1)

# MACD
fig.add_trace(go.Scatter(x=idf.index, y=idf["MACD"], name="MACD", mode="lines"), row=3, col=1)
fig.add_trace(go.Scatter(x=idf.index, y=idf["MACD_signal"], name="Signal", mode="lines"), row=3, col=1)
fig.add_trace(go.Bar(x=idf.index, y=idf["MACD_hist"], name="Hist"), row=3, col=1)

fig.update_layout(xaxis_rangeslider_visible=False, height=900, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))

st.plotly_chart(fig, use_container_width=True)

if run_bt:
    with st.spinner("Running backtest..."):
        stats, bt = run_backtest(idf[["Open","High","Low","Close","Volume","entry","exit"]])
    kpis = {
        "Return [%]": float(stats["Return [%]"]),
        "CAGR [%]": float(stats.get("CAGR %", 0.0)),
        "Sharpe Ratio": float(stats.get("Sharpe Ratio", 0.0)),
        "Max. Drawdown [%]": float(stats.get("Max. Drawdown [%]", 0.0)),
        "Win Rate [%]": float(stats.get("Win Rate [%]", 0.0)),
        "# Trades": int(stats.get("# Trades", 0)),
    }
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    for (k,v), col in zip(kpis.items(), (c1,c2,c3,c4,c5,c6)):
        if isinstance(v, float):
            col.metric(k, f"{v:.2f}")
        else:
            col.metric(k, str(v))

    with st.expander("Backtest details"):
        st.write(stats.to_frame())

st.caption("Not investment advice. Educational only.")
