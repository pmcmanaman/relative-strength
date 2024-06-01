#!/usr/bin/env python
import sys
import pandas as pd
import numpy as np
import json
import os
from datetime import date
from scipy.stats import linregress
import yaml
from rs_data import cfg, read_json
from functools import reduce

DIR = os.path.dirname(os.path.realpath(__file__))

pd.set_option("display.max_rows", None)
pd.set_option("display.width", None)
pd.set_option("display.max_columns", None)

try:
    with open("config.yaml", "r") as stream:
        config = yaml.safe_load(stream)
except FileNotFoundError:
    config = None
except yaml.YAMLError as exc:
    print(exc)

PRICE_DATA = os.path.join(DIR, "data", "price_history.json")
PRICE_DATA_JSON = read_json(PRICE_DATA)
MIN_PERCENTILE = cfg("MIN_PERCENTILE")
ALL_STOCKS = cfg("USE_ALL_LISTED_STOCKS")
TICKER_INFO_FILE = os.path.join(DIR, "data_persist", "ticker_info.json")
TICKER_INFO_JSON = read_json(TICKER_INFO_FILE)
REFERENCE_TICKER = cfg("REFERENCE_TICKER")
REFERENCE_PRICE_SERIES = pd.Series(
    list(
        map(
            lambda candle: candle["close"], PRICE_DATA_JSON[REFERENCE_TICKER]["candles"]
        )
    )
)

TITLE_RANK = "Rank"
TITLE_TICKER = "Ticker"
TITLE_TICKERS = "Tickers"
TITLE_SECTOR = "Sector"
TITLE_INDUSTRY = "Industry"
TITLE_MCAP = "Market Cap"
TITLE_UNIVERSE = "Universe" if not ALL_STOCKS else "Exchange"
TITLE_PERCENTILE = "Percentile"
TITLE_1M = "1 Month Ago"
TITLE_3M = "3 Months Ago"
TITLE_6M = "6 Months Ago"
TITLE_RS = "Relative Strength"

if not os.path.exists("output"):
    os.makedirs("output")


def relative_strength(closes: pd.Series, closes_ref: pd.Series):
    rs_stock = strength(closes)
    rs_ref = strength(closes_ref)
    rs = (1 + rs_stock) / (1 + rs_ref) * 100
    rs = int(rs * 100) / 100  # round to 2 decimals
    return rs


def strength(closes: pd.Series):
    """Calculates the performance of the last year (most recent quarter is weighted double)"""
    try:
        quarters1 = quarters_perf(closes, 1)
        quarters2 = quarters_perf(closes, 2)
        quarters3 = quarters_perf(closes, 3)
        quarters4 = quarters_perf(closes, 4)
        return 0.4 * quarters1 + 0.2 * quarters2 + 0.2 * quarters3 + 0.2 * quarters4
    except:
        return 0


def quarters_perf(closes: pd.Series, n):
    if len(closes) < (n * int(252 / 4)):
        return 0

    start_price = closes.iloc[-n * int(252 / 4)]  # Price 'n' quarters ago
    end_price = closes.iloc[-1]  # Price at the end of the period
    return (end_price / start_price) - 1  # Percentage change in price over the period


def ticker_info(ticker, field):
    return (
        TICKER_INFO_JSON[ticker]["info"][field]
        if PRICE_DATA_JSON[ticker][field] == "unknown"
        else PRICE_DATA_JSON[ticker][field]
    )


def compute_relative_strength(ticker, relative_strengths):
    closes = list(
        map(lambda candle: candle["close"], PRICE_DATA_JSON[ticker]["candles"])
    )

    market_cap = (
        TICKER_INFO_JSON[ticker]["info"]["marketCap"]
        if ticker in TICKER_INFO_JSON
        and "marketCap" in TICKER_INFO_JSON[ticker]["info"]
        else "n/a"
    )

    if (
        len(closes) >= 6 * 20
        and market_cap != "n/a"
        and int(market_cap) > 300_000_000
        and closes[-1] > 10
    ):
        closes_series = pd.Series(closes)
        rs = relative_strength(closes_series, REFERENCE_PRICE_SERIES)
        month = 20
        tmp_percentile = 100
        rs1m = relative_strength(
            closes_series.head(-1 * month), REFERENCE_PRICE_SERIES.head(-1 * month)
        )
        rs3m = relative_strength(
            closes_series.head(-3 * month), REFERENCE_PRICE_SERIES.head(-3 * month)
        )
        rs6m = relative_strength(
            closes_series.head(-6 * month), REFERENCE_PRICE_SERIES.head(-6 * month)
        )

        # if rs is too big assume there is faulty price data
        if rs < 600:
            # stocks output
            relative_strengths.append(
                (
                    0,
                    ticker,
                    ticker_info(ticker, "sector"),
                    ticker_info(ticker, "industry"),
                    PRICE_DATA_JSON[ticker]["universe"],
                    rs,
                    tmp_percentile,
                    rs1m,
                    rs3m,
                    rs6m,
                    market_cap,
                    closes[-1],
                )
            )  # Include market cap in the tuple


def convert_to_dataframe(relative_strengths):
    df = pd.DataFrame(
        relative_strengths,
        columns=[
            TITLE_RANK,
            TITLE_TICKER,
            TITLE_SECTOR,
            TITLE_INDUSTRY,
            TITLE_UNIVERSE,
            TITLE_RS,
            TITLE_PERCENTILE,
            TITLE_1M,
            TITLE_3M,
            TITLE_6M,
            "Market Cap",
            "Close",
        ],
    )  # Include "Market Cap" column in columns list
    df[TITLE_PERCENTILE] = pd.qcut(df[TITLE_RS], 100, labels=False, duplicates="drop")
    df[TITLE_1M] = pd.qcut(df[TITLE_1M], 100, labels=False, duplicates="drop")
    df[TITLE_3M] = pd.qcut(df[TITLE_3M], 100, labels=False, duplicates="drop")
    df[TITLE_6M] = pd.qcut(df[TITLE_6M], 100, labels=False, duplicates="drop")
    df = df.sort_values(([TITLE_RS]), ascending=False)
    df[TITLE_RANK] = list(range(1, len(relative_strengths) + 1))
    return df


def write_csv(df):
    qualifying_tickers = 0
    for index, row in df.iterrows():
        if row[TITLE_PERCENTILE] >= MIN_PERCENTILE:
            qualifying_tickers = qualifying_tickers + 1
    df = df.head(qualifying_tickers)

    df.to_csv(
        os.path.join(DIR, "output", f'rs_stocks_{date.today().strftime("%Y%m%d")}.csv'),
        index=False,
    )


def compute_relative_strengths():
    """Returns a dataframe with percentile rankings for relative strength including a column for market capitalization"""
    relative_strengths = []
    for ticker in PRICE_DATA_JSON:
        compute_relative_strength(ticker, relative_strengths)

    return relative_strengths


def main():
    relative_strengths = compute_relative_strengths()
    df = convert_to_dataframe(relative_strengths)
    write_csv(df)
    print("***\nYour csv is in the output folder.\n***")


if __name__ == "__main__":
    main()
