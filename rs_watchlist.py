#!/usr/bin/env python
import csv
import os
from collections import defaultdict

def create_ticker_lists_by_sector(input_csv, output_dir):
    # Read the CSV file
    with open(input_csv, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        sector_industry_tickers = defaultdict(lambda: defaultdict(list))

        # Process each row in the CSV file
        for row in reader:
            sector = row['Sector'].replace('/', '')
            industry = row['Industry'].replace(',', '').replace('/', '')
            exchange = row['Exchange']
            if exchange == "NYSE MKT":
                exchange = "AMEX"
            ticker = row['Ticker']
            ticker_entry = f"{exchange}:{ticker}"

            sector_industry_tickers[sector][industry].append(ticker_entry)

    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Write tickers to separate files for each sector
    for sector, industries in sector_industry_tickers.items():
        output_txt = os.path.join(output_dir, f"00 RS - {sector}.txt")
        with open(output_txt, 'w') as txtfile:
            for industry, tickers in sorted(industries.items()):
                txtfile.write(f"###{industry},\n")
                txtfile.write(", ".join(tickers) + "\n")
        print(f"Ticker list for {sector} has been created successfully at {output_txt}.")

if __name__ == "__main__":
    input_csv = "output/rs_stocks_90th_percentile_screened_20240601.csv"  # Replace with the path to your CSV file
    output_dir = 'watchlists/90th_percentile'  # Replace with the desired output directory
    create_ticker_lists_by_sector(input_csv, output_dir)
