import textwrap
import pandas as pd
import matplotlib.pyplot as plt
from eeo4_config import BAR_EDGE_COLOR

def figure_17(wfrg_df, output_dir, table_dir):

    wfrg_df = wfrg_df[wfrg_df['Work_Type'] != 'NEW HIRES']

    fig17_df = (wfrg_df.groupby('Government_Function')['Count'].sum()
           .sort_index()
           .reset_index())

    fig, ax = plt.subplots(figsize=(16, 7))

    # Government function bars — single color fill with grey border, percentage label above each bar
    total = fig17_df['Count'].sum()
    bars = ax.bar(fig17_df['Government_Function'], fig17_df['Count'],
                color='#003F5C', edgecolor=BAR_EDGE_COLOR, width=0.6)

    for bar, val in zip(bars, fig17_df['Count']):
        pct = f"{(val / total * 100).round(0).astype(int)}%"
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
            pct, ha='center', va='bottom', fontsize=12)

    # Axis labels and tick formatting
    ax.set_xlabel('Government Function', fontweight='semibold', fontsize=14, labelpad=10)
    ax.set_ylabel('Employee Count', fontweight='semibold', fontsize=14, labelpad=10)
    ax.set_xticks(range(len(fig17_df)))
    ax.set_xticklabels([textwrap.fill(l, width=20, break_long_words=False) for l in fig17_df['Government_Function']],
                    rotation=70, ha='center', fontsize=10)
    ax.tick_params(axis='y', labelsize=14)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{int(v/1000)}k' if v >= 1000 else f'{int(v)}'))
    ax.set_xlim(-0.5, len(fig17_df) - 0.5)


    plt.tight_layout()

    # Export Figure
    fig.savefig(f'{output_dir}/figure_17.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Create Table
    fig17_df = pd.DataFrame({
        'Government Function': fig17_df['Government_Function'].values,
        'Percentage':          (fig17_df['Count'] / total * 100).round(0).astype(int).astype(str) + '%',
    })

    # Export Table
    fig17_df.to_csv(f'{table_dir}/figure_17_table.csv', index=False)
