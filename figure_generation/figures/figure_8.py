import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Wedge as MplWedge
from eeo1_figure_config import FEMALE_COLOR, ORG_SIZE_ORDER, MALE_COLOR, BAR_EDGE_COLOR

def figure_8(org_size_gender_df, output_dir, table_dir):

    pie8_df = org_size_gender_df.groupby(['Organizational Size Binned', 'Gender'])['Count'].sum().unstack()
    pie8_df = pie8_df.reindex(ORG_SIZE_ORDER)
    pie8_pct = pie8_df.div(pie8_df.sum(axis=1), axis=0) * 100

    size_totals = pie8_df.sum(axis=1)
    MIN_R, MAX_R = 0.5, 1.0
    radii = MIN_R + (size_totals - size_totals.min()) / (size_totals.max() - size_totals.min()) * (MAX_R - MIN_R)

    g_colors  = [FEMALE_COLOR, MALE_COLOR]

    fig, axes = plt.subplots(2, 2, figsize=(8, 8))
    axes = axes.flatten()

    # Pie charts per org size — radius scaled to total headcount
    for i, size in enumerate(ORG_SIZE_ORDER):
        ax = axes[i]
        r  = radii[size]

        pie_labels = [
            f'Female\n{pie8_pct.loc[size, "Female"]:.0f}%',
            f'Male\n{pie8_pct.loc[size, "Male"]:.0f}%',
        ]

        patches, texts = ax.pie(
            pie8_df.loc[size],
            labels=pie_labels,
            textprops={'fontsize': 14},
            startangle=90,
            colors=g_colors,
            radius=r
        )

        for text in texts:
            text.set_fontsize(13)
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

        ax.set_title(size, fontweight='semibold', fontsize=14)


    fig.text(0.5, 0.02,
        'Note: Pie chart sizes are proportionate to each organizational size group\'s employee count in the overall dataset.',
        ha='center', va='bottom', fontsize=9, style='italic')

    plt.tight_layout()
    plt.subplots_adjust(hspace=0.4, bottom=0.08)

    # Export Figure
    fig.savefig(f'{output_dir}/figure_8.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Create Table
    fig8_df = pd.DataFrame({
        'Organizational Size': pie8_df.index.values,
        'Female Percentage':   (pie8_df['Female'].values / size_totals.values * 100).round(0).astype(int).astype(str) + '%',
        'Male Percentage':     (pie8_df['Male'].values   / size_totals.values * 100).round(0).astype(int).astype(str) + '%',
    })

    # Export Table
    fig8_df.to_csv(f'{table_dir}/figure_8_table.csv', index=False)
