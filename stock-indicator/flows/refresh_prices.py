from __future__ import annotations
import argparse
from typing import List
from prefect import flow, task
from datetime import datetime, timedelta
from data import fetch_prices
from db import get_connection, upsert_prices

@task
def refresh_ticker(ticker: str, days_back: int = 365, interval: str = "1d") -> int:
    end = datetime.utcnow().date()
    start = end - timedelta(days=days_back)
    df = fetch_prices(ticker, start=str(start), end=str(end), interval=interval)
    con = get_connection()
    upsert_prices(df, ticker, con)
    return len(df)

@flow(name="refresh-prices")
def refresh_prices_flow(tickers: List[str], days_back: int = 365, interval: str = "1d") -> None:
    for t in tickers:
        n = refresh_ticker(t, days_back, interval)
        print(f"Refreshed {t}: {n} rows")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tickers", nargs="+", default=["AAPL","MSFT","NVDA"])
    parser.add_argument("--days_back", type=int, default=365)
    parser.add_argument("--interval", type=str, default="1d")
    parser.add_argument("--deploy", type=str, default=None, help='Name to create a local deployment with a daily 18:00 schedule')
    args = parser.parse_args()

    if args.deploy:
        from prefect.deployments import Deployment
        from prefect.server.schemas.schedules import CronSchedule

        dep = Deployment.build_from_flow(
            flow=refresh_prices_flow,
            name=args.deploy,
            parameters={"tickers": args.tickers, "days_back": args.days_back, "interval": args.interval},
            schedule=CronSchedule(cron="0 18 * * *", timezone="America/New_York"),
        )
        dep.apply()
        print(f"Applied deployment '{args.deploy}'. Start a local worker to pick it up:\n  prefect worker start --pool default")
    else:
        refresh_prices_flow(args.tickers, args.days_back, args.interval)
