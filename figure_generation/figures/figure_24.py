import textwrap
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch
from eeo4_figure_config import BAR_EDGE_COLOR, FEMALE_COLOR, MALE_COLOR

def figure_24(wfrg_df, output_dir, table_dir):

    wfrg_df = wfrg_df[wfrg_df['Work_Type'] != 'NEW HIRES']

    fig24_df = (wfrg_df.groupby(['Work_Type', 'Gender'])['Count'].sum()
         .clip(lower=0)
         .unstack()[['Female', 'Male']])
    fig24_pct = fig24_df.div(fig24_df.sum(axis=1), axis=0) * 100

    wtypes = list(fig24_df.index)
    x      = np.arange(len(wtypes))
    width  = 0.4

    fig, ax = plt.subplots(figsize=(8, 6))

    # Grouped bars by gender — colored fill with grey border, percentage label above each bar
    for j, gender in enumerate(['Female', 'Male']):
        color  = FEMALE_COLOR if gender == 'Female' else MALE_COLOR
        counts = fig24_df[gender].values
        pcts   = fig24_pct[gender].values
        xpos   = x + (j - 0.5) * width

        ax.bar(xpos, counts, width=width, color=color, edgecolor='none')
        ax.bar(xpos, counts, width=width, color='none', edgecolor=BAR_EDGE_COLOR)
        for xi, count, pct in zip(xpos, counts, pcts):
            ax.text(xi, count, f'{pct:.0f}%', ha='center', va='bottom', fontsize=12)

    # Legend and axis labels
    legend_handles = [
        Patch(facecolor=FEMALE_COLOR, edgecolor=BAR_EDGE_COLOR, label='Female'),
        Patch(facecolor=MALE_COLOR,   edgecolor=BAR_EDGE_COLOR, label='Male'),
    ]
    ax.legend(handles=legend_handles, title='Sex', fontsize=14, title_fontsize=14)

    ax.set_xlabel('Work Type', fontweight='semibold', fontsize=14, labelpad=10)
    ax.set_ylabel('Employee Count', fontweight='semibold', fontsize=14, labelpad=10)
    ax.set_xticks(x)
    ax.set_xticklabels([textwrap.fill(w.title(), width=20) for w in wtypes], ha='center', fontsize=12)
    ax.tick_params(axis='y', labelsize=14)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{int(v/1000)}k' if v >= 1000 else f'{int(v)}'))

    plt.tight_layout()

    # Export Figure
    fig.savefig(f'{output_dir}/figure_24.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Create Table
    total = fig24_df.sum(axis=1)
    fig24_df = pd.DataFrame({
        'Work Type':         fig24_df.index.values,
        'Female Percentage': (fig24_df['Female'].values / total.values * 100).round(0).astype(int).astype(str) + '%',
        'Male Percentage':   (fig24_df['Male'].values   / total.values * 100).round(0).astype(int).astype(str) + '%',
    })

    # Export Table
    fig24_df.to_csv(f'{table_dir}/figure_24_table.csv', index=False)
