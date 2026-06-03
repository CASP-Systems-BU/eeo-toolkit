import pandas as pd
import matplotlib.pyplot as plt
from eeo4_config import BAR_EDGE_COLOR, FEMALE_COLOR, MALE_COLOR

def figure_14(jrg_df, output_dir, table_dir):
    gender_totals = jrg_df.groupby('Gender')['Count'].sum()
    gender_pct = gender_totals / gender_totals.sum() * 100
    female_pct = gender_pct['Female']
    male_pct   = gender_pct['Male']

    fig, ax = plt.subplots(figsize=(10, 2))

    # Female segment (left)
    ax.barh(0, female_pct, color=FEMALE_COLOR, edgecolor='none', height=0.6)
    ax.barh(0, female_pct, color='none', edgecolor=BAR_EDGE_COLOR, height=0.6)

    # Male segment (right)
    ax.barh(0, male_pct, left=female_pct, color=MALE_COLOR, edgecolor='none', height=0.6)
    ax.barh(0, male_pct, left=female_pct, color='none', edgecolor=BAR_EDGE_COLOR, height=0.6)

    # Labels at left/right ends above bar
    ax.text(0.5, 0.35, 'Female', ha='left', va='bottom', fontsize=16, fontweight='medium')
    ax.text(99.5, 0.35, 'Male', ha='right', va='bottom', fontsize=16, fontweight='medium')

    # Bold percentages below the bar
    ax.text(4, -0.4, f'{female_pct:.0f}%', ha='center', va='top', fontsize=16, color='black')
    ax.text(96, -0.4, f'{male_pct:.0f}%', ha='center', va='top', fontsize=16, color='black')

    ax.set_xlim(-0.3, 100.3)
    ax.set_ylim(-0.65, 0.75)
    ax.axis('off')

    # Export Figure
    fig.savefig(f'{output_dir}/figure_14.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Create Table
    fig14_df = pd.DataFrame({
        'Sex':        ['Female', 'Male'],
        'Percentage': [gender_totals['Female'] / gender_totals.sum(),
                       gender_totals['Male']   / gender_totals.sum()]
    })
    fig14_df['Percentage'] = (fig14_df['Percentage'] * 100).round(0).astype(int).astype(str) + '%'

    # Export Table
    fig14_df.to_csv(f'{table_dir}/figure_14_table.csv', index=False)
