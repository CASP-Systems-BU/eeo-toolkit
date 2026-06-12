import textwrap
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch
from eeo4_figure_config import BAR_EDGE_COLOR, FEMALE_COLOR, MALE_COLOR

def figure_26(jrg_df, output_dir, table_dir):

    fig26_df = (jrg_df.groupby(['Job Category', 'Gender'])['Count'].sum()
         .clip(lower=0)
         .unstack())
    fig26_pct = fig26_df.div(fig26_df.sum(axis=1), axis=0) * 100
    count_order = fig26_df.sum(axis=1).sort_values(ascending=False).index
    fig26_df  = fig26_df.reindex(count_order)
    fig26_pct = fig26_pct.reindex(count_order)

    cats  = list(fig26_df.index)
    x     = np.arange(len(cats))
    width = 0.35

    fig, ax = plt.subplots(figsize=(16, 7))

    # Grouped bars by gender — colored fill with grey border, percentage label above each bar
    for j, gender in enumerate(['Female', 'Male']):
        color  = FEMALE_COLOR if gender == 'Female' else MALE_COLOR
        counts = fig26_df[gender].values
        pcts   = fig26_pct[gender].values
        xpos   = x + (j - 0.5) * width

        ax.bar(xpos, counts, width=width, color=color, edgecolor='none')
        ax.bar(xpos, counts, width=width, color='none', edgecolor=BAR_EDGE_COLOR)
        for xi, count, pct in zip(xpos, counts, pcts):
            ax.text(xi, count + 30, f'{pct:.0f}%', ha='center', va='bottom', fontsize=12)

    # Legend and axis labels
    legend_handles = [
        Patch(facecolor=FEMALE_COLOR, edgecolor=BAR_EDGE_COLOR, label='Female'),
        Patch(facecolor=MALE_COLOR,   edgecolor=BAR_EDGE_COLOR, label='Male'),
    ]
    ax.legend(handles=legend_handles, title='Sex', loc='upper right', fontsize=14, title_fontsize=14)

    ax.set_xlabel('Job Category', fontweight='semibold', fontsize=14, labelpad=10)
    ax.set_ylabel('Employee Count', fontweight='semibold', fontsize=14, labelpad=10)
    ax.set_xticks(x)
    ax.set_xticklabels([textwrap.fill(c, width=20, break_long_words=False) for c in cats], ha='center', fontsize=12)
    ax.tick_params(axis='y', labelsize=14)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v/1000:.1f}k'))
    ax.set_xlim(-0.5, len(cats) - 0.5)

    plt.tight_layout()

    # Export Figure
    fig.savefig(f'{output_dir}/figure_26.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Create Table
    total = fig26_df.sum(axis=1)
    fig26_df = pd.DataFrame({
        'Job Category':      fig26_df.index.values,
        'Female Percentage': (fig26_df['Female'].values / total.values * 100).round(0).astype(int).astype(str) + '%',
        'Male Percentage':   (fig26_df['Male'].values   / total.values * 100).round(0).astype(int).astype(str) + '%',
    })

    # Export Table
    fig26_df.to_csv(f'{table_dir}/figure_26_table.csv', index=False)
