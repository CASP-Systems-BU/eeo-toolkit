import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import colormaps
import math


df = pd.read_csv("../files/batch_1/csv_output/GENDER_AND_RACE_CURRENT.csv")
numeric_cols = df.select_dtypes(include='number').columns.tolist()
# numeric_cols = numeric_cols[1:]
cmap = colormaps.get_cmap("tab10")
colors = {col: cmap(i / len(numeric_cols)) for i, col in enumerate(numeric_cols)}
num_rows = len(df)

cols = 4
rows = math.ceil(num_rows / cols)
fig, axes = plt.subplots(rows, cols, figsize=(cols * 6, rows * 6))
if num_rows == 1:
    axes = [axes]
axes = axes.flatten()
for idx, row in df.iterrows():
    sizes = row[numeric_cols].values.astype(float)
    title = row[df.columns.tolist()[0]]
    ax = axes[idx]
    wedges, _, _ = ax.pie(
        sizes,
        labels=None,
        autopct='%1.1f%%',
        colors=[colors[col] for col in numeric_cols],
        startangle=90,
        textprops=dict(color="black", fontsize=8))
    ax.set_title(title)
    ax.axis('equal')
for j in range(idx + 1, len(axes)):
    axes[j].axis('off')
handles = [plt.Line2D([0], [0], marker='o', color='w',
                      markerfacecolor=colors[r], markersize=10)
           for r in numeric_cols]
labels = numeric_cols
fig.legend(handles, labels, title="Gender", loc='center right', bbox_to_anchor=(1.1, 0.5))
fig.suptitle("Gender Distribution by Race", fontsize=30, y=1.02)
plt.tight_layout(rect=[0, 0, 0.9, 1])
plt.savefig("gender_and_race.png", dpi=300, bbox_inches='tight')
plt.close()
