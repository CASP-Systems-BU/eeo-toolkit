"""
This script generates bar chart visualizations for all three-way (and fallback two-way)
contingency tables in a given directory. For three-way tables:
- One subplot is created per value of the first column.
- Each subplot is a bar chart showing the relationship between the second and third columns.

For two-way tables:
- A single stacked bar chart is generated.

Each chart is saved as a PNG file named after the corresponding contingency dimensions.
"""

import os.path
import pandas as pd
import matplotlib.pyplot as plt
from ocr.utilities.dir_helper import get_files_in_directory

# Path to the folder containing contingency table CSVs
csv_path = "/home/node0/Documents/csv_output/eeo1_contingency_tables/three_way"
csv_files = get_files_in_directory(csv_path, extension="csv")

for csv_file in csv_files:
    test_df = pd.read_csv(os.path.join(csv_path, csv_file))
    column_name_list = list(test_df.columns)

    if len(column_name_list) > 3:
        # Handle 3-way tables
        first_column_values = test_df[column_name_list[0]].unique()
        n = len(first_column_values)
        cols = 3  # Number of subplot columns
        rows = -(-n // cols)  # Ceiling division for subplot rows
        fig, axes = plt.subplots(rows, cols, figsize=(cols * 10, rows * 10), squeeze=False)

        for i, value in enumerate(first_column_values):
            ax = axes[i // cols][i % cols]
            sub = test_df[test_df[column_name_list[0]] == value]
            pivot = sub.pivot(index=column_name_list[1], columns=column_name_list[2],
                              values=column_name_list[3]).fillna(0)
            pivot.plot(kind='bar', ax=ax)

            ax.set_title(value)
            ax.set_ylabel(column_name_list[3])
            ax.set_xlabel(column_name_list[1])
            ax.tick_params(axis='x', rotation=45)

        # Remove empty subplots
        for j in range(i + 1, rows * cols):
            fig.delaxes(axes[j // cols][j % cols])

        plt.tight_layout()
        title = f"{column_name_list[1]} and {column_name_list[2]} Distribution by {column_name_list[0]}"
        plt.suptitle(title, fontsize=16, y=1.02)
        plt.savefig(os.path.join(csv_path, title.replace(' ', '_') + ".png"))

    else:
        # Handle 2-way tables (fallback)
        fig, ax = plt.subplots(figsize=(100, 100), dpi=600, constrained_layout=True)
        pivot = test_df.pivot(index=column_name_list[0],
                              columns=column_name_list[1],
                              values=column_name_list[2]).fillna(0)

        pivot.plot(kind='bar', stacked=True, ax=ax)
        title = f"{column_name_list[1]} Distribution by {column_name_list[0]}"
        ax.set_title(title)
        ax.set_xlabel(column_name_list[0])
        ax.set_ylabel(column_name_list[2])
        plt.xticks(rotation=45)
        plt.subplots_adjust(bottom=0.3)
        plt.savefig(os.path.join(csv_path, title.replace(' ', '_') + ".png"))

    print(f"Figure {title} saved.")

# Close any remaining figures
plt.close()
