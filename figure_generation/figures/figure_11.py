import textwrap
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from eeo1_config import BAR_EDGE_COLOR

def figure_11(df, output_dir, table_dir):
    fig_11_df = df.groupby(['NAICS_label']).agg({'Count': 'sum'}).sort_values('Count', ascending=False)
    fig_11_df["Proportion"] = fig_11_df["Count"] / fig_11_df["Count"].sum() * 100
    fig_11_df_reset = fig_11_df.reset_index()

    fig, ax = plt.subplots(figsize=(16, 7))

    # NAICS label bars — single color fill with grey border, percentage label above each bar
    bars = ax.bar(fig_11_df_reset['NAICS_label'], fig_11_df_reset['Proportion'],
                color='#003F5C', edgecolor=BAR_EDGE_COLOR, width=0.6)

    for bar, val in zip(bars, fig_11_df_reset['Proportion']):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                f"{val:.0f}%", ha="center", fontsize=12, va="bottom")

    # Axis labels and tick formatting
    ax.set_xlabel("NAICS Label", fontsize=14, fontweight='semibold', labelpad=10)
    ax.set_ylabel("Percentage of Employees", fontsize=14, fontweight='semibold', labelpad=10)
    ax.set_xticks(range(len(fig_11_df_reset)))
    ax.set_xticklabels([textwrap.fill(l, width=20, break_long_words=False) for l in fig_11_df_reset['NAICS_label']],
                    fontsize=10, rotation=70, ha="center")
    ax.tick_params(axis='y', labelsize=14)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.set_xlim(-0.7, len(fig_11_df_reset) - 0.3)

    plt.tight_layout()

    # Export Figure
    fig.savefig(f'{output_dir}/figure_11.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Create Table
    fig11_df = pd.DataFrame({
        'NAICS Label': fig_11_df_reset['NAICS_label'].values,
        'Percentage':  fig_11_df_reset['Proportion'].round(0).astype(int).astype(str) + '%',
    })

    # Export Table
    fig11_df.to_csv(f'{table_dir}/figure_11_table.csv', index=False)
