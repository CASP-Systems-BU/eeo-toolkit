import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import textwrap
from eeo1_config import FEMALE_COLOR, MALE_COLOR, BAR_EDGE_COLOR, RACE_ORDER_5

def figure_3(df, output_dir, table_dir):

    bar_df  = df[df['Race'].isin(RACE_ORDER_5)].groupby(['Race', 'Gender'])['Count'].sum().unstack()
    bar_pct = bar_df.div(bar_df.sum(axis=1), axis=0) * 100
    bar_df  = bar_df.reindex(RACE_ORDER_5)
    bar_pct = bar_pct.reindex(RACE_ORDER_5)

    races  = list(bar_df.index)
    x      = np.arange(len(races))
    width  = 0.35

    fig, ax = plt.subplots(figsize=(13, 6))

    # Grouped bars by gender — colored fill with grey border, percentage label above each bar
    for j, gender in enumerate(["Female", "Male"]):
        color  = FEMALE_COLOR if gender == "Female" else MALE_COLOR
        counts = bar_df[gender].values
        pcts   = bar_pct[gender].values
        xpos   = x + (j - 0.5) * width

        ax.bar(xpos, counts, width=width, color=color, edgecolor="none")
        ax.bar(xpos, counts, width=width, color="none", edgecolor=BAR_EDGE_COLOR)
        for xi, count, pct in zip(xpos, counts, pcts):
            ax.text(xi, count + 500, f"{pct:.0f}%", fontsize=12, ha="center", va="bottom")

    # Legend and axis labels
    legend_handles = [
        Patch(facecolor=FEMALE_COLOR, label="Female"),
        Patch(facecolor=MALE_COLOR,   label="Male"),
    ]
    ax.legend(handles=legend_handles, title_fontsize=14, fontsize=14, title="Sex")

    ax.set_xlabel("Race", fontsize=14, fontweight="semibold", labelpad=10)
    ax.set_ylabel("Employee Count", fontsize=14, fontweight="semibold", labelpad=10)
    ax.set_xticks(x)
    ax.set_xticklabels([textwrap.fill(r, width=30) for r in races], ha="center", fontsize=10)
    ax.tick_params(axis='y', labelsize=14)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{int(v/1000)}k" if v >= 1000 else f"{int(v)}"))

    plt.tight_layout()

    # Export Figure
    fig.savefig(f'{output_dir}/figure_3.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Create Table
    fig3_all = (df.groupby(['Race', 'Gender'])['Count'].sum().unstack()
            .reindex(RACE_ORDER_5))

    total = fig3_all.sum(axis=1)
    fig3_df = pd.DataFrame({
        'Race':              fig3_all.index,
        'Female Percentage': (fig3_all['Female'] / total * 100).round(0).astype(int).astype(str) + '%',
        'Male Percentage':   (fig3_all['Male']   / total * 100).round(0).astype(int).astype(str) + '%',
    }).reset_index(drop=True)

    # Export Table
    fig3_df.to_csv(f'{table_dir}/figure_3_table.csv', index=False)
