import textwrap
from matplotlib.patches import Patch
import pandas as pd
import matplotlib.pyplot as plt
from eeo4_config import BAR_EDGE_COLOR, RACE_COLORS, RACE_ORDER_5

def figure_19(wfrg_df, output_dir, table_dir):

    wfrg_df = wfrg_df[wfrg_df['Work_Type'] != 'NEW HIRES']

    figure19_df = (wfrg_df.groupby(['Government_Function', 'Race_Ethnicity'])['Count'].sum()
             .unstack()
             .reindex(columns=RACE_ORDER_5)
             .fillna(0))
    figure19_df  = figure19_df.reindex(figure19_df.sort_index().index).clip(lower=0)
    figure19_pct = figure19_df.div(figure19_df.sum(axis=1), axis=0) * 100

    funcs_flip = list(figure19_pct.index)
    n          = len(funcs_flip)
    bar_height = 0.6
    y_gap      = 1.2

    fig, ax = plt.subplots(figsize=(12, n * y_gap * 0.75))

    # Stacked horizontal race bars per government function — tick line + label below each segment
    for i, func in enumerate(funcs_flip):
        y    = (n - 1 - i) * y_gap
        left = 0

        for race in RACE_ORDER_5:
            val   = figure19_pct.loc[func, race]
            color = RACE_COLORS[race]

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

        # Government function label to the left
        ax.text(-2, y, textwrap.fill(func, width=24, break_long_words=False),
                ha='right', va='center', color='black', fontsize=14)

    ax.set_xlim(-25, 100.3)
    ax.set_ylim(-y_gap * 0.65, (n - 1) * y_gap + y_gap * 0.55)
    ax.axis('off')

    # Legend
    legend_handles = [
        Patch(facecolor=RACE_COLORS[r], edgecolor=BAR_EDGE_COLOR, label=r)
        for r in RACE_ORDER_5
    ]
    ax.legend(handles=legend_handles, title='Race', loc='lower center', bbox_to_anchor=(0.5, -0.08), ncol=3, fontsize=14, title_fontsize=14)

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.1)

    # Export Figure
    fig.savefig(f'{output_dir}/figure_19.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Create Table
    fig19_all = (wfrg_df.groupby(['Government_Function', 'Race_Ethnicity'])['Count'].sum()
                  .unstack().sort_index()[RACE_ORDER_5].fillna(0).clip(lower=0))
    total = fig19_all.sum(axis=1)

    fig19_df = pd.DataFrame({'Government Function': fig19_all.index.values})
    for race in RACE_ORDER_5:
        fig19_df[f'{race} Percentage'] = (fig19_all[race].values / total.values * 100).round(0).astype(int).astype(str) + '%'

    # Export Table
    fig19_df.to_csv(f'{table_dir}/figure_19_table.csv', index=False)
