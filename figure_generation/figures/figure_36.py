import textwrap
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from eeo5_figure_config import BAR_EDGE_COLOR, WORK_TYPE_COLORS, WORK_TYPE_ORDER, AGENT_TYPE_ORDER


def figure_36(twg_df, output_dir, table_dir):
    fig36_df = (twg_df.groupby(['Type of Agent', 'Work Type'])['Count'].sum()
                .unstack().reindex(columns=WORK_TYPE_ORDER).fillna(0)
                .reindex(AGENT_TYPE_ORDER).clip(lower=0))
    fig36_pct = fig36_df.div(fig36_df.sum(axis=1), axis=0) * 100

    agents     = list(fig36_pct.index)
    n          = len(agents)
    bar_height = 0.6
    y_gap      = 1.2

    fig, ax = plt.subplots(figsize=(10, n * y_gap * 0.75 + 1.5))

    for i, agent in enumerate(agents):
        y    = (n - 1 - i) * y_gap
        left = 0

        for wtype in WORK_TYPE_ORDER:
            val   = fig36_pct.loc[agent, wtype]
            color = WORK_TYPE_COLORS[wtype]

            ax.barh(y, val, left=left, color=color, edgecolor='none', height=bar_height)
            ax.barh(y, val, left=left, color='none', edgecolor=BAR_EDGE_COLOR, height=bar_height)

            mid_x    = left + val / 2
            tick_top = y - bar_height / 2
            tick_bot = tick_top - 0.12
            ax.plot([mid_x, mid_x], [tick_top, tick_bot],
                    color='black', linewidth=0.8, solid_capstyle='butt', clip_on=False)
            ax.text(mid_x, tick_bot - 0.05, f'{val:.0f}%',
                    ha='center', va='top', fontsize=12, clip_on=False)

            left += val

        ax.text(-2, y, textwrap.fill(agent, width=22), ha='right', va='center', fontsize=13)

    ax.set_xlim(-28, 100.3)
    ax.set_ylim(-y_gap * 0.65, (n - 1) * y_gap + y_gap * 0.55)
    ax.axis('off')

    legend_handles = [
        Patch(facecolor=WORK_TYPE_COLORS[w], edgecolor=BAR_EDGE_COLOR,
              label=textwrap.fill(w.title(), width=20))
        for w in WORK_TYPE_ORDER
    ]
    ax.legend(handles=legend_handles, title='Work Type', loc='lower center',
              bbox_to_anchor=(0.5, -0.12), ncol=2, fontsize=12, title_fontsize=12)

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.15)

    # Export Figure
    fig.savefig(f'{output_dir}/figure_36.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Create Table
    total     = fig36_df.sum(axis=1)
    fig36_out = pd.DataFrame({'Agent Type': fig36_df.index.values})
    for wtype in WORK_TYPE_ORDER:
        fig36_out[f'{wtype} Percentage'] = (fig36_df[wtype].values / total.values * 100).round(0).astype(int).astype(str) + '%'
    # Export Table
    fig36_out.to_csv(f'{table_dir}/figure_36_table.csv', index=False)
