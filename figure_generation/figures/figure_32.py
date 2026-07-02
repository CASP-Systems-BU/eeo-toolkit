import textwrap
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch
from eeo5_figure_config import BAR_EDGE_COLOR, RACE_ORDER_7, FEMALE_COLOR, MALE_COLOR


def figure_32(jrg_df, output_dir, table_dir):
    bar_df = (jrg_df.groupby(['Race', 'Gender'])['Count'].sum()
              .clip(lower=0).unstack().reindex(RACE_ORDER_7).fillna(0))
    bar_pct = bar_df.div(bar_df.sum(axis=1), axis=0) * 100

    races = list(bar_df.index)
    x     = np.arange(len(races))
    width = 0.35

    fig, ax = plt.subplots(figsize=(15, 6))

    for j, gender in enumerate(['Female', 'Male']):
        color  = FEMALE_COLOR if gender == 'Female' else MALE_COLOR
        counts = bar_df[gender].values
        pcts   = bar_pct[gender].values
        xpos   = x + (j - 0.5) * width

        ax.bar(xpos, counts, width=width, color=color, edgecolor=BAR_EDGE_COLOR)
        for xi, count, pct in zip(xpos, counts, pcts):
            ax.text(xi, count, f'{pct:.0f}%', fontsize=10, ha='center', va='bottom')

    legend_handles = [
        Patch(facecolor=FEMALE_COLOR, edgecolor=BAR_EDGE_COLOR, label='Female'),
        Patch(facecolor=MALE_COLOR,   edgecolor=BAR_EDGE_COLOR, label='Male'),
    ]
    ax.legend(handles=legend_handles, title='Sex', fontsize=12, title_fontsize=12)
    ax.set_xlabel('Race', fontweight='semibold', fontsize=14, labelpad=10)
    ax.set_ylabel('Employee Count', fontweight='semibold', fontsize=14, labelpad=10)
    ax.set_xticks(x)
    ax.set_xticklabels([textwrap.fill(r, width=20) for r in races], ha='center', fontsize=9)
    ax.tick_params(axis='y', labelsize=12)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{int(v/1000)}k' if v >= 1000 else f'{int(v)}'))

    plt.tight_layout()
    # Export Figure
    fig.savefig(f'{output_dir}/figure_32.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Create Table
    total    = bar_df.sum(axis=1)
    fig32_df = pd.DataFrame({
        'Race':              bar_df.index.values,
        'Female Percentage': (bar_df['Female'].values / total.values * 100).round(0).astype(int).astype(str) + '%',
        'Male Percentage':   (bar_df['Male'].values   / total.values * 100).round(0).astype(int).astype(str) + '%',
    })
    # Export Table
    fig32_df.to_csv(f'{table_dir}/figure_32_table.csv', index=False)
