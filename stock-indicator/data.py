from __future__ import annotations
import yfinance as yf
import pandas as pd
from functools import lru_cache

def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.index = pd.to_datetime(df.index).tz_localize(None)
    wanted = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]
    for w in wanted:
        if w not in df.columns and w != "Adj Close":
            raise ValueError(f"Column {w} not in downloaded data.")
    if "Adj Close" not in df.columns:
        df["Adj Close"] = df["Close"]
    return df[wanted]

@lru_cache(maxsize=256)
def fetch_prices(ticker: str, start: str | None = None, end: str | None = None,
                 interval: str = "1d") -> pd.DataFrame:
    df = yf.download(ticker, start=start, end=end, interval=interval, auto_adjust=False, progress=False)
    return _normalize(df)

def latest_bar(ticker: str, interval: str = "1d") -> pd.Series | None:
    df = fetch_prices(ticker, interval=interval)
    if df is None or df.empty:
        return None
    return df.iloc[-1]
