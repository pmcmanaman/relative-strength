#!/usr/bin/env python

import os
import pandas as pd
from datetime import date
from rs_data import read_json


DIR = os.path.dirname(os.path.realpath(__file__))
PRICE_DATA = os.path.join(DIR, "data", "price_history.json")
PRICE_DATA_JSON = read_json(PRICE_DATA)


def screen_dataframe(df, passing_tickers, pct_min, pct_max):
    # Filter the DataFrame to include only passing tickers
    df_filtered = df[
        (df["Ticker"].isin(passing_tickers))
        & (df["Percentile"] >= pct_min)
        & (df["Percentile"] <= pct_max)
    ]
    return df_filtered


def run_stock_screener():
    screened_tickers = []
    for ticker in PRICE_DATA_JSON:
        if len(PRICE_DATA_JSON[ticker]["candles"]) >= 200:
            technicals = compute_technicals(ticker)
            if meets_technical_requirements(technicals):
                screened_tickers.append(ticker)

    return screened_tickers


def meets_technical_requirements(technicals):
    closing_price = technicals.get("close")
    sma_100 = technicals.get("100_day_sma")
    sma_200 = technicals.get("200_day_sma")
    sma_50 = technicals.get("50_day_sma")
    ema_21 = technicals.get("21_day_ema")
    high_52_week = technicals.get("52_week_high")
    low_52_week = technicals.get("52_week_low")

    # Check if closing price is within -25% of the 52-week high
    if high_52_week is None or closing_price >= 0.75 * high_52_week:
        # Check if price is greater than 30% over the 52-week low
        if low_52_week is None or closing_price > 1.3 * low_52_week:
            # Check if 100-day SMA is greater than 200-day SMA
            if sma_100 is None or sma_200 is None or sma_100 > sma_200:
                # Check if 50-day SMA is greater than 100-day SMA
                if sma_50 is None or sma_100 is None or sma_50 > sma_100:
                    # Check if closing price is within -10% of the 50-day SMA
                    if sma_50 is None or closing_price >= 0.9 * sma_50:
                        # Check if closing price is within -7% of the 21-day EMA
                        if ema_21 is None or closing_price >= 0.93 * ema_21:
                            # Check if latest price is greater than 12 dollars
                            if closing_price > 8:
                                # Check if latest price is greater than 200-day SMA
                                if sma_200 is None or closing_price > sma_200:
                                    return True

    return False


def compute_technicals(ticker):
    price_data = PRICE_DATA_JSON[ticker]
    candles = price_data["candles"][-252:]
    closes = [candle["close"] for candle in candles]
    return {
        "close": closes[-1],
        "21_day_ema": ema(closes, 21),
        "50_day_sma": sma(closes, 50),
        "100_day_sma": sma(closes, 100),
        "200_day_sma": sma(closes, 200),
        "52_week_high": max([candle["high"] for candle in candles]),
        "52_week_low": min([candle["low"] for candle in candles]),
    }


def sma(closes, N):
    if len(closes) < N:
        return None  # Not enough data points to compute SMA
    return sum(closes[-N:]) / N


def ema(closes, N):
    if len(closes) < N:
        return None  # Not enough data points to compute EMA
    multiplier = 2 / (N + 1)
    ema = closes[0]
    for price in closes[1:]:
        ema = (price - ema) * multiplier + ema
    return ema


def main(pct_min, pct_max):
    csv_file = os.path.join(
        DIR, "output", f'rs_stocks_{date.today().strftime("%Y%m%d")}.csv'
    )

    # Read the CSV file and convert it to a DataFrame
    df = pd.read_csv(csv_file)
    screened_tickers = run_stock_screener()
    screened_df = screen_dataframe(df, screened_tickers, pct_min, pct_max)

    screened_df.to_csv(
        os.path.join(
            DIR,
            "output/screened",
            f'rs_stocks_screened_{date.today().strftime("%Y%m%d")}.csv',
        ),
        index=False,
    )

    print("your csv was written to /output/screened")


if __name__ == "__main__":
    main()
