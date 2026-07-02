import textwrap
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Wedge as MplWedge
from eeo4_figure_config import BAR_EDGE_COLOR, PIE_ORDER, RACE_COLORS

def figure_28(wfrg_df, output_dir, table_dir):

    EXPLODE = 0.06

    wfrg_df = wfrg_df[wfrg_df['Work_Type'] == 'NEW HIRES']

    fig28_df = (wfrg_df.groupby('Race_Ethnicity')['Count'].sum()
         .clip(lower=0)
         .reindex(PIE_ORDER))

    total    = fig28_df.sum()
    r_colors = [RACE_COLORS[r] for r in PIE_ORDER]
    explode  = [EXPLODE] * len(PIE_ORDER)

    pie_labels = [
        f"{textwrap.fill(race, width=25)}\n{fig28_df[race] / total * 100:.0f}%"
        for race in PIE_ORDER
    ]

    fig, ax = plt.subplots(figsize=(8, 6))

    # Pie chart — each slice colored by race with explode separation
    patches, _ = ax.pie(
        fig28_df,
        labels=pie_labels,
        textprops={'fontsize': 14},
        startangle=90,
        colors=r_colors,
        explode=explode,
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

    plt.tight_layout()

    # Export Figure
    fig.savefig(f'{output_dir}/figure_28.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Create Table
    fig28_df = pd.DataFrame({
        'Race':       list(PIE_ORDER),
        'Percentage': (fig28_df.values / total * 100).round(0).astype(int).astype(str) + '%',
    })

    # Export Table
    fig28_df.to_csv(f'{table_dir}/figure_28_table.csv', index=False)
