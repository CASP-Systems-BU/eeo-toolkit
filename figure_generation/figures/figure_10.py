import textwrap
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch
from eeo1_config import BAR_EDGE_COLOR

def figure_10(org_size_gender_df, output_dir, table_dir):
    ORG_SIZES_10   = ['Small', 'Very Large']
    ORG_COLORS_10  = {'Small': '#003F5C', 'Very Large': '#FFA600'}

    job_org = (org_size_gender_df[org_size_gender_df['Organizational Size Binned'].isin(ORG_SIZES_10)]
            .groupby(['JobCategory', 'Organizational Size Binned'])['Count'].sum()
            .unstack()[ORG_SIZES_10])

    org_totals = job_org.sum(axis=0)
    job_org_pct = job_org.div(org_totals, axis=1) * 100

    count_order = job_org.sum(axis=1).sort_values(ascending=False).index
    job_org_pct = job_org_pct.reindex(count_order)

    x     = np.arange(len(job_org_pct))
    width = 0.35

    fig, ax = plt.subplots(figsize=(14, 6))

    # Grouped bars by org size — colored fill with grey border, percentage label above each bar
    for j, size in enumerate(ORG_SIZES_10):
        color  = ORG_COLORS_10[size]
        vals   = job_org_pct[size].values
        xpos   = x + (j - 0.5) * width

        ax.bar(xpos, vals, width=width, color=color, edgecolor="none")
        ax.bar(xpos, vals, width=width, color="none", edgecolor=BAR_EDGE_COLOR)

        for xi, val in zip(xpos, vals):
            ax.text(xi, val + 0.3, f"{val:.0f}%", ha="center", fontsize=12, va="bottom")

    # Legend and axis labels
    legend_handles = [
        Patch(facecolor=ORG_COLORS_10[s], label=s, edgecolor=BAR_EDGE_COLOR)
        for s in ORG_SIZES_10
    ]
    ax.legend(handles=legend_handles, title="Org Size", fontsize=14, title_fontsize=14)

    ax.set_xlabel("Job Category", fontsize=14, fontweight="semibold", labelpad=10)
    ax.set_ylabel("Percentage of Employees", fontsize=14, fontweight="semibold", labelpad=10)
    ax.set_xticks(x)
    ax.set_xticklabels([textwrap.fill(l, width=15, break_long_words=False) for l in job_org_pct.index], fontsize=10, rotation=0, ha="center")
    ax.tick_params(axis='y', labelsize=14)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.set_xlim(-0.5, len(job_org_pct) - 0.5)

    plt.tight_layout()

    # Export Figure
    fig.savefig(f'{output_dir}/figure_10.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Create Table
    fig10_all = (org_size_gender_df[org_size_gender_df['Organizational Size Binned'].isin(ORG_SIZES_10)]
             .groupby(['JobCategory', 'Organizational Size Binned'])['Count'].sum()
             .unstack()[ORG_SIZES_10])

    org_totals_all = fig10_all.sum(axis=0)
    count_order_   = fig10_all.sum(axis=1).sort_values(ascending=False).index

    job_rows = pd.DataFrame({
        'Job Category': count_order_.values,
        **{f'{size} Percentage': (fig10_all.loc[count_order_, size] / org_totals_all[size] * 100).round(0).astype(int).astype(str).values + '%'
           for size in ORG_SIZES_10}
    })
    total_row = pd.DataFrame([{'Job Category': 'Total', **{f'{size} Percentage': '100%' for size in ORG_SIZES_10}}])
    fig10_df = pd.concat([job_rows, total_row], ignore_index=True)

    # Export Table
    fig10_df.to_csv(f'{table_dir}/figure_10_table.csv', index=False)
