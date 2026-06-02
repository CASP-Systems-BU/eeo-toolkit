import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import textwrap
from eeo1_config import BAR_EDGE_COLOR, RACE_COLORS, RACE_ORDER_5

def figure_7(df, output_dir, table_dir):
    RACES_7 = ['White', 'Asian', 'Black or African American']

    job_race = df[df['Race'].isin(RACES_7)].groupby(['JobCategory', 'Race'])['Count'].sum().unstack()
    count_order = df.groupby('JobCategory')['Count'].sum().sort_values(ascending=False).index
    job_race = job_race.reindex(count_order)[RACES_7]
    job_totals = df.groupby('JobCategory')['Count'].sum().reindex(job_race.index)

    y     = np.arange(len(job_race))
    width = 0.25

    fig, ax = plt.subplots(figsize=(10, 12))

    # Grouped horizontal bars by race — colored fill with grey border, labeled percentage to the right
    for j, race in enumerate(RACES_7):
        color = RACE_COLORS[race]
        vals  = job_race[race].values
        ypos  = y + (j - 1) * width

        ax.barh(ypos, vals, height=width, color=color, edgecolor='none')
        ax.barh(ypos, vals, height=width, color='none', edgecolor=BAR_EDGE_COLOR)

        for yi, val, total in zip(ypos, vals, job_totals.values):
            pct = val / total * 100
            ax.text(val + 1500, yi, f"{race}, {pct:.0f}%", fontsize=12,
                    ha='left', va='center')

    # Axis labels and tick formatting
    ax.set_xlim(0.5, job_race.max().max() * 1.2)
    ax.set_ylim(-0.5, len(job_race) - 0.5)
    ax.invert_yaxis()
    ax.set_xlabel("Employee Count", fontsize=14, fontweight='semibold', labelpad=10)
    ax.set_ylabel("Job Category", fontsize=14, fontweight='semibold', labelpad=10)
    ax.set_yticks(y)
    ax.set_yticklabels([textwrap.fill(l, width=20, break_long_words=False) for l in job_race.index], fontsize=12, ha="right")
    ax.tick_params(axis='x', labelsize=14)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{int(v/1000)}k' if v >= 1000 else f'{int(v)}'))

    plt.tight_layout()

    # Export Figure
    fig.savefig(f'{output_dir}/figure_7.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Create Table
    fig7_all = (df.groupby(['JobCategory', 'Race'])['Count'].sum()
             .unstack()
             .reindex(count_order)[RACE_ORDER_5])
    job_totals_all = df.groupby('JobCategory')['Count'].sum().reindex(count_order)

    fig7_df = pd.DataFrame({'Job Category': fig7_all.index.values})
    for race in RACES_7:
        fig7_df[f'{race} Percentage'] = (fig7_all[race].values / job_totals_all.values * 100).round(0).astype(int).astype(str) + '%'

    # Export Table
    fig7_df.to_csv(f'{table_dir}/figure_7_table.csv', index=False)
