import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Wedge as MplWedge
from eeo4_figure_config import BAR_EDGE_COLOR, FEMALE_COLOR, MALE_COLOR, SALARY_LABELS_K_TABLE, SALARY_ORDER, SALARY_LABELS_K

def figure_21(wfrg_df, output_dir, table_dir):

    wfrg_df = wfrg_df[wfrg_df['Work_Type'] != 'NEW HIRES']

    fig21_df = (wfrg_df[wfrg_df['Salary_Range'] != '-']
            .groupby(['Salary_Range', 'Gender'])['Count'].sum()
            .clip(lower=0)
            .unstack()[['Female', 'Male']]
            .reindex(SALARY_ORDER))
    fig21_pct = fig21_df.div(fig21_df.sum(axis=1), axis=0) * 100

    band_totals = fig21_df.sum(axis=1)
    MIN_R, MAX_R = 0.5, 1.0
    radii = MIN_R + (band_totals - band_totals.min()) / (band_totals.max() - band_totals.min()) * (MAX_R - MIN_R)

    g_colors = [FEMALE_COLOR, MALE_COLOR]

    fig, axes = plt.subplots(2, 2, figsize=(8, 8))
    axes = axes.flatten()

    # Pie charts per salary band — radius scaled to total headcount
    for i, band in enumerate(SALARY_ORDER[::-1]):
        ax = axes[i]
        r  = radii[band]

        pie_labels = [
            f'Female\n{fig21_pct.loc[band, "Female"]:.0f}%',
            f'Male\n{fig21_pct.loc[band, "Male"]:.0f}%',
        ]

        patches, texts = ax.pie(
            fig21_df.loc[band],
            labels=pie_labels,
            textprops={'fontsize': 14},
            startangle=90,
            colors=g_colors,
            radius=r,
            wedgeprops={'edgecolor': 'white'}
        )

        for text in texts:
            text.set_multialignment('left')

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
    plt.subplots_adjust(hspace=0.4, bottom=0.08)

    # Export Figure
    fig.savefig(f'{output_dir}/figure_21.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Create Table
    total = fig21_df.sum(axis=1).sort_values(ascending=False)
    fig21_sorted = fig21_df.reindex(total.index)

    fig21_df = pd.DataFrame({
        'Salary Band':       [SALARY_LABELS_K_TABLE[b] for b in fig21_sorted.index],
        'Female Percentage': (fig21_sorted['Female'].values / total.values * 100).round(0).astype(int).astype(str) + '%',
        'Male Percentage':   (fig21_sorted['Male'].values   / total.values * 100).round(0).astype(int).astype(str) + '%',
    })

    # Export Table
    fig21_df.to_csv(f'{table_dir}/figure_21_table.csv', index=False)
