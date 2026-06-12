import textwrap
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
from eeo4_figure_config import BAR_EDGE_COLOR, RACE_ORDER_5, FEMALE_COLOR, MALE_COLOR

def figure_16(jrg_df, output_dir, table_dir):
    bar_df  = (jrg_df[jrg_df['Race'].isin(RACE_ORDER_5)]
           .groupby(['Race', 'Gender'])['Count'].sum()
           .clip(lower=0)
           .unstack()
           .reindex(RACE_ORDER_5))
    bar_pct = bar_df.div(bar_df.sum(axis=1), axis=0) * 100

    races = list(bar_df.index)
    x     = np.arange(len(races))
    width = 0.35

    fig, ax = plt.subplots(figsize=(13, 6))

    # Grouped bars by gender — colored fill with grey border, percentage label above each bar
    for j, gender in enumerate(['Female', 'Male']):
        color  = FEMALE_COLOR if gender == 'Female' else MALE_COLOR
        counts = bar_df[gender].values
        pcts   = bar_pct[gender].values
        xpos   = x + (j - 0.5) * width

        ax.bar(xpos, counts, width=width, color=color, edgecolor=BAR_EDGE_COLOR)
        for xi, count, pct in zip(xpos, counts, pcts):
            ax.text(xi, count, f'{pct:.0f}%', fontsize=12, ha='center', va='bottom')

    # Legend and axis labels
    legend_handles = [
        Patch(facecolor=FEMALE_COLOR, edgecolor=BAR_EDGE_COLOR, label='Female'),
        Patch(facecolor=MALE_COLOR,   edgecolor=BAR_EDGE_COLOR, label='Male'),
    ]
    ax.legend(handles=legend_handles, title='Sex', fontsize=14, title_fontsize=14)

    ax.set_xlabel('Race', fontweight='semibold', fontsize=14, labelpad=10)
    ax.set_ylabel('Employee Count', fontweight='semibold', fontsize=14, labelpad=10)
    ax.set_xticks(x)
    ax.set_xticklabels([textwrap.fill(r, width=30) for r in races], ha='center', fontsize=10)
    ax.tick_params(axis='y', labelsize=14)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{int(v/1000)}k' if v >= 1000 else f'{int(v)}'))

    plt.tight_layout()

    # Export Figure
    fig.savefig(f'{output_dir}/figure_16.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Create Table
    fig16_all = (jrg_df.groupby(['Race', 'Gender'])['Count'].sum()
                   .clip(lower=0).unstack().reindex(RACE_ORDER_5))
    total = fig16_all.sum(axis=1)
    fig16_df = pd.DataFrame({
        'Race':              fig16_all.index.values,
        'Female Percentage': (fig16_all['Female'].values / total.values * 100).round(0).astype(int).astype(str) + '%',
        'Male Percentage':   (fig16_all['Male'].values   / total.values * 100).round(0).astype(int).astype(str) + '%',
    })

    # Export Table
    fig16_df.to_csv(f'{table_dir}/figure_16_table.csv', index=False)
