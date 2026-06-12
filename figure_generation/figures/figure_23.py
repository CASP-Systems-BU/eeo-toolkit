import textwrap
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch
from eeo4_figure_config import BAR_EDGE_COLOR, SALARY_LABELS_K_TABLE, SALARY_ORDER, SALARY_LABELS_K, SALARY_COLORS, RACE_ORDER_5

def figure_23(wfrg_df, output_dir, table_dir):

    wfrg_df = wfrg_df[wfrg_df['Work_Type'] != 'NEW HIRES']

    fig23_df = (wfrg_df[wfrg_df['Salary_Range'] != '-']
             .groupby(['Race_Ethnicity', 'Salary_Range'])['Count'].sum()
             .unstack()
             .reindex(columns=SALARY_ORDER[::-1])
             .fillna(0))
    fig23_df  = fig23_df.reindex(RACE_ORDER_5).clip(lower=0)
    fig23_pct = fig23_df.div(fig23_df.sum(axis=1), axis=0) * 100

    races      = list(fig23_pct.index)
    n          = len(races)
    bar_height = 0.6
    y_gap      = 1.2

    fig, ax = plt.subplots(figsize=(12, n * y_gap * 0.75))

    # Stacked horizontal salary bars per race — tick line + label below each segment
    for i, race in enumerate(races):
        y    = (n - 1 - i) * y_gap
        left = 0

        for band in SALARY_ORDER:
            val   = fig23_pct.loc[race, band]
            color = SALARY_COLORS[band]

            ax.barh(y, val, left=left, color=color, edgecolor='none', height=bar_height)
            ax.barh(y, val, left=left, color='none', edgecolor=BAR_EDGE_COLOR, height=bar_height)

            mid_x    = left + val / 2
            tick_top = y - bar_height / 2
            tick_bot = tick_top - 0.12
            ax.plot([mid_x, mid_x], [tick_top, tick_bot],
                    color='black', linewidth=0.8, solid_capstyle='butt', clip_on=False)
            ax.text(mid_x, tick_bot - 0.05, f'{val:.0f}%',
                    ha='center', va='top', color='black', fontsize=12, clip_on=False)

            left += val

        # Race label to the left
        ax.text(-2, y, textwrap.fill(race, width=30, break_long_words=False),
                ha='right', va='center', color='black', fontsize=14)

    ax.set_xlim(-25, 100.3)
    ax.set_ylim(-y_gap * 0.65, (n - 1) * y_gap + y_gap * 0.55)
    ax.axis('off')

    # Legend
    legend_handles = [
        Patch(facecolor=SALARY_COLORS[b], edgecolor=BAR_EDGE_COLOR, label=SALARY_LABELS_K[b])
        for b in SALARY_ORDER
    ]
    ax.legend(handles=legend_handles, title='Salary Band',
            loc='lower center', bbox_to_anchor=(0.5, -0.25), ncol=len(SALARY_ORDER), fontsize=14, title_fontsize=14)

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.1)

    # Export Figure
    fig.savefig(f'{output_dir}/figure_23.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Create Table
    fig23_all = (wfrg_df[wfrg_df['Salary_Range'] != '-']
               .groupby(['Race_Ethnicity', 'Salary_Range'])['Count'].sum()
               .unstack().reindex(columns=SALARY_ORDER)
               .reindex(RACE_ORDER_5).fillna(0).clip(lower=0))
    total = fig23_all.sum(axis=1)

    fig23_df = pd.DataFrame({'Race': fig23_all.index.values})
    for band in SALARY_ORDER:
        label = SALARY_LABELS_K_TABLE[band]
        fig23_df[f'{label} Percentage'] = (fig23_all[band].values / total.values * 100).round(0).astype(int).astype(str) + '%'

    # Export Table
    fig23_df.to_csv(f'{table_dir}/figure_23_table.csv', index=False)
