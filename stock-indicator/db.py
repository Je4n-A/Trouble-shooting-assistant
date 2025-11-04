from __future__ import annotations
import duckdb
import pandas as pd
from pathlib import Path

DEFAULT_DB_PATH = Path("data/prices.duckdb")

def get_connection(db_path: str | None = None) -> duckdb.DuckDBPyConnection:
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(path))
    con.execute('''
        CREATE TABLE IF NOT EXISTS ohlcv (
            symbol TEXT,
            ts TIMESTAMP,
            open DOUBLE,
            high DOUBLE,
            low DOUBLE,
            close DOUBLE,
            adj_close DOUBLE,
            volume BIGINT,
            PRIMARY KEY (symbol, ts)
        )
    ''')
    return con

def upsert_prices(df: pd.DataFrame, symbol: str, con: duckdb.DuckDBPyConnection) -> None:
    if df.empty:
        return
    # Normalize columns
    cols = {c.lower().replace(" ", "_"): c for c in df.columns}
    # Accept either Close/Adj Close etc.
    open_col = cols.get("open", "Open")
    high_col = cols.get("high", "High")
    low_col = cols.get("low", "Low")
    close_col = cols.get("close", "Close")
    adj_col = cols.get("adj_close", cols.get("adj_close", "Adj Close"))
    vol_col = cols.get("volume", "Volume")

    out = pd.DataFrame({
        "symbol": symbol,
        "ts": pd.to_datetime(df.index).tz_localize(None),
        "open": df[open_col].astype(float).values,
        "high": df[high_col].astype(float).values,
        "low": df[low_col].astype(float).values,
        "close": df[close_col].astype(float).values,
        "adj_close": (df[adj_col].astype(float).values if adj_col in df.columns else df[close_col].astype(float).values),
        "volume": df[vol_col].astype("Int64").fillna(0).astype("int64").values
    })

    con.execute('''
        INSERT OR REPLACE INTO ohlcv AS t
        SELECT * FROM out_df
    ''', {"out_df": out})

def read_prices(symbol: str, start: str | None, end: str | None, con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    query = "SELECT ts, open, high, low, close, adj_close, volume FROM ohlcv WHERE symbol = ?"
    params = [symbol]
    if start:
        query += " AND ts >= ?"
        params.append(pd.to_datetime(start))
    if end:
        query += " AND ts <= ?"
        params.append(pd.to_datetime(end))
    query += " ORDER BY ts"
    df = con.execute(query, params).fetch_df()
    if df.empty:
        return df
    df = df.set_index("ts")
    df.index.name = None
    df.rename(columns={
        "open": "Open", "high": "High", "low": "Low",
        "close": "Close", "adj_close": "Adj Close", "volume": "Volume"
    }, inplace=True)
    return df
