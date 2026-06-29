import textwrap
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch
from eeo5_figure_config import BAR_EDGE_COLOR, FEMALE_COLOR, MALE_COLOR, WORK_TYPE_ORDER


def figure_37(wcrg_df, output_dir, table_dir):
    fig37_df = (wcrg_df.groupby(['Work Type', 'Gender'])['Count'].sum()
                .clip(lower=0).unstack()[['Female', 'Male']].reindex(WORK_TYPE_ORDER))
    fig37_pct = fig37_df.div(fig37_df.sum(axis=1), axis=0) * 100

    wtypes = list(fig37_df.index)
    x      = np.arange(len(wtypes))
    width  = 0.4

    fig, ax = plt.subplots(figsize=(8, 6))

    for j, gender in enumerate(['Female', 'Male']):
        color  = FEMALE_COLOR if gender == 'Female' else MALE_COLOR
        counts = fig37_df[gender].values
        pcts   = fig37_pct[gender].values
        xpos   = x + (j - 0.5) * width

        ax.bar(xpos, counts, width=width, color=color, edgecolor='none')
        ax.bar(xpos, counts, width=width, color='none', edgecolor=BAR_EDGE_COLOR)
        for xi, count, pct in zip(xpos, counts, pcts):
            ax.text(xi, count, f'{pct:.0f}%', ha='center', va='bottom', fontsize=12)

    legend_handles = [
        Patch(facecolor=FEMALE_COLOR, edgecolor=BAR_EDGE_COLOR, label='Female'),
        Patch(facecolor=MALE_COLOR,   edgecolor=BAR_EDGE_COLOR, label='Male'),
    ]
    ax.legend(handles=legend_handles, title='Sex', fontsize=12, title_fontsize=12)
    ax.set_xlabel('Work Type', fontweight='semibold', fontsize=14, labelpad=10)
    ax.set_ylabel('Employee Count', fontweight='semibold', fontsize=14, labelpad=10)
    ax.set_xticks(x)
    ax.set_xticklabels([textwrap.fill(w.title(), width=20) for w in wtypes], ha='center', fontsize=12)
    ax.tick_params(axis='y', labelsize=12)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{int(v/1000)}k' if v >= 1000 else f'{int(v)}'))

    plt.tight_layout()

    # Export Figure
    fig.savefig(f'{output_dir}/figure_37.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Create Table
    total    = fig37_df.sum(axis=1)
    fig37_out = pd.DataFrame({
        'Work Type':         fig37_df.index.values,
        'Female Percentage': (fig37_df['Female'].values / total.values * 100).round(0).astype(int).astype(str) + '%',
        'Male Percentage':   (fig37_df['Male'].values   / total.values * 100).round(0).astype(int).astype(str) + '%',
    })
    # Export Table
    fig37_out.to_csv(f'{table_dir}/figure_37_table.csv', index=False)
