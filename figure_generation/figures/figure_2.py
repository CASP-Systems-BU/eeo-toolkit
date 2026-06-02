import pandas as pd
import matplotlib.pyplot as plt
import textwrap
from eeo1_config import RACE_ORDER_5, RACE_COLORS, BAR_EDGE_COLOR

def figure_2(df, output_dir, table_dir):
    race_totals = df[df['Race'].isin(RACE_ORDER_5)].groupby('Race')['Count'].sum()
    race_pct = race_totals / race_totals.sum() * 100
    race_pct = race_pct.reindex(RACE_ORDER_5)

    races   = list(race_pct.index)
    colors  = [RACE_COLORS[r] for r in races]

    fig, ax = plt.subplots(figsize=(11, 6))

    # Race bars — colored fill with grey border, percentage label above each bar
    for i, (race, color, val) in enumerate(zip(races, colors, race_pct.values)):
        ax.bar(race, val, color=color, edgecolor='none', width=0.6)
        ax.bar(race, val, color='none', edgecolor=BAR_EDGE_COLOR, width=0.6)
        ax.text(i, val + 0.3, f"{val:.0f}%", ha="center", va="bottom", fontsize=12)

    # Axis labels and tick formatting
    ax.set_xlabel("Race", fontsize=14, fontweight="semibold", labelpad=10)
    ax.set_ylabel("Percentage", fontsize=14, fontweight="semibold", labelpad=10)
    ax.set_ylim(0, max(race_pct.values) * 1.15)
    ax.set_xticks(range(len(races)))
    ax.set_xticklabels([textwrap.fill(r, width=25) for r in races], ha="center", fontsize=10)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))

    plt.tight_layout()

    # Export Figure
    fig.savefig(f'{output_dir}/figure_2.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Create Table
    fig2_df = pd.DataFrame({
        'Race': races,
        'Percentage': race_pct.values.round(0).astype(int).astype(str) + '%'
    })

    # Export Table
    fig2_df.to_csv(f'{table_dir}/figure_2_table.csv', index=False)