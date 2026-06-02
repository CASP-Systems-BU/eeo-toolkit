import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import textwrap
from eeo1_config import RACE_COLORS, BAR_EDGE_COLOR, RACE_ORDER_5

def figure_4(df, output_dir, table_dir):
    stack_df   = df.groupby(['Gender', 'Race'])['Count'].sum().unstack().reindex(['Female', 'Male'])[RACE_ORDER_5]
    gender_totals = stack_df.sum(axis=1)

    fig, ax = plt.subplots(figsize=(16, 7))

    bottoms = np.zeros(2)
    x = np.arange(2)

    # Stacked race bars — each segment colored by race with a labeled tick line to the right
    for race in RACE_ORDER_5[::-1]:
        vals  = stack_df[race].values
        color = RACE_COLORS[race]

        ax.bar(x, vals, bottom=bottoms, color=color, edgecolor='none', width=0.5)
        ax.bar(x, vals, bottom=bottoms, color='none', edgecolor=BAR_EDGE_COLOR, width=0.5)

        for xi, val, bottom, total in zip(x, vals, bottoms, gender_totals.values):
            pct = val / total * 100
            mid_y = bottom + val / 2
            bar_edge = xi + 0.25
            tick_end = xi + 0.275
            text_x   = xi + 0.295
            ax.plot([bar_edge, tick_end], [mid_y, mid_y],
                    color='black', linewidth=0.8, solid_capstyle='butt', clip_on=False)
            ax.text(text_x, mid_y, textwrap.fill(race, width=30) + f' ({pct:.0f}%)',
                    ha='left', va='center', fontsize=12, color='black', clip_on=False)

        bottoms += vals

    # Axis labels and tick formatting
    ax.set_xlim(-0.3, 1.7)
    ax.set_xticks(x)
    ax.set_xticklabels(['Female', 'Male'], fontsize=14)
    ax.set_xlabel('Sex', fontsize=14, fontweight='semibold', labelpad=10)
    ax.set_ylabel('Employee Count', fontsize=14, fontweight='semibold', labelpad=10)
    ax.tick_params(axis='y', labelsize=14)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{int(v/1000)}k' if v >= 1000 else f'{int(v)}'))

    plt.tight_layout()

    # Export Figure
    fig.savefig(f'{output_dir}/figure_4.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Create Table
    fig4_all = (df.groupby(['Race', 'Gender'])['Count'].sum().unstack()
            .reindex(RACE_ORDER_5))

    female_total = fig4_all['Female'].sum()
    male_total   = fig4_all['Male'].sum()

    race_rows = pd.DataFrame({
        'Race':              fig4_all.index,
        'Female Percentage': (fig4_all['Female'] / female_total * 100).round(0).astype(int).astype(str) + '%',
        'Male Percentage':   (fig4_all['Male']   / male_total   * 100).round(0).astype(int).astype(str) + '%',
    })
    total_row = pd.DataFrame([{'Race': 'Total', 'Female Percentage': '100%', 'Male Percentage': '100%'}])
    fig4_df = pd.concat([race_rows, total_row], ignore_index=True)

    # Export Table
    fig4_df.to_csv(f'{table_dir}/figure_4_table.csv', index=False)
