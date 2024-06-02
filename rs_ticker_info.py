#!/usr/bin/env python
import json
import os
import yaml
import yfinance as yf
from ftplib import FTP
from io import StringIO

DIR = os.path.dirname(os.path.realpath(__file__))

if not os.path.exists(os.path.join(DIR, "data")):
    os.makedirs(os.path.join(DIR, "data"))
if not os.path.exists(os.path.join(DIR, "tmp")):
    os.makedirs(os.path.join(DIR, "tmp"))

try:
    with open(os.path.join(DIR, "config_private.yaml"), "r") as stream:
        private_config = yaml.safe_load(stream)
except FileNotFoundError:
    private_config = None
except yaml.YAMLError as exc:
    print(exc)

try:
    with open("config.yaml", "r") as stream:
        config = yaml.safe_load(stream)
except FileNotFoundError:
    config = None
except yaml.YAMLError as exc:
    print(exc)


def cfg(key):
    try:
        return private_config[key]
    except:
        try:
            return config[key]
        except:
            return None


def exchange_from_symbol(symbol):
    if symbol == "Q":
        return "NASDAQ"
    if symbol == "A":
        return "NYSE MKT"
    if symbol == "N":
        return "NYSE"
    if symbol == "P":
        return "NYSE ARCA"
    if symbol == "Z":
        return "BATS"
    if symbol == "V":
        return "IEXG"
    return "n/a"


def read_json(json_file):
    with open(json_file, "r", encoding="utf-8") as fp:
        return json.load(fp)


REFERENCE_TICKER = cfg("REFERENCE_TICKER")
REF_TICKER = {
    "ticker": REFERENCE_TICKER,
    "sector": "--- Reference ---",
    "industry": "--- Reference ---",
    "universe": "--- Reference ---",
}


def get_resolved_securities():
    tickers = {REFERENCE_TICKER: REF_TICKER}
    return get_tickers_from_nasdaq(tickers)
    # return {"1": {"ticker": "DTST", "sector": "MICsec", "industry": "MICind", "universe": "we"}, "2": {"ticker": "MIGI", "sector": "MIGIsec", "industry": "MIGIind", "universe": "we"}}


UNKNOWN = "unknown"


def get_tickers_from_nasdaq(tickers):
    filename = "nasdaqtraded.txt"
    ticker_column = 1
    etf_column = 5
    exchange_column = 3
    test_column = 7
    ftp = FTP("ftp.nasdaqtrader.com")
    ftp.login()
    ftp.cwd("SymbolDirectory")
    lines = StringIO()
    ftp.retrlines("RETR " + filename, lambda x: lines.write(str(x) + "\n"))
    ftp.quit()
    lines.seek(0)
    results = lines.readlines()

    for entry in results:
        sec = {}
        values = entry.split("|")
        ticker = values[ticker_column]
        if (
            re.match(r"^[A-Z]+$", ticker)
            and values[etf_column] == "N"
            and values[test_column] == "N"
        ):
            sec["ticker"] = ticker
            sec["sector"] = UNKNOWN
            sec["industry"] = UNKNOWN
            sec["universe"] = exchange_from_symbol(values[exchange_column])
            tickers[sec["ticker"]] = sec

    return tickers


def write_to_file(dict, file):
    with open(file, "w", encoding="utf8") as fp:
        json.dump(dict, fp, ensure_ascii=False)


def escape_ticker(ticker):
    return ticker.replace(".", "-")


def get_info_from_dict(dict, key):
    value = dict[key] if key in dict else "n/a"
    # fix unicode
    # value = value.replace("\u2014", " ")
    return value


def load_ticker_info(info_dict, ticker):
    escaped_ticker = escape_ticker(ticker)
    info = yf.Ticker(escaped_ticker)

    try:
        ticker_info = {
            "info": {
                "industry": get_info_from_dict(info.info, "industry"),
                "sector": get_info_from_dict(info.info, "sector"),
                "marketCap": get_info_from_dict(info.info, "marketCap"),
            }
        }
        info_dict[ticker] = ticker_info
    except:
        print(f"{ticker} failed")
        print(info)


TICKER_INFO_FILE = os.path.join(DIR, "data_persist", "ticker_info.json")


def load_tickers_from_yahoo(ticker_info_dict, securities):
    print("*** Loading Stocks from Yahoo Finance ***")
    new_entries = 0

    for idx, security in enumerate(securities):
        ticker = security["ticker"]
        print(f"Loading {ticker}")
        load_ticker_info(ticker_info_dict, ticker)
        new_entries = new_entries + 1
        if new_entries % 25 == 0:
            write_to_file(ticker_info_dict, TICKER_INFO_FILE)

    return ticker_info_dict


def main():
    securities = get_resolved_securities().values()
    info_dict = read_json(TICKER_INFO_FILE)
    info_dict = load_tickers_from_yahoo(info_dict, securities)
    write_to_file(info_dict, TICKER_INFO_FILE)


if __name__ == "__main__":
    main()
