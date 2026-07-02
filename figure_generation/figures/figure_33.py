import textwrap
import pandas as pd
import matplotlib.pyplot as plt
from eeo5_figure_config import BAR_EDGE_COLOR, AGENT_TYPE_ORDER


def figure_33(twg_df, output_dir, table_dir):
    fig33_df = (twg_df.groupby('Type of Agent')['Count'].sum()
                .reindex(AGENT_TYPE_ORDER).reset_index())
    total = fig33_df['Count'].sum()

    fig, ax = plt.subplots(figsize=(8, 5))

    bars = ax.bar(fig33_df['Type of Agent'], fig33_df['Count'],
                  color='#003F5C', edgecolor=BAR_EDGE_COLOR, width=0.4)

    for bar, val in zip(bars, fig33_df['Count']):
        pct = f"{(val / total * 100).round(0).astype(int)}%"
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                pct, ha='center', va='bottom', fontsize=12)

    ax.set_xlabel('Agent Type', fontweight='semibold', fontsize=14, labelpad=10)
    ax.set_ylabel('Employee Count', fontweight='semibold', fontsize=14, labelpad=10)
    ax.set_xticks(range(len(fig33_df)))
    ax.set_xticklabels([textwrap.fill(l, width=20) for l in fig33_df['Type of Agent']],
                       ha='center', fontsize=12)
    ax.tick_params(axis='y', labelsize=12)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{int(v/1000)}k' if v >= 1000 else f'{int(v)}'))

    plt.tight_layout()

    # Export Figure
    fig.savefig(f'{output_dir}/figure_33.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Create Table
    fig33_df = pd.DataFrame({
        'Agent Type': fig33_df['Type of Agent'].values,
        'Percentage': (fig33_df['Count'] / total * 100).round(0).astype(int).astype(str) + '%',
    })
    # Export Table
    fig33_df.to_csv(f'{table_dir}/figure_33_table.csv', index=False)
