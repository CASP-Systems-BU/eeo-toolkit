import textwrap
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch
from eeo5_figure_config import BAR_EDGE_COLOR, RACE_COLORS, RACE_ORDER_7, WORK_TYPE_ORDER


def figure_40(wcrg_df, output_dir, table_dir):
    fig40_df = (wcrg_df.groupby(['Work Type', 'Race'])['Count'].sum()
                .clip(lower=0).unstack().reindex(WORK_TYPE_ORDER)
                .reindex(columns=RACE_ORDER_7).fillna(0))
    fig40_pct = fig40_df.div(fig40_df.sum(axis=1), axis=0) * 100

    wtypes = list(fig40_df.index)
    x      = np.arange(len(wtypes))
    width  = 0.08
    n_race = len(RACE_ORDER_7)

    fig, ax = plt.subplots(figsize=(10, 6))

    for j, race in enumerate(RACE_ORDER_7):
        color  = RACE_COLORS[race]
        counts = fig40_df[race].values
        pcts   = fig40_pct[race].values
        xpos   = x + (j - n_race / 2 + 0.5) * width

        ax.bar(xpos, counts, width=width, color=color, edgecolor=BAR_EDGE_COLOR)
        for xi, count, pct in zip(xpos, counts, pcts):
            ax.text(xi, count, f'{pct:.0f}%', ha='center', va='bottom', fontsize=7, rotation=90)

    legend_handles = [
        Patch(facecolor=RACE_COLORS[r], edgecolor=BAR_EDGE_COLOR,
              label=textwrap.fill(r, width=30))
        for r in RACE_ORDER_7
    ]
    ax.legend(handles=legend_handles, title='Race', loc='upper right',
              fontsize=9, title_fontsize=10)
    ax.set_xlabel('Work Type', fontweight='semibold', fontsize=14, labelpad=10)
    ax.set_ylabel('Employee Count', fontweight='semibold', fontsize=14, labelpad=10)
    ax.set_xticks(x)
    ax.set_xticklabels([textwrap.fill(w.title(), width=20) for w in wtypes], ha='center', fontsize=12)
    ax.tick_params(axis='y', labelsize=12)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{int(v/1000)}k' if v >= 1000 else f'{int(v)}'))

    plt.tight_layout()

    # Export Figure
    fig.savefig(f'{output_dir}/figure_40.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Create Table
    total     = fig40_df.sum(axis=1)
    fig40_out = pd.DataFrame({'Work Type': fig40_df.index.values})
    for race in RACE_ORDER_7:
        fig40_out[f'{race} Percentage'] = (fig40_df[race].values / total.values * 100).round(0).astype(int).astype(str) + '%'
    # Export Table
    fig40_out.to_csv(f'{table_dir}/figure_40_table.csv', index=False)
