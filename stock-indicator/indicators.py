from __future__ import annotations
import pandas as pd
import numpy as np
import pandas_ta as pta

def _first_col_with(df: pd.DataFrame, prefix: str) -> str:
    for c in df.columns:
        if str(c).startswith(prefix + "_"):
            return c
    # last resort: any column that starts with prefix
    for c in df.columns:
        if str(c).startswith(prefix):
            return c
    raise KeyError(f"No column starting with {prefix}_ found. Got: {list(df.columns)}")

def compute_indicators(
    df: pd.DataFrame,
    rsi_len: int = 14,
    macd_fast: int = 12,
    macd_slow: int = 26,
    macd_signal: int = 9,
    bb_len: int = 20,
    bb_std: float = 2.0
) -> pd.DataFrame:
    if df is None or df.empty:
        return df.copy()

    out = df.copy()

    # --- RSI ---
    out["RSI"] = pta.rsi(out["Close"], length=rsi_len)

    # --- MACD (robust to naming & parameter changes) ---
    macd = pta.macd(out["Close"], fast=macd_fast, slow=macd_slow, signal=macd_signal)
    out["MACD"]        = macd[_first_col_with(macd, "MACD")]
    out["MACD_signal"] = macd[_first_col_with(macd, "MACDs")]
    out["MACD_hist"]   = macd[_first_col_with(macd, "MACDh")]

    # --- Bollinger Bands: compute manually to avoid naming quirks entirely ---
    mid = out["Close"].rolling(bb_len, min_periods=bb_len).mean()
    std = out["Close"].rolling(bb_len, min_periods=bb_len).std(ddof=0)
    out["BBM"] = mid
    out["BBU"] = mid + bb_std * std
    out["BBL"] = mid - bb_std * std

    # --- Signals ---
    out["rsi_below_30"] = out["RSI"] < 30
    out["rsi_above_70"] = out["RSI"] > 70
    out["macd_pos"] = out["MACD_hist"] > 0
    out["macd_neg"] = out["MACD_hist"] < 0

    # Crosses
    out["rsi_cross_up_30"] = (out["RSI"].shift(1) < 30) & (out["RSI"] >= 30)
    out["rsi_cross_dn_70"] = (out["RSI"].shift(1) > 70) & (out["RSI"] <= 70)

    # Entry / Exit
    out["entry"] = out["rsi_cross_up_30"] & out["macd_pos"]
    out["exit"]  = out["rsi_cross_dn_70"] | out["macd_neg"]

    # Position (0/1)
    pos = []
    holding = 0
    for en, ex in zip(out["entry"].fillna(False), out["exit"].fillna(False)):
        if holding == 0 and en:
            holding = 1
        elif holding == 1 and ex:
            holding = 0
        pos.append(holding)
    out["position"] = pd.Series(pos, index=out.index, dtype="int64")

    return out
