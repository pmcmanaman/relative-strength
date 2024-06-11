#!/usr/bin/env python
import rs_ticker_info
import rs_data
import rs_ranking
import rs_stock_screener
import rs_watchlist
import argparse
import sys


def main():
    parser = argparse.ArgumentParser(description="Process stock screening parameters.")
    parser.add_argument(
        "pct_min", type=int, nargs="?", default=79, help="Minimum percentile"
    )
    parser.add_argument(
        "pct_max", type=int, nargs="?", default=99, help="Maximum percentile"
    )
    parser.add_argument(
        "watchlist_prefix", type=int, nargs="?", default=90, help="Watchlist prefix"
    )

    args = parser.parse_args()
    pct_min = args.pct_min
    pct_max = args.pct_max
    prefix = args.watchlist_prefix

    # rs_ticker_info.main()
    # rs_data.main()
    # rs_ranking.main()
    rs_stock_screener.main(pct_min, pct_max)
    rs_watchlist.main(pct_min, prefix)


if __name__ == "__main__":
    main()
