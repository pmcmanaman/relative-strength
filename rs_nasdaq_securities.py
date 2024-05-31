import yaml
import re
import os
from ftplib import FTP
from io import StringIO

DIR = os.path.dirname(os.path.realpath(__file__))

try:
    with open(os.path.join(DIR, 'config_private.yaml'), 'r') as stream:
        private_config = yaml.safe_load(stream)
except FileNotFoundError:
    private_config = None
except yaml.YAMLError as exc:
        print(exc)

try:
    with open('config.yaml', 'r') as stream:
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
        
REFERENCE_TICKER = cfg("REFERENCE_TICKER")
REF_TICKER = {"ticker": REFERENCE_TICKER, "sector": "--- Reference ---", "industry": "--- Reference ---", "universe": "--- Reference ---"}
UNKNOWN = "unknown"

def get_resolved_securities():
    tickers = {REFERENCE_TICKER: REF_TICKER}
    return get_tickers_from_nasdaq(tickers)
    # return {"1": {"ticker": "DTST", "sector": "MICsec", "industry": "MICind", "universe": "we"}, "2": {"ticker": "MIGI", "sector": "MIGIsec", "industry": "MIGIind", "universe": "we"}}

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

def get_tickers_from_nasdaq(tickers):
    filename = "nasdaqtraded.txt"
    ticker_column = 1
    etf_column = 5
    exchange_column = 3
    test_column = 7
    ftp = FTP('ftp.nasdaqtrader.com')
    ftp.login()
    ftp.cwd('SymbolDirectory')
    lines = StringIO()
    ftp.retrlines('RETR '+filename, lambda x: lines.write(str(x)+'\n'))
    ftp.quit()
    lines.seek(0)
    results = lines.readlines()

    for entry in results:
        sec = {}
        values = entry.split('|')
        ticker = values[ticker_column]
        if re.match(r'^[A-Z]+$', ticker) and values[etf_column] == "N" and values[test_column] == "N":
            sec["ticker"] = ticker
            sec["sector"] = UNKNOWN
            sec["industry"] = UNKNOWN
            sec["universe"] = exchange_from_symbol(values[exchange_column])
            tickers[sec["ticker"]] = sec

    return tickers