import textwrap
import pandas as pd
import matplotlib.pyplot as plt
from eeo4_figure_config import BAR_EDGE_COLOR, FEMALE_COLOR, MALE_COLOR

def figure_18(wfrg_df, output_dir, table_dir):

    wfrg_df = wfrg_df[wfrg_df['Work_Type'] != 'NEW HIRES']

    fig18_df = (wfrg_df.groupby(['Government_Function', 'Gender'])['Count'].sum()
                .unstack()[['Female', 'Male']])
    func_order_flip = fig18_df.sort_index().index
    fig18_df  = fig18_df.reindex(func_order_flip)
    fig18_pct = fig18_df.div(fig18_df.sum(axis=1), axis=0) * 100

    funcs_flip = list(fig18_pct.index)
    n = len(funcs_flip)

    bar_height = 0.6
    y_gap      = 1.2

    fig, ax = plt.subplots(figsize=(12, n * y_gap * 0.75))

    for i, func in enumerate(funcs_flip):
        y  = (n - 1 - i) * y_gap
        fp = fig18_pct.loc[func, 'Female']
        mp = fig18_pct.loc[func, 'Male']

        # Female segment
        ax.barh(y, fp, color=FEMALE_COLOR, edgecolor='none', height=bar_height)
        overlay = ax.barh(y, fp, color='none', edgecolor='white', height=bar_height)
        for patch in overlay:
            patch.set_linewidth(0)
        ax.barh(y, fp, color='none', edgecolor=BAR_EDGE_COLOR, height=bar_height)

        # Male segment
        ax.barh(y, mp, left=fp, color=MALE_COLOR, edgecolor='none', height=bar_height)
        ax.barh(y, mp, left=fp, color='none', edgecolor=BAR_EDGE_COLOR, height=bar_height)

        # Percentages below bar
        ax.text(2,  y - bar_height / 2 - 0.08, f'{fp:.0f}%',
                ha='center', va='top', color='black', fontsize=12)
        ax.text(98, y - bar_height / 2 - 0.08, f'{mp:.0f}%',
                ha='center', va='top', color='black', fontsize=12)

        # Government function label to the left
        ax.text(-2, y, textwrap.fill(func, width=24, break_long_words=False),
                ha='right', va='center', color='black', fontsize=14)

    # 'Female' / 'Male' labels above first (top) bar only
    top_y = (n - 1) * y_gap
    ax.text(0.5,  top_y + bar_height / 2 + 0.08, 'Female', ha='left',  va='bottom', fontsize=14, fontweight='medium')
    ax.text(99.5, top_y + bar_height / 2 + 0.08, 'Male',   ha='right', va='bottom', fontsize=14, fontweight='medium')

    ax.set_xlim(-38, 100.3)
    ax.set_ylim(-y_gap * 0.65, top_y + y_gap * 0.55)
    ax.axis('off')

    plt.tight_layout()

    # Export Figure
    fig.savefig(f'{output_dir}/figure_18.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Create Table
    total = fig18_df.sum(axis=1)
    fig18_df = pd.DataFrame({
        'Government Function': fig18_df.index.values,
        'Female Percentage':   (fig18_df['Female'].values / total.values * 100).round(0).astype(int).astype(str) + '%',
        'Male Percentage':     (fig18_df['Male'].values   / total.values * 100).round(0).astype(int).astype(str) + '%',
    })

    # Export Table
    fig18_df.to_csv(f'{table_dir}/figure_18_table.csv', index=False)
