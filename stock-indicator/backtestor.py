from __future__ import annotations
import pandas as pd
from backtesting import Backtest, Strategy

class RSIMACDStrategy(Strategy):
    def init(self):
        pass

    def next(self):
        i = len(self.data) - 1
        df = self.data._df  # pandas view

        entry = bool(df["entry"].iat[i])
        exit_ = bool(df["exit"].iat[i])

        if not self.position and entry:
            self.buy()
        elif self.position and exit_:
            self.position.close()

def run_backtest(df: pd.DataFrame, cash: float = 10000.0, commission: float = 0.0005):
    bt = Backtest(df, RSIMACDStrategy, cash=cash, commission=commission, exclusive_orders=True)
    stats = bt.run()
    return stats, bt
