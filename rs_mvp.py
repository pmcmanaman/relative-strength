#!/usr/bin/env python
import pandas as pd
import json
import os
from datetime import datetime, date
import rs_stock_screener

# Define the directory and file names for the price data and RS stocks data
DIR = os.path.dirname(os.path.realpath(__file__))
PRICE_DATA_FILE = os.path.join(DIR, "data", "price_history.json")


def load_price_data(file_path):
    """Load price data from a JSON file."""
    with open(file_path, "r") as f:
        return json.load(f)


def load_rs_stocks(file_path):
    """Load RS stocks data from a CSV file."""
    return pd.read_csv(file_path)


def find_12_up_days_in_15(candles):
    """Find the start date if there is a period where 12 out of 15 days are up days."""
    six_mo = candles[-63:-1]  # last ~3 months
    if len(six_mo) < 16:
        return (None, None)
    for i in range(len(six_mo) - 16):
        period = six_mo[i : i + 16]
        up_days = sum(
            1 for j in range(1, 16) if period[j]["close"] > period[j - 1]["close"]
        )
        gain = percentage_gain(period)
        if up_days >= 12 and gain > 20:
            return (period[0]["datetime"], gain)  # Return the start date of the period
    return (None, None)


def percentage_gain(period):
    """Calculate the percentage gain during the period."""
    start_price = period[0]["close"]
    max_gain = max(
        (candle["close"] - start_price) / start_price * 100 for candle in period
    )
    return max_gain


def scan_tickers_for_up_days(price_data):
    """Scan all tickers for the specified condition."""
    results = []
    for ticker, data in price_data.items():
        (start_date, gain) = find_12_up_days_in_15(data["candles"])
        if start_date:
            results.append((ticker, start_date, gain))
    return results


def main():
    price_data = load_price_data(PRICE_DATA_FILE)
    rs_stocks_df = load_rs_stocks(
        os.path.join(DIR, "output", f'rs_stocks_{date.today().strftime("%Y%m%d")}.csv')
    )
    rs_tickers = set(rs_stocks_df["Ticker"])

    results = scan_tickers_for_up_days(price_data)
    results.sort(key=lambda x: x[1], reverse=True)

    # Prepare the data for the CSV
    filtered_data = []
    if results:
        for ticker, start_date, gain in results:
            if ticker in rs_tickers:
                technicals = rs_stock_screener.compute_technicals(ticker)
                if rs_stock_screener.meets_technical_requirements(technicals):
                    stock_info = rs_stocks_df[rs_stocks_df["Ticker"] == ticker].iloc[0]
                    filtered_data.append(stock_info)

    # Create a DataFrame and write to CSV
    if filtered_data:
        filtered_df = pd.DataFrame(filtered_data)
        output_file = os.path.join(
            DIR, "output", f'filtered_mvps_{date.today().strftime("%Y%m%d")}.csv'
        )
        filtered_df.to_csv(output_file, index=False)
        print(f"Results written to {output_file}")
    else:
        print("No tickers found with the specified condition.")


if __name__ == "__main__":
    main()
