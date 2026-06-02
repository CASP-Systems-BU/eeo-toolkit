import textwrap
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Wedge as MplWedge
from eeo1_config import ORG_SIZE_ORDER, PIE_ORDER, BAR_EDGE_COLOR, RACE_COLORS, RACE_ORDER_5

def figure_9(org_size_race_df, output_dir, table_dir):
    EXPLODE = 0.06
    
    large_groups_r = org_size_race_df[org_size_race_df['Race'].isin(PIE_ORDER)]

    pie9_df = large_groups_r.groupby(['Organizational Size Binned', 'Race'])['Count'].sum().unstack()
    pie9_df = pie9_df.reindex(ORG_SIZE_ORDER)[PIE_ORDER]

    size_totals = pie9_df.sum(axis=1)
    MIN_R, MAX_R = 0.5, 1.0
    radii = MIN_R + (size_totals - size_totals.min()) / (size_totals.max() - size_totals.min()) * (MAX_R - MIN_R)

    r_colors = [RACE_COLORS[r] for r in PIE_ORDER]
    explode  = [EXPLODE] * len(PIE_ORDER)

    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    axes = axes.flatten()

    # Pie charts per org size — radius scaled to total headcount
    for i, size in enumerate(ORG_SIZE_ORDER):
        ax    = axes[i]
        r     = radii[size]
        total = pie9_df.loc[size].sum()

        pie_labels = [
            f"{textwrap.fill(race, width=25)}\n{pie9_df.loc[size, race] / total * 100:.0f}%"
            for race in PIE_ORDER
        ]

        patches, texts = ax.pie(
            pie9_df.loc[size],
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

        ax.set_title(size, fontweight='semibold', fontsize=14)
        

    fig.text(0.5, 0.02,
            'Note: Pie chart sizes are proportionate to each organizational size group\'s employee count in the overall dataset.',
            ha='center', va='bottom', fontsize=9, style='italic')

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.08, hspace=0.4)

    # Export Figure
    fig.savefig(f'{output_dir}/figure_9.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Create Table
    fig9_all = (org_size_race_df.groupby(['Organizational Size Binned', 'Race'])['Count'].sum()
            .unstack()
            .reindex(ORG_SIZE_ORDER)[RACE_ORDER_5])
    size_totals_all = fig9_all.sum(axis=1)

    fig9_df = pd.DataFrame({'Organizational Size': fig9_all.index.values})
    for race in RACE_ORDER_5:
        fig9_df[f'{race} Percentage'] = (fig9_all[race].values / size_totals_all.values * 100).round(0).astype(int).astype(str) + '%'

    # Export Table
    fig9_df.to_csv(f'{table_dir}/figure_9_table.csv', index=False)
