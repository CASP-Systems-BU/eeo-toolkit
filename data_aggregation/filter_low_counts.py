import os
import pandas as pd

input_folder = "/home/node0/Documents/csv_output/eeo1_contingency_tables/three_way"
output_folder = "/home/node0/Documents/csv_output/eeo1_contingency_tables/three_way"
threshold = 50
for filename in os.listdir(input_folder):
    if filename.endswith(".csv"):
        filepath = os.path.join(input_folder, filename)

        df = pd.read_csv(filepath)


        df['Count'] = df['Count'].apply(lambda x: 0 if x < threshold else x)
        output_path = os.path.join(output_folder, filename)
        df.to_csv(output_path, index=False)

        print(f"Processed: {filename}")