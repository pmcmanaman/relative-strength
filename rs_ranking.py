#!/usr/bin/env python
import pandas as pd
import os
from datetime import date
import yaml
from rs_data import cfg, read_json

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
TITLE_CLOSE = "Close"

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

    if len(closes) >= 200:
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
            )


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
            TITLE_MCAP,
            TITLE_CLOSE,
        ],
    )  # Include "Market Cap" column in columns list
    df[TITLE_PERCENTILE] = pd.qcut(df[TITLE_RS], 100, labels=False, duplicates="drop")
    df[TITLE_1M] = pd.qcut(df[TITLE_1M], 100, labels=False, duplicates="drop")
    df[TITLE_3M] = pd.qcut(df[TITLE_3M], 100, labels=False, duplicates="drop")
    df[TITLE_6M] = pd.qcut(df[TITLE_6M], 100, labels=False, duplicates="drop")
    df = df.sort_values(([TITLE_RS]), ascending=False)
    df[TITLE_RANK] = list(range(1, len(relative_strengths) + 1))
    return df


def write_csv(df, filename, percentile_min, percentile_max):
    filtered_df = df[
        (df[TITLE_PERCENTILE] >= percentile_min)
        & (df[TITLE_PERCENTILE] <= percentile_max)
    ]

    filtered_df.to_csv(
        os.path.join(DIR, "output", filename),
        index=False,
    )


def compute_relative_strengths():
    """Returns a dataframe with percentile rankings for relative strength including a column for market capitalization"""
    relative_strengths = []
    for ticker in PRICE_DATA_JSON:
        compute_relative_strength(ticker, relative_strengths)

    return relative_strengths


def screen_dataframe(df, passing_tickers):
    # Filter the DataFrame to include only passing tickers
    df_filtered = df[df[TITLE_TICKER].isin(passing_tickers)]
    return df_filtered


def screened_tickers():
    screened_tickers = []
    for ticker in PRICE_DATA_JSON:
        if len(PRICE_DATA_JSON[ticker]["candles"]) >= 200:
            technicals = compute_technicals(ticker)
            if meets_technical_requirements(technicals):
                screened_tickers.append(ticker)

    return screened_tickers


def meets_technical_requirements(technicals):
    closing_price = technicals["close"]
    sma_100 = technicals["100_day_sma"]
    sma_200 = technicals["200_day_sma"]
    sma_50 = technicals["50_day_sma"]
    ema_21 = technicals["21_day_ema"]
    high_52_week = technicals["52_week_high"]
    low_52_week = technicals["52_week_low"]

    # Check if closing price is within -25% of the 52-week high
    if closing_price >= 0.75 * high_52_week:
        # Check if price is greater than 30% over the 52-week low
        if closing_price > 1.3 * low_52_week:
            # Check if 100-day SMA is greater than 200-day SMA
            if sma_100 > sma_200:
                # Check if 50-day SMA is greater than 100-day SMA
                if sma_50 > sma_100:
                    # Check if closing price is within -10% of the 50-day SMA
                    if closing_price >= 0.9 * sma_50:
                        # Check if closing price is within -7% of the 21-day EMA
                        if closing_price >= 0.93 * ema_21:
                            # Check if latest price is greater than 12 dollars
                            if closing_price > 12:
                                # Check if latest price is greater than 200-day SMA
                                if closing_price > sma_200:
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


def main():
    relative_strengths = compute_relative_strengths()
    df = convert_to_dataframe(relative_strengths)
    df_screened = screen_dataframe(df, screened_tickers())

    write_csv(df, f'rs_stocks_{date.today().strftime("%Y%m%d")}.csv', 69, 99)

    print("***\nYour csvs are in the output folder.\n***")


if __name__ == "__main__":
    main()
