# Stock Indicator App (RSI + MACD + BB) — Streamlit

A minimal, production-friendly project that:
- fetches OHLCV with **yfinance**
- computes indicators with **pandas-ta**
- visualizes with **Plotly**
- backtests a simple rule with **Backtesting.py**
- optionally **persists** prices to **DuckDB** and **schedules** refreshes with **Prefect**

## Quick start

```bash
# 1) create a venv (recommended)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2) install deps
pip install -r requirements.txt

# 3) run the app
streamlit run app.py
```

## App features
- Ticker, date range & interval controls
- Indicator params (RSI length, MACD, Bollinger Bands)
- Candlestick + BB overlay; RSI & MACD subplots
- Buy/Sell markers from a simple rule:
  - **Enter long** when RSI crosses up from <30 **and** MACD histogram > 0
  - **Exit** when RSI crosses down from >70 **or** MACD histogram < 0
- One-click backtest → shows CAGR, Sharpe, Max Drawdown
- (Optional) Persist prices in DuckDB; (Optional) Prefect flow to refresh prices nightly

## Persistence (DuckDB)
By default the app fetches from yfinance on demand. To store/reuse prices:
1. Create a DuckDB file (the app will auto-create): `data/prices.duckdb`
2. Toggle **"Use DuckDB cache"** in the sidebar.
3. The app will **upsert** new candles and read from local storage first.

## Scheduling (Prefect)
We include a simple Prefect flow to refresh a list of tickers into DuckDB.

```bash
# run once (ad hoc refresh)
python flows/refresh_prices.py --tickers AAPL MSFT NVDA

# or register a local schedule (every day at 18:00)
prefect worker start --pool "default"
# In another terminal:
python flows/refresh_prices.py --deploy "daily-1800"
```
> For advanced deployments, see Prefect docs.

## Project layout

```
stock-indicator/
├─ app.py
├─ data.py
├─ indicators.py
├─ backtestor.py
├─ db.py
├─ flows/
│  └─ refresh_prices.py
├─ data/
│  └─ prices.duckdb  (created at runtime)
├─ .streamlit/config.toml
└─ requirements.txt
```

## Notes
- This is educational; not investment advice.
- yfinance terms apply; for intraday or robust realtime, consider Polygon/Tiingo/Alpaca.
