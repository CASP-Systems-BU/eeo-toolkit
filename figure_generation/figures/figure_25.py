import textwrap
import pandas as pd
import matplotlib.pyplot as plt
from eeo4_config import BAR_EDGE_COLOR

def figure_25(jrg_df, output_dir, table_dir):

    fig25_df = (jrg_df.groupby('Job Category')['Count'].sum()
         .sort_values(ascending=False)
         .reset_index())
    total = fig25_df['Count'].sum()

    fig, ax = plt.subplots(figsize=(16, 7))

    # Job category bars — single color fill with grey border, percentage label above each bar
    bars = ax.bar(fig25_df['Job Category'], fig25_df['Count'],
                color='#003F5C', edgecolor=BAR_EDGE_COLOR, width=0.6)

    for bar, val in zip(bars, fig25_df['Count']):
        pct = f"{(val / total * 100).round(0).astype(int)}%"
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                pct, ha='center', va='bottom', fontsize=12)

    # Axis labels and tick formatting
    ax.set_xlabel('Job Category', fontweight='semibold', labelpad=10, fontsize=14)
    ax.set_ylabel('Employee Count', fontweight='semibold', labelpad=10, fontsize=14)
    ax.set_xticks(range(len(fig25_df)))
    ax.set_xticklabels([textwrap.fill(l, width=20, break_long_words=False) for l in fig25_df['Job Category']],
                    rotation=0, ha='center', fontsize=12)
    ax.tick_params(axis='y', labelsize=14)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{int(v/1000)}k' if v >= 1000 else f'{int(v)}'))
    ax.set_xlim(-0.5, len(fig25_df) - 0.5)

    plt.tight_layout()

    # Export Figure
    fig.savefig(f'{output_dir}/figure_25.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Create Table
    fig25_df = pd.DataFrame({
        'Job Category': fig25_df['Job Category'].values,
        'Percentage':   (fig25_df['Count'] / total * 100).round(0).astype(int).astype(str) + '%',
    })

    # Export Table
    fig25_df.to_csv(f'{table_dir}/figure_25_table.csv', index=False)
