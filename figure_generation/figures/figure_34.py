import textwrap
import pandas as pd
import matplotlib.pyplot as plt
from eeo5_figure_config import BAR_EDGE_COLOR, FEMALE_COLOR, MALE_COLOR, AGENT_TYPE_ORDER


def figure_34(twg_df, output_dir, table_dir):
    fig34_df = (twg_df.groupby(['Type of Agent', 'Gender'])['Count'].sum()
                .unstack()[['Female', 'Male']].reindex(AGENT_TYPE_ORDER))
    fig34_pct = fig34_df.div(fig34_df.sum(axis=1), axis=0) * 100

    agents     = list(fig34_pct.index)
    n          = len(agents)
    bar_height = 0.6
    y_gap      = 1.2

    fig, ax = plt.subplots(figsize=(10, n * y_gap * 0.75 + 1))

    for i, agent in enumerate(agents):
        y  = (n - 1 - i) * y_gap
        fp = fig34_pct.loc[agent, 'Female']
        mp = fig34_pct.loc[agent, 'Male']

        ax.barh(y, fp, color=FEMALE_COLOR, edgecolor='none', height=bar_height)
        ax.barh(y, fp, color='none', edgecolor=BAR_EDGE_COLOR, height=bar_height)
        ax.barh(y, mp, left=fp, color=MALE_COLOR, edgecolor='none', height=bar_height)
        ax.barh(y, mp, left=fp, color='none', edgecolor=BAR_EDGE_COLOR, height=bar_height)

        ax.text(2,  y - bar_height / 2 - 0.08, f'{fp:.0f}%', ha='center', va='top', fontsize=12)
        ax.text(98, y - bar_height / 2 - 0.08, f'{mp:.0f}%', ha='center', va='top', fontsize=12)
        ax.text(-2, y, textwrap.fill(agent, width=22), ha='right', va='center', fontsize=13)

    top_y = (n - 1) * y_gap
    ax.text(0.5,  top_y + bar_height / 2 + 0.08, 'Female', ha='left',  va='bottom', fontsize=14, fontweight='medium')
    ax.text(99.5, top_y + bar_height / 2 + 0.08, 'Male',   ha='right', va='bottom', fontsize=14, fontweight='medium')

    ax.set_xlim(-30, 100.3)
    ax.set_ylim(-y_gap * 0.65, top_y + y_gap * 0.55)
    ax.axis('off')

    plt.tight_layout()

    # Export Figure
    fig.savefig(f'{output_dir}/figure_34.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Create Table
    total    = fig34_df.sum(axis=1)
    fig34_df = pd.DataFrame({
        'Agent Type':        fig34_df.index.values,
        'Female Percentage': (fig34_df['Female'].values / total.values * 100).round(0).astype(int).astype(str) + '%',
        'Male Percentage':   (fig34_df['Male'].values   / total.values * 100).round(0).astype(int).astype(str) + '%',
    })
    # Export Table
    fig34_df.to_csv(f'{table_dir}/figure_34_table.csv', index=False)
