import textwrap
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch
from eeo5_figure_config import BAR_EDGE_COLOR, RACE_COLORS, RACE_ORDER_7


def figure_41(jrg_df, output_dir, table_dir):
    fig41_df = (jrg_df.groupby(['Job Category', 'Race'])['Count'].sum()
                .unstack().reindex(columns=RACE_ORDER_7).fillna(0))
    # Sort job categories by total count descending
    fig41_df  = fig41_df.reindex(fig41_df.sum(axis=1).sort_values(ascending=False).index).clip(lower=0)
    fig41_pct = fig41_df.div(fig41_df.sum(axis=1), axis=0) * 100

    cats       = list(fig41_pct.index)
    n          = len(cats)
    bar_height = 0.6
    y_gap      = 1.2

    fig, ax = plt.subplots(figsize=(13, n * y_gap * 0.6))

    for i, cat in enumerate(cats):
        y    = (n - 1 - i) * y_gap
        left = 0

        for race in RACE_ORDER_7:
            val   = fig41_pct.loc[cat, race]
            color = RACE_COLORS[race]

            ax.barh(y, val, left=left, color=color, edgecolor='none', height=bar_height)
            ax.barh(y, val, left=left, color='none', edgecolor=BAR_EDGE_COLOR, height=bar_height)

            if val >= 5:
                mid_x    = left + val / 2
                tick_top = y - bar_height / 2
                tick_bot = tick_top - 0.10
                ax.plot([mid_x, mid_x], [tick_top, tick_bot],
                        color='black', linewidth=0.8, solid_capstyle='butt', clip_on=False)
                ax.text(mid_x, tick_bot - 0.04, f'{val:.0f}%',
                        ha='center', va='top', fontsize=8, clip_on=False)

            left += val

        ax.text(-2, y, textwrap.fill(cat, width=28, break_long_words=False),
                ha='right', va='center', fontsize=10)

    ax.set_xlim(-30, 100.3)
    ax.set_ylim(-y_gap * 0.65, (n - 1) * y_gap + y_gap * 0.55)
    ax.axis('off')

    legend_handles = [
        Patch(facecolor=RACE_COLORS[r], edgecolor=BAR_EDGE_COLOR,
              label=textwrap.fill(r, width=30))
        for r in RACE_ORDER_7
    ]
    ax.legend(handles=legend_handles, title='Race', loc='lower center',
              bbox_to_anchor=(0.5, -0.06), ncol=3, fontsize=10, title_fontsize=11)

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.12)

    # Export Figure
    fig.savefig(f'{output_dir}/figure_41.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Create Table
    total     = fig41_df.sum(axis=1)
    fig41_out = pd.DataFrame({'Job Category': fig41_df.index.values})
    for race in RACE_ORDER_7:
        fig41_out[f'{race} Percentage'] = (fig41_df[race].values / total.values * 100).round(0).astype(int).astype(str) + '%'
    # Export Table
    fig41_out.to_csv(f'{table_dir}/figure_41_table.csv', index=False)
