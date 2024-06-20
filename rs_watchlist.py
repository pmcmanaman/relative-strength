#!/usr/bin/env python

import csv
import os
from collections import defaultdict
from datetime import date


def create_ticker_lists_by_sector(input_csvs, percentile, prefix, output_dir):
    # Process each input CSV file
    for input_csv in input_csvs:
        # Read the CSV file
        with open(input_csv, "r") as csvfile:
            reader = csv.DictReader(csvfile)

            # Initialize defaultdict to store tickers by sector and industry
            sector_industry_tickers = defaultdict(lambda: defaultdict(list))
            tickers = []

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
                tickers.append(ticker_entry)

        # Create output directory for the current percentile if it doesn't exist
        percentile_output_dir = os.path.join(output_dir, f"{percentile}_percentile")
        if not os.path.exists(percentile_output_dir):
            os.makedirs(percentile_output_dir)

        # Write tickers organized by sector and industry to separate files
        for sector, industries in sector_industry_tickers.items():
            sector_filename = f"{prefix} - RS {sector}.txt"
            sector_filepath = os.path.join(percentile_output_dir, sector_filename)
            with open(sector_filepath, "w") as sector_file:
                for industry, tickers in sorted(industries.items()):
                    sector_file.write(f"### {industry}\n")
                    sector_file.write(", ".join(tickers) + "\n\n")

        # Write the tickers to a single file if required
        base_name = os.path.basename(input_csv).split(".")[0]
        output_txt = os.path.join(
            percentile_output_dir,
            f"{prefix} - RS {base_name}.txt",
        )

        with open(output_txt, "w") as txtfile:
            if "rs_stocks_screened" in base_name:
                # Write tickers organized by industry within each sector
                for sector, industries in sector_industry_tickers.items():
                    txtfile.write(f"## {sector}\n")
                    for industry, tickers in sorted(industries.items()):
                        txtfile.write(f"### {industry}\n")
                        txtfile.write(", ".join(tickers) + "\n\n")
            else:
                # Write only tickers for filtered_mvps
                txtfile.write(", ".join(tickers) + "\n")

        print(
            f"Ticker list for the {percentile} percentile from {input_csv} has been written successfully to {output_txt}."
        )


def main(pct_min, prefix):
    input_csvs = [f'output/rs_stocks_screened_{date.today().strftime("%Y%m%d")}.csv']
    output_dir = "watchlists"  # Replace with the desired output directory
    create_ticker_lists_by_sector(input_csvs, pct_min, prefix, output_dir)


if __name__ == "__main__":
    main(79, 90)
