import textwrap
import pandas as pd
import matplotlib.pyplot as plt
from eeo5_figure_config import BAR_EDGE_COLOR


def figure_38(jrg_df, output_dir, table_dir):
    fig38_df = (jrg_df.groupby('Job Category')['Count'].sum()
                .sort_values(ascending=False).reset_index())
    total = fig38_df['Count'].sum()

    fig, ax = plt.subplots(figsize=(18, 7))

    bars = ax.bar(fig38_df['Job Category'], fig38_df['Count'],
                  color='#003F5C', edgecolor=BAR_EDGE_COLOR, width=0.6)

    for bar, val in zip(bars, fig38_df['Count']):
        pct = f"{(val / total * 100).round(0).astype(int)}%"
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                pct, ha='center', va='bottom', fontsize=10)

    ax.set_xlabel('Job Category', fontweight='semibold', fontsize=14, labelpad=10)
    ax.set_ylabel('Employee Count', fontweight='semibold', fontsize=14, labelpad=10)
    ax.set_xticks(range(len(fig38_df)))
    ax.set_xticklabels([textwrap.fill(l, width=16, break_long_words=False) for l in fig38_df['Job Category']],
                       rotation=0, ha='center', fontsize=8)
    ax.tick_params(axis='y', labelsize=12)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{int(v/1000)}k' if v >= 1000 else f'{int(v)}'))
    ax.set_xlim(-0.5, len(fig38_df) - 0.5)

    plt.tight_layout()

    # Export Figure
    fig.savefig(f'{output_dir}/figure_38.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Create Table
    fig38_out = pd.DataFrame({
        'Job Category': fig38_df['Job Category'].values,
        'Percentage':   (fig38_df['Count'] / total * 100).round(0).astype(int).astype(str) + '%',
    })
    # Export Table
    fig38_out.to_csv(f'{table_dir}/figure_38_table.csv', index=False)
