import textwrap
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from eeo5_figure_config import BAR_EDGE_COLOR, RACE_COLORS, RACE_ORDER_7, AGENT_TYPE_ORDER


def figure_35(twr_df, output_dir, table_dir):
    fig35_df = (twr_df.groupby(['Type of Agent', 'Race'])['Count'].sum()
                .unstack().reindex(columns=RACE_ORDER_7).fillna(0)
                .reindex(AGENT_TYPE_ORDER).clip(lower=0))
    fig35_pct = fig35_df.div(fig35_df.sum(axis=1), axis=0) * 100

    agents     = list(fig35_pct.index)
    n          = len(agents)
    bar_height = 0.6
    y_gap      = 1.2

    fig, ax = plt.subplots(figsize=(12, n * y_gap * 0.75 + 1.5))

    for i, agent in enumerate(agents):
        y    = (n - 1 - i) * y_gap
        left = 0

        for race in RACE_ORDER_7:
            val   = fig35_pct.loc[agent, race]
            color = RACE_COLORS[race]

            ax.barh(y, val, left=left, color=color, edgecolor='none', height=bar_height)
            ax.barh(y, val, left=left, color='none', edgecolor=BAR_EDGE_COLOR, height=bar_height)

            mid_x    = left + val / 2
            tick_top = y - bar_height / 2
            tick_bot = tick_top - 0.12
            ax.plot([mid_x, mid_x], [tick_top, tick_bot],
                    color='black', linewidth=0.8, solid_capstyle='butt', clip_on=False)
            ax.text(mid_x, tick_bot - 0.05, f'{val:.0f}%',
                    ha='center', va='top', fontsize=10, clip_on=False)

            left += val

        ax.text(-2, y, textwrap.fill(agent, width=22), ha='right', va='center', fontsize=13)

    ax.set_xlim(-28, 100.3)
    ax.set_ylim(-y_gap * 0.65, (n - 1) * y_gap + y_gap * 0.55)
    ax.axis('off')

    legend_handles = [
        Patch(facecolor=RACE_COLORS[r], edgecolor=BAR_EDGE_COLOR, label=textwrap.fill(r, width=30))
        for r in RACE_ORDER_7
    ]
    ax.legend(handles=legend_handles, title='Race', loc='lower center',
              bbox_to_anchor=(0.5, -0.12), ncol=3, fontsize=11, title_fontsize=12)

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.18)

    # Export Figure
    fig.savefig(f'{output_dir}/figure_35.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Create Table
    total    = fig35_df.sum(axis=1)
    fig35_out = pd.DataFrame({'Agent Type': fig35_df.index.values})
    for race in RACE_ORDER_7:
        fig35_out[f'{race} Percentage'] = (fig35_df[race].values / total.values * 100).round(0).astype(int).astype(str) + '%'
    # Export Table
    fig35_out.to_csv(f'{table_dir}/figure_35_table.csv', index=False)
