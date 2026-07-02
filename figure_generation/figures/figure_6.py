from matplotlib.patches import Patch
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import textwrap
from eeo1_figure_config import BAR_EDGE_COLOR, FEMALE_COLOR, MALE_COLOR

def figure_6(df, output_dir, table_dir):
    job_gender = df.groupby(['JobCategory', 'Gender'])['Count'].sum().unstack()
    job_gender = job_gender.reindex(df.groupby('JobCategory')['Count'].sum().sort_values(ascending=False).index)
    job_totals = job_gender.sum(axis=1)

    x = np.arange(len(job_gender))
    width = 0.35

    fig, ax = plt.subplots(figsize=(14, 6))

    # Grouped bars by gender — colored fill with grey border, percentage label above each bar
    for j, gender in enumerate(['Female', 'Male']):
        color  = FEMALE_COLOR if gender == 'Female' else MALE_COLOR
        vals   = job_gender[gender].values
        xpos   = x + (j - 0.5) * width

        ax.bar(xpos, vals, width=width, color=color, edgecolor='none')
        ax.bar(xpos, vals, width=width, color='none', edgecolor=BAR_EDGE_COLOR)

        for xi, val, total in zip(xpos, vals, job_totals.values):
            pct = (val / total) * 100
            ax.text(xi, val + 500, f'{pct:.0f}%', fontsize=12, ha='center', va='bottom')

    # Legend and axis labels
    legend_handles = [
        Patch(facecolor=FEMALE_COLOR, edgecolor=BAR_EDGE_COLOR, label='Female'),
        Patch(facecolor=MALE_COLOR,   edgecolor=BAR_EDGE_COLOR, label='Male'),
    ]
    ax.legend(handles=legend_handles, title='Sex', title_fontsize=14, fontsize=14)

    ax.set_xlabel('Job Category', fontsize=14, fontweight='semibold', labelpad=10)
    ax.set_ylabel('Employee Count', fontsize=14, fontweight='semibold', labelpad=10)
    ax.set_xticks(x)
    ax.set_xticklabels([textwrap.fill(l, width=15, break_long_words=False) for l in job_gender.index], rotation=0, ha='center', fontsize=10)
    ax.tick_params(axis='y', labelsize=14)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{int(v/1000)}k' if v >= 1000 else f'{int(v)}'))
    ax.set_xlim(-0.5, 9.5)

    plt.tight_layout()

    # Export Figure
    fig.savefig(f'{output_dir}/figure_6.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Create Table
    fig6_df = pd.DataFrame({
        'Job Category':      job_gender.index,
        'Female Percentage': (job_gender['Female'] / job_totals * 100).round(0).astype(int).astype(str) + '%',
        'Male Percentage':   (job_gender['Male']   / job_totals * 100).round(0).astype(int).astype(str) + '%',
    })

    # Export Table
    fig6_df.to_csv(f'{table_dir}/figure_6_table.csv', index=False)
