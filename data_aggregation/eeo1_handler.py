import os
import pandas as pd
import numpy as np

from aggregation import (
    json_to_df
)

from custom_types import (
    YearType
)

if __name__ == "__main__":
    # generate aggregation
    input_dir = "/home/node0/Documents/eeo1_json"
    output_dir = f"{input_dir}/../csv_output"
    agg_df = json_to_df(input_dir)
    agg_df['zip code'] = agg_df['zip code'].astype(str)
    agg_df['HQ zip code'] = agg_df['HQ zip code'].astype(str)
    agg_df.to_csv(os.path.join(output_dir, "aggregation.csv"))
    agg_df = pd.read_csv(os.path.join(output_dir, "aggregation.csv"))
    naics_df = pd.read_csv("../public_data/naics_2digits.csv")
    agg_df['NAICS_prefix'] = agg_df['NAICS'].astype(str).str[:2]
    naics_df['NAICS_prefix'] = naics_df['2022 NAICS US   Code'].astype(str)

    merged_df = pd.merge(agg_df, naics_df, on='NAICS_prefix', how='left')
    merged_df['NAICS_label'] = merged_df['2022 NAICS US Title']
    merged_df = merged_df.drop(columns=['Unnamed: 3', 'Seq. No.', '2022 NAICS US   Code', '2022 NAICS US Title'])
    merged_df.to_csv(os.path.join(output_dir, "joined.csv"))
    agg_df = merged_df
    excluded_jobs = ["CURRENT REPORTING YEAR TOTAL", "PRIOR REPORTING YEAR TOTAL"]
    df_filtered = agg_df[
        ~agg_df["JobCategory"].isin(excluded_jobs)
    ].copy()
    tmp_df = df_filtered[['filename', 'Row Total']].copy()
    tmp_df = tmp_df.groupby('filename')['Row Total'].sum().reset_index()
    tmp_df.rename(columns={'Row Total': 'Organizational Size'}, inplace=True)
    tmp_df.to_csv(os.path.join(output_dir, "org_size.csv"))
    merged_df = pd.merge(df_filtered, tmp_df, on='filename', how='left')
    merged_df = merged_df.drop(columns=['Unnamed: 0'])
    merged_df['Organizational Size Binned'], bins = pd.qcut(merged_df['Organizational Size'],
                                                      q=4, labels=['Small', 'Medium', 'Large', 'Very Large'], retbins=True)
    print(bins)
    merged_df['Real Zip Code'] = np.where(merged_df['State'] == "MA", merged_df['zip code'], merged_df['HQ zip code'])
    merged_df['Real Zip Code'] = merged_df['Real Zip Code'].astype(str)
    merged_df['zip5'] = merged_df['Real Zip Code'].str.extract(r"^(\d{4,5})")[0].str.zfill(5)
    merged_df.to_csv(os.path.join(output_dir, "join.csv"))

    zip_to_county_df = pd.read_csv("../public_data/geocorr2022_2510107037.csv")
    zip_to_county_df = zip_to_county_df.drop(columns=['county', 'ZIPName', 'pop20', 'afact'])
    zip_to_county_df['zcta'] = zip_to_county_df['zcta'].astype(str)
    zip_to_county_df = zip_to_county_df.iloc[3:,:]
    merged_df = merged_df.merge(zip_to_county_df, left_on='zip5', right_on='zcta', how='left')
    merged_df['County Only'] = merged_df['CountyName'].str.replace(r"\s[A-Z]{2}$", "", regex=True)
    additional_zip_df = pd.read_csv("../public_data/uscities.csv")
    additional_zip_df = additional_zip_df.drop(columns=["city", "city_ascii", "state_id",
                                                      "state_name", "county_fips", "lat", "lng", "population",
                                                      "density", "source", "military", "incorporated", "timezone",
                                                      "ranking", "id"])
    additional_zip_df['zips'] = additional_zip_df['zips'].str.strip("[]").str.split()
    additional_zip_df = additional_zip_df.explode('zips')[['zips', 'county_name']].rename(
        columns={'zips': 'zip', 'county_name': 'county'})
    merged_df = merged_df.merge(additional_zip_df, left_on='zip5', right_on='zip', how='left')
    merged_df['County Name'] = np.where(merged_df['County Only'].notna() & (merged_df['County Only'] != ""), merged_df['County Only'], merged_df['county'])
    merged_df = merged_df.drop(columns=['county', 'zip', 'County Only', 'CountyName', 'zcta', 'Real Zip Code'])
    merged_df.to_csv(os.path.join(output_dir, "join_with_county.csv"))
