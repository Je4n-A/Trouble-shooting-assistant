from __future__ import annotations
import pandas as pd
import pandas_ta as pta

def compute_indicators(
    df: pd.DataFrame,
    rsi_len: int = 14,
    macd_fast: int = 12,
    macd_slow: int = 26,
    macd_signal: int = 9,
    bb_len: int = 20,
    bb_std: float = 2.0
) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    out = df.copy()

    # RSI
    out["RSI"] = pta.rsi(out["Close"], length=rsi_len)

    # MACD (macd, signal, hist)
    macd = pta.macd(out["Close"], fast=macd_fast, slow=macd_slow, signal=macd_signal)
    out["MACD"] = macd["MACD_12_26_9"]
    out["MACD_signal"] = macd["MACDs_12_26_9"]
    out["MACD_hist"] = macd["MACDh_12_26_9"]

    # Bollinger Bands
    bb = pta.bbands(out["Close"], length=bb_len, std=bb_std)
    out["BBL"] = bb[f"BBL_{bb_len}_{bb_std}"]
    out["BBM"] = bb[f"BBM_{bb_len}_{bb_std}"]
    out["BBU"] = bb[f"BBU_{bb_len}_{bb_std}"]

    # Simple rule-based signals
    out["rsi_below_30"] = out["RSI"] < 30
    out["rsi_above_70"] = out["RSI"] > 70
    out["macd_pos"] = out["MACD_hist"] > 0
    out["macd_neg"] = out["MACD_hist"] < 0

    # Cross detections
    out["rsi_cross_up_30"] = (out["RSI"].shift(1) < 30) & (out["RSI"] >= 30)
    out["rsi_cross_dn_70"] = (out["RSI"].shift(1) > 70) & (out["RSI"] <= 70)

    # Entry when RSI crosses up 30 AND MACD hist > 0
    # Exit when RSI crosses down 70 OR MACD hist < 0
    out["entry"] = out["rsi_cross_up_30"] & out["macd_pos"]
    out["exit"] = out["rsi_cross_dn_70"] | out["macd_neg"]

    # Position (0/1) - forward-fill entries until exit
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
