import textwrap
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge as MplWedge
import numpy as np
from eeo4_figure_config import BAR_EDGE_COLOR, PIE_ORDER, RACE_COLORS

def figure_15(jrg_df, output_dir, table_dir):
    EXPLODE = 0.06
    large_groups = jrg_df[jrg_df['Race'].isin(PIE_ORDER)]
    pie_df = large_groups.groupby('Race')['Count'].sum().reindex(PIE_ORDER)
    total = pie_df.sum()
    colors = [RACE_COLORS[r] for r in PIE_ORDER]
    explode = [EXPLODE] * len(PIE_ORDER)

    pie_labels = [
        f"{textwrap.fill(race, width=30)}\n{pie_df[race] / total * 100:.0f}%"
        for race in PIE_ORDER
    ]

    fig, ax = plt.subplots()

    # Pie chart — each slice colored by race with explode separation
    patches, texts = ax.pie(
        pie_df,
        labels=pie_labels,
        textprops={'fontsize': 14},
        explode=explode,
        startangle=90,
        colors=colors
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

    # Export Figure
    fig.savefig(f'{output_dir}/figure_15.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Create Table
    fig15_df = pd.DataFrame({
        'Race':       list(PIE_ORDER),
        'Percentage': (pie_df.values / total * 100).round(0).astype(int).astype(str) + '%',
    })
    
    # Export Table
    fig15_df.to_csv(f'{table_dir}/figure_15_table.csv', index=False)
