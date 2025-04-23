"""
This script processes JSON-based EEO-1 form data by aggregating job category information,
joining with NAICS industry classifications and geographic data, and producing several
intermediate and final CSV outputs. It includes logic for:
- Aggregating JSON records into a master DataFrame
- Joining NAICS labels using 2-digit codes
- Computing organizational sizes and binning them
- Mapping ZIP codes to counties via two external datasets
The result is a fully joined and enriched dataset with county-level identifiers.
"""

import os
import pandas as pd
import numpy as np

from aggregation import json_to_df  # Custom function to parse JSON and aggregate

if __name__ == "__main__":
    # === Step 1: Aggregate all JSON files ===
    input_dir = "/home/node0/Documents/eeo1_json"
    output_dir = f"{input_dir}/../csv_output"
    agg_df = json_to_df(input_dir)

    # Ensure zip codes are treated as strings
    agg_df['zip code'] = agg_df['zip code'].astype(str)
    agg_df['HQ zip code'] = agg_df['HQ zip code'].astype(str)

    # Save aggregated output
    agg_df.to_csv(os.path.join(output_dir, "aggregation.csv"))

    # Reload it just in case
    agg_df = pd.read_csv(os.path.join(output_dir, "aggregation.csv"))

    # === Step 2: Join with 2-digit NAICS code descriptions ===
    naics_df = pd.read_csv("../public_data/naics_2digits.csv")
    agg_df['NAICS_prefix'] = agg_df['NAICS'].astype(str).str[:2]
    naics_df['NAICS_prefix'] = naics_df['2022 NAICS US   Code'].astype(str)

    # Merge NAICS labels to data
    merged_df = pd.merge(agg_df, naics_df, on='NAICS_prefix', how='left')
    merged_df['NAICS_label'] = merged_df['2022 NAICS US Title']

    # Drop unnecessary NAICS columns
    merged_df = merged_df.drop(columns=['Unnamed: 3', 'Seq. No.', '2022 NAICS US   Code', '2022 NAICS US Title'])
    merged_df.to_csv(os.path.join(output_dir, "joined.csv"))

    # === Step 3: Compute and bin organizational size ===
    agg_df = merged_df
    excluded_jobs = ["CURRENT REPORTING YEAR TOTAL", "PRIOR REPORTING YEAR TOTAL"]

    # Exclude summary-level rows
    df_filtered = agg_df[~agg_df["JobCategory"].isin(excluded_jobs)].copy()

    # Group by file and sum row totals to compute size
    tmp_df = df_filtered[['filename', 'Row Total']].copy()
    tmp_df = tmp_df.groupby('filename')['Row Total'].sum().reset_index()
    tmp_df.rename(columns={'Row Total': 'Organizational Size'}, inplace=True)
    tmp_df.to_csv(os.path.join(output_dir, "org_size.csv"))

    # Join back to main DataFrame
    merged_df = pd.merge(df_filtered, tmp_df, on='filename', how='left')

    # Remove redundant column
    merged_df = merged_df.drop(columns=['Unnamed: 0'])

    # Bin organization sizes into quartiles
    merged_df['Organizational Size Binned'], bins = pd.qcut(
        merged_df['Organizational Size'],
        q=4,
        labels=['Small', 'Medium', 'Large', 'Very Large'],
        retbins=True
    )
    print(bins)

    # === Step 4: Derive a reliable ZIP code field ===
    merged_df['Real Zip Code'] = np.where(
        merged_df['State'] == "MA",
        merged_df['zip code'],
        merged_df['HQ zip code']
    )
    merged_df['Real Zip Code'] = merged_df['Real Zip Code'].astype(str)

    # Extract first 5 digits and pad with leading zeros
    merged_df['zip5'] = merged_df['Real Zip Code'].str.extract(r"^(\d{4,5})")[0].str.zfill(5)
    merged_df.to_csv(os.path.join(output_dir, "join.csv"))

    # === Step 5: Join with ZIP-to-county mapping ===
    zip_to_county_df = pd.read_csv("../public_data/geocorr2022_2510107037.csv")
    zip_to_county_df = zip_to_county_df.drop(columns=['county', 'ZIPName', 'pop20', 'afact'])
    zip_to_county_df['zcta'] = zip_to_county_df['zcta'].astype(str)
    zip_to_county_df = zip_to_county_df.iloc[3:, :]  # Skip header notes or extra rows

    # Merge geocorr ZIP-to-county data
    merged_df = merged_df.merge(zip_to_county_df, left_on='zip5', right_on='zcta', how='left')

    # Clean county name by removing state abbreviation
    merged_df['County Only'] = merged_df['CountyName'].str.replace(r"\s[A-Z]{2}$", "", regex=True)

    # === Step 6: Fill in missing counties using an auxiliary ZIP dataset ===
    additional_zip_df = pd.read_csv("../public_data/uscities.csv")
    additional_zip_df = additional_zip_df.drop(columns=[
        "city", "city_ascii", "state_id", "state_name", "county_fips", "lat", "lng", "population",
        "density", "source", "military", "incorporated", "timezone", "ranking", "id"
    ])
    additional_zip_df['zips'] = additional_zip_df['zips'].str.strip("[]").str.split()
    additional_zip_df = additional_zip_df.explode('zips')[['zips', 'county_name']].rename(
        columns={'zips': 'zip', 'county_name': 'county'}
    )

    # Merge ZIP-county data and determine final county name
    merged_df = merged_df.merge(additional_zip_df, left_on='zip5', right_on='zip', how='left')
    merged_df['County Name'] = np.where(
        merged_df['County Only'].notna() & (merged_df['County Only'] != ""),
        merged_df['County Only'],
        merged_df['county']
    )

    # Final cleanup of temporary columns
    merged_df = merged_df.drop(columns=[
        'county', 'zip', 'County Only', 'CountyName', 'zcta', 'Real Zip Code'
    ])
    merged_df.to_csv(os.path.join(output_dir, "join_with_county.csv"))
