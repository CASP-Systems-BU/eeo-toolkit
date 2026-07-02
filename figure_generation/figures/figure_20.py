import textwrap
from matplotlib.patches import Patch
import pandas as pd
import matplotlib.pyplot as plt
from eeo4_figure_config import BAR_EDGE_COLOR, SALARY_LABELS_K_TABLE, SALARY_ORDER, SALARY_COLORS, SALARY_LABELS_K

def figure_20(wfrg_df, output_dir, table_dir):

    wfrg_df = wfrg_df[wfrg_df['Work_Type'] != 'NEW HIRES']

    fig20_df = (wfrg_df[wfrg_df['Salary_Range'] != '-']
             .groupby(['Government_Function', 'Salary_Range'])['Count'].sum()
             .unstack()
             .reindex(columns=SALARY_ORDER[::-1])
             .fillna(0))
    fig20_df  = fig20_df.reindex(fig20_df.sort_index().index).clip(lower=0)
    fig20_pct = fig20_df.div(fig20_df.sum(axis=1), axis=0) * 100

    funcs_flip = list(fig20_pct.index)
    n          = len(funcs_flip)
    bar_height = 0.6
    y_gap      = 1.2

    fig, ax = plt.subplots(figsize=(12, n * y_gap * 0.75))

    # Stacked horizontal salary bars per government function — tick line + label below each segment
    for i, func in enumerate(funcs_flip):
        y    = (n - 1 - i) * y_gap
        left = 0

        for band in SALARY_ORDER:
            val   = fig20_pct.loc[func, band]
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

        # Government function label to the left
        ax.text(-2, y, textwrap.fill(func, width=24, break_long_words=False),
                ha='right', va='center', color='black', fontsize=14)

    ax.set_xlim(-25, 100.3)
    ax.set_ylim(-y_gap * 0.65, (n - 1) * y_gap + y_gap * 0.55)
    ax.axis('off')

    # Legend
    legend_handles = [
        Patch(facecolor=SALARY_COLORS[b], edgecolor=BAR_EDGE_COLOR, label=SALARY_LABELS_K[b])
        for b in SALARY_ORDER
    ]
    ax.legend(handles=legend_handles, title='Salary Band', loc='lower center', bbox_to_anchor=(0.5, -0.08), ncol=len(SALARY_ORDER), fontsize=14, title_fontsize=14)

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.1)

    # Export Figure
    fig.savefig(f'{output_dir}/figure_20.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Create Table
    fig20_all = (wfrg_df[wfrg_df['Salary_Range'] != '-']
                      .groupby(['Government_Function', 'Salary_Range'])['Count'].sum()
                      .unstack().reindex(columns=SALARY_ORDER).sort_index().fillna(0).clip(lower=0))
    total = fig20_all.sum(axis=1)

    fig20_df = pd.DataFrame({'Government_Function': fig20_all.index.values})
    for band in SALARY_ORDER:
        label = SALARY_LABELS_K_TABLE[band]
        fig20_df[f'{label} Percentage'] = (fig20_all[band].values / total.values * 100).round(0).astype(int).astype(str) + '%'

    # Export Table
    fig20_df.to_csv(f'{table_dir}/figure_20_table.csv', index=False)
