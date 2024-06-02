#!/usr/bin/env python

import csv
import os
from collections import defaultdict


def create_ticker_lists_by_sector(input_csvs, output_dir):
    # Process each input CSV file
    for input_csv in input_csvs:
        # Read the CSV file
        with open(input_csv, "r") as csvfile:
            reader = csv.DictReader(csvfile)

            # Initialize defaultdict to store tickers by sector and industry
            sector_industry_tickers = defaultdict(lambda: defaultdict(list))

            # Process each row in the CSV file
            for row in reader:
                sector = row["Sector"].replace("/", "")
                industry = row["Industry"].replace(",", "").replace("/", "")
                exchange = row["Exchange"]
                if exchange == "NYSE MKT":
                    exchange = "AMEX"
                ticker = row["Ticker"]
                ticker_entry = f"{exchange}:{ticker}"

                # Add ticker to the defaultdict
                sector_industry_tickers[sector][industry].append(ticker_entry)

        # Get the percentile from the input CSV file name
        percentile = os.path.splitext(os.path.basename(input_csv))[0].split("_")[2]

        # Create output directory for the current percentile if it doesn't exist
        percentile_output_dir = os.path.join(output_dir, f"{percentile}_percentile")
        if not os.path.exists(percentile_output_dir):
            os.makedirs(percentile_output_dir)

        # Write tickers to separate files for each sector
        for sector, industries in sector_industry_tickers.items():
            output_txt = os.path.join(percentile_output_dir, f"{sector}.txt")
            with open(output_txt, "w") as txtfile:
                # Write tickers organized by industry
                for industry, tickers in sorted(industries.items()):
                    txtfile.write(f"### {industry}\n")
                    txtfile.write(", ".join(tickers) + "\n\n")

            print(
                f"Ticker list for the {percentile} percentile in sector {sector} has been written successfully to {output_txt}."
            )


if __name__ == "__main__":
    input_csvs = [
        "output/rs_stocks_70th_percentile_screened_20240601.csv",
        "output/rs_stocks_80th_percentile_screened_20240601.csv",
        "output/rs_stocks_90th_percentile_screened_20240601.csv",
    ]
    output_dir = "watchlists"  # Replace with the desired output directory
    create_ticker_lists_by_sector(input_csvs, output_dir)
