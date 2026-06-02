import textwrap
from matplotlib.patches import Patch
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from eeo1_config import BAR_EDGE_COLOR, RACE_ORDER_5, RACE_COLORS

def figure_12(df, output_dir, table_dir):
    naics_total = df.groupby('NAICS_label')['Count'].sum().sort_values(ascending=True)
    naics_order = list(naics_total.index)

    naics_race = (df[df['Race'].isin(RACE_ORDER_5)]
                .groupby(['NAICS_label', 'Race'])['Count'].sum()
                .unstack()
                .reindex(naics_order)[RACE_ORDER_5]
                .fillna(0)
                .clip(lower=0))

    wrapped_labels = [textwrap.fill(l, width=30, break_long_words=False) for l in naics_order]

    fig, ax = plt.subplots(figsize=(12, 12))

    # Stacked horizontal race bars — colored fill with grey border
    lefts = np.zeros(len(naics_race))
    for race in RACE_ORDER_5:
        vals  = naics_race[race].values
        color = RACE_COLORS[race]

        ax.barh(wrapped_labels, vals, left=lefts, color=color, edgecolor='none')
        ax.barh(wrapped_labels, vals, left=lefts, color='none', edgecolor=BAR_EDGE_COLOR)

        lefts += vals

    # Legend and axis labels
    legend_handles = [
        Patch(facecolor=RACE_COLORS[r], label=r)
        for r in RACE_ORDER_5
    ]
    ax.legend(handles=legend_handles, title='Race',
            loc='lower center', bbox_to_anchor=(0.5, -0.2), ncol=3, fontsize=14, title_fontsize=14)

    ax.set_xlabel('Employee Count', fontweight='semibold', fontsize=14, labelpad=10)
    ax.set_ylabel('NAICS Label', fontweight='semibold', fontsize=14, labelpad=10)
    ax.tick_params(axis='x', labelsize=14)
    ax.tick_params(axis='y', labelsize=12)
    ax.xaxis.set_major_locator(plt.MultipleLocator(50000))
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{int(v/1000)}k' if v >= 1000 else f'{int(v)}'))
    ax.set_ylim(-0.7, len(wrapped_labels) - 0.3)

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.08)

    # Export Figure
    fig.savefig(f'{output_dir}/figure_12.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Create Table
    fig12_all = (df.groupby(['NAICS_label', 'Race'])['Count'].sum()
                   .unstack()
                   .reindex(naics_order)[RACE_ORDER_5]
                   .fillna(0))

    total = fig12_all.sum(axis=1).sort_values(ascending=False)
    fig12_all = fig12_all.reindex(total.index)

    fig12_df = pd.DataFrame({'NAICS Label': fig12_all.index.values})
    for race in RACE_ORDER_5:
        fig12_df[f'{race} Percentage'] = (fig12_all[race].values / total.values * 100).round(0).astype(int).astype(str) + '%'

    # Export Table
    fig12_df.to_csv(f'{table_dir}/figure_12_table.csv', index=False)
