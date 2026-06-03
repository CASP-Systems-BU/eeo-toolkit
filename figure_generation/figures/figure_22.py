import textwrap
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Wedge as MplWedge
from eeo4_config import BAR_EDGE_COLOR, SALARY_LABELS_K_TABLE, SALARY_ORDER, SALARY_LABELS_K, PIE_ORDER, RACE_COLORS

def figure_22(wfrg_df, output_dir, table_dir):

    wfrg_df = wfrg_df[wfrg_df['Work_Type'] != 'NEW HIRES']

    EXPLODE = 0.06

    fig22_df = (wfrg_df[wfrg_df['Salary_Range'] != '-']
            .groupby(['Salary_Range', 'Race_Ethnicity'])['Count'].sum()
            .clip(lower=0)
            .unstack()
            .reindex(SALARY_ORDER[::-1])[PIE_ORDER]
            .fillna(0))

    band_totals = fig22_df.sum(axis=1)
    MIN_R, MAX_R = 0.5, 1.0
    radii = MIN_R + (band_totals - band_totals.min()) / (band_totals.max() - band_totals.min()) * (MAX_R - MIN_R)

    r_colors = [RACE_COLORS[r] for r in PIE_ORDER]
    explode  = [EXPLODE] * len(PIE_ORDER)

    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    axes = axes.flatten()

    # Pie charts per salary band — radius scaled to total headcount
    for i, band in enumerate(SALARY_ORDER[::-1]):
        ax    = axes[i]
        r     = radii[band]
        total = fig22_df.loc[band].sum()

        pie_labels = [
            f"{textwrap.fill(race, width=25)}\n{fig22_df.loc[band, race] / total * 100:.0f}%"
            for race in PIE_ORDER
        ]

        patches, _ = ax.pie(
            fig22_df.loc[band],
            labels=pie_labels,
            textprops={'fontsize': 14},
            startangle=90,
            colors=r_colors,
            explode=explode,
            radius=r
        )

        # Grey border overlay and radial tick line per wedge
        for wedge in patches:
            outer = MplWedge(
                wedge.center, wedge.r, wedge.theta1, wedge.theta2,
                facecolor='none', edgecolor=BAR_EDGE_COLOR, linewidth=0.8,
                transform=ax.transData
            )
            ax.add_patch(outer)
            mid_angle = np.radians((wedge.theta1 + wedge.theta2) / 2)
            cx, cy = wedge.center
            x0 = cx + wedge.r * np.cos(mid_angle)
            y0 = cy + wedge.r * np.sin(mid_angle)
            x1 = cx + (wedge.r + 0.05) * np.cos(mid_angle)
            y1 = cy + (wedge.r + 0.05) * np.sin(mid_angle)
            ax.plot([x0, x1], [y0, y1], color='black', linewidth=0.8, solid_capstyle='butt', clip_on=False)

        ax.set_title(SALARY_LABELS_K[band], fontsize=14, fontweight='semibold')

    fig.text(0.5, 0.02,
            'Note: Pie chart sizes are proportionate to each salary band\'s employee count in the overall dataset.',
            ha='center', va='bottom', fontsize=9, style='italic')

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.08, hspace=0.4)

    # Export Figure
    fig.savefig(f'{output_dir}/figure_22.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Create Table
    fig22_all = (wfrg_df[wfrg_df['Salary_Range'] != '-']
               .groupby(['Salary_Range', 'Race_Ethnicity'])['Count'].sum()
               .unstack().reindex(SALARY_ORDER)[PIE_ORDER].fillna(0).clip(lower=0))
    total = fig22_all.sum(axis=1).sort_values(ascending=False)
    fig22_all = fig22_all.reindex(total.index)

    fig22_df = pd.DataFrame({'Salary Band': [SALARY_LABELS_K_TABLE[b] for b in fig22_all.index]})
    for race in PIE_ORDER:
        fig22_df[f'{race} Percentage'] = (fig22_all[race].values / total.values * 100).round(0).astype(int).astype(str) + '%'

    # Export Table
    fig22_df.to_csv(f'{table_dir}/figure_22_table.csv', index=False)
