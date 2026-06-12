import textwrap
from matplotlib.patches import Patch
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from eeo1_figure_config import BAR_EDGE_COLOR, FEMALE_COLOR, MALE_COLOR

def figure_13(df, output_dir, table_dir):
    naics_total    = df.groupby("NAICS_label")["Count"].sum().sort_values(ascending=True)
    naics_order    = list(naics_total.index)

    naics_gender_df = (df.groupby(["NAICS_label", "Gender"])["Count"].sum()
                    .unstack().reindex(naics_order)[["Female", "Male"]])
    wrapped_labels  = [textwrap.fill(l, width=30, break_long_words=False) for l in naics_order]

    fig, ax = plt.subplots(figsize=(12, 12))

    # Stacked horizontal gender bars — colored fill with grey border
    lefts = np.zeros(len(naics_gender_df))
    for gender in ["Female", "Male"]:
        color = FEMALE_COLOR if gender == "Female" else MALE_COLOR
        vals  = naics_gender_df[gender].fillna(0).values

        ax.barh(wrapped_labels, vals, left=lefts, color=color, edgecolor="none")
        overlay = ax.barh(wrapped_labels, vals, left=lefts, color="none", edgecolor="white")
        for patch in overlay:
            patch.set_linewidth(0)
        ax.barh(wrapped_labels, vals, left=lefts, color="none", edgecolor=BAR_EDGE_COLOR)

        lefts += vals

    # Legend and axis labels
    legend_handles = [
        Patch(facecolor=FEMALE_COLOR, edgecolor=BAR_EDGE_COLOR, label="Female"),
        Patch(facecolor=MALE_COLOR, edgecolor=BAR_EDGE_COLOR, label="Male"),
    ]
    ax.legend(handles=legend_handles, title="Sex",
            loc="lower center", bbox_to_anchor=(0.5, -0.15), ncol=2, fontsize=14, title_fontsize=14)

    ax.set_xlabel("Employee Count", fontweight='semibold', fontsize=14, labelpad=10)
    ax.set_ylabel('NAICS Label', fontweight='semibold', fontsize=14, labelpad=10)
    ax.tick_params(axis='x', labelsize=14)
    ax.tick_params(axis='y', labelsize=12)
    ax.xaxis.set_major_locator(plt.MultipleLocator(50000))
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{int(v/1000)}k' if v >= 1000 else f'{int(v)}'))
    ax.set_ylim(-0.7, len(wrapped_labels) - 0.3)

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.08)

    # Export Figure
    fig.savefig(f'{output_dir}/figure_13.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Create Table
    fig13_all = naics_gender_df.fillna(0)
    total = fig13_all.sum(axis=1).sort_values(ascending=False)
    fig13_all = fig13_all.reindex(total.index)

    fig13_df = pd.DataFrame({
        'NAICS Label':       fig13_all.index.values,
        'Female Percentage': (fig13_all['Female'].values / total.values * 100).round(0).astype(int).astype(str) + '%',
        'Male Percentage':   (fig13_all['Male'].values   / total.values * 100).round(0).astype(int).astype(str) + '%',
    })

    # Export Table
    fig13_df.to_csv(f'{table_dir}/figure_13_table.csv', index=False)
