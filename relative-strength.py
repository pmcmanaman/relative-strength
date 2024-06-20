#!/usr/bin/env python
import rs_ticker_info
import rs_data
import rs_mvp
import rs_ranking
import rs_stock_screener
import rs_watchlist
import argparse
import sys


def main():
    rs_ticker_info.main()
    rs_data.main()
    rs_ranking.main()
    rs_stock_screener.main(79, 99)
    rs_watchlist.main(79, 90)


if __name__ == "__main__":
    main()
