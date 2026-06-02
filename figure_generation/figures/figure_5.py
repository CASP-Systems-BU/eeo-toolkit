import pandas as pd
import matplotlib.pyplot as plt
import textwrap
from eeo1_config import BAR_EDGE_COLOR

def figure_5(df, output_dir, table_dir):
    job_totals = df.groupby('JobCategory')['Count'].sum().sort_values(ascending=False)
    total = job_totals.sum()

    fig, ax = plt.subplots(figsize=(12, 6))

    # Job category bars — single color fill with grey border, percentage label above each bar
    bars = ax.bar(job_totals.index, job_totals.values, color='#003F5C', edgecolor=BAR_EDGE_COLOR, width=0.6)
    for bar, val in zip(bars, job_totals.values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 500,
                f'{val/total*100:.0f}%', fontsize=12, ha='center', va='bottom')

    # Axis labels and tick formatting
    ax.set_xlim(-0.7, 9.7)
    ax.set_xlabel('Job Category', fontsize=14, fontweight='semibold', labelpad=10)
    ax.set_ylabel('Employee Count', fontsize=14, fontweight='semibold', labelpad=10)
    ax.set_xticks(range(len(job_totals)))
    ax.set_xticklabels([textwrap.fill(l, width=12, break_long_words=False) for l in job_totals.index], rotation=0, ha='center', fontsize=10)
    ax.tick_params(axis='y', labelsize=14)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{int(v/1000)}k' if v >= 1000 else f'{int(v)}'))

    plt.tight_layout()

    # Export Figure
    fig.savefig(f'{output_dir}/figure_5.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Create Table
    fig5_df = pd.DataFrame({
        'Job Category': job_totals.index,
        'Percentage':   (job_totals / total * 100).round(0).astype(int).astype(str) + '%',
    })

    # Export Table
    fig5_df.to_csv(f'{table_dir}/figure_5_table.csv', index=False)
