import pandas as pd
df1 = pd.read_csv("/home/node0/Documents/csv_output/aggregation.csv")
df2 = pd.read_csv("../public_data/naics_2digits.csv")
df1['NAICS_prefix'] = df1['NAICS'].astype(str).str[:2]
df2['NAICS_prefix'] = df2['2022 NAICS US   Code'].astype(str)

merged_df = pd.merge(df1, df2, on='NAICS_prefix', how='left')
merged_df['NAICS_label'] = merged_df['2022 NAICS US Title']
merged_df = merged_df.drop(columns=['Unnamed: 3', 'Seq. No.', '2022 NAICS US   Code', '2022 NAICS US Title'])
print(merged_df.head())
merged_df.to_csv("/home/node0/Documents/csv_output/joined.csv")