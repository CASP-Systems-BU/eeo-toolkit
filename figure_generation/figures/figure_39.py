import textwrap
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch
from eeo5_figure_config import BAR_EDGE_COLOR, FEMALE_COLOR, MALE_COLOR


def figure_39(jrg_df, output_dir, table_dir):
    fig39_df = (jrg_df.groupby(['Job Category', 'Gender'])['Count'].sum()
                .clip(lower=0).unstack())
    fig39_pct   = fig39_df.div(fig39_df.sum(axis=1), axis=0) * 100
    count_order = fig39_df.sum(axis=1).sort_values(ascending=False).index
    fig39_df    = fig39_df.reindex(count_order)
    fig39_pct   = fig39_pct.reindex(count_order)

    cats  = list(fig39_df.index)
    x     = np.arange(len(cats))
    width = 0.35

    fig, ax = plt.subplots(figsize=(20, 7))

    for j, gender in enumerate(['Female', 'Male']):
        color  = FEMALE_COLOR if gender == 'Female' else MALE_COLOR
        counts = fig39_df[gender].values
        pcts   = fig39_pct[gender].values
        xpos   = x + (j - 0.5) * width

        ax.bar(xpos, counts, width=width, color=color, edgecolor='none')
        ax.bar(xpos, counts, width=width, color='none', edgecolor=BAR_EDGE_COLOR)
        for xi, count, pct in zip(xpos, counts, pcts):
            ax.text(xi, count + 30, f'{pct:.0f}%', ha='center', va='bottom', fontsize=9)

    legend_handles = [
        Patch(facecolor=FEMALE_COLOR, edgecolor=BAR_EDGE_COLOR, label='Female'),
        Patch(facecolor=MALE_COLOR,   edgecolor=BAR_EDGE_COLOR, label='Male'),
    ]
    ax.legend(handles=legend_handles, title='Sex', loc='upper right', fontsize=12, title_fontsize=12)
    ax.set_xlabel('Job Category', fontweight='semibold', fontsize=14, labelpad=10)
    ax.set_ylabel('Employee Count', fontweight='semibold', fontsize=14, labelpad=10)
    ax.set_xticks(x)
    ax.set_xticklabels([textwrap.fill(c, width=16, break_long_words=False) for c in cats],
                       ha='center', fontsize=8)
    ax.tick_params(axis='y', labelsize=12)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{int(v/1000)}k' if v >= 1000 else f'{int(v)}'))
    ax.set_xlim(-0.5, len(cats) - 0.5)

    plt.tight_layout()

    # Export Figure
    fig.savefig(f'{output_dir}/figure_39.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Create Table
    total     = fig39_df.sum(axis=1)
    fig39_out = pd.DataFrame({
        'Job Category':      fig39_df.index.values,
        'Female Percentage': (fig39_df['Female'].values / total.values * 100).round(0).astype(int).astype(str) + '%',
        'Male Percentage':   (fig39_df['Male'].values   / total.values * 100).round(0).astype(int).astype(str) + '%',
    })
    # Export Table
    fig39_out.to_csv(f'{table_dir}/figure_39_table.csv', index=False)
