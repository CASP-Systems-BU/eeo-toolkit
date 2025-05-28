import matplotlib.pyplot as plt
import csv
import pandas as pd
from matplotlib.ticker import FuncFormatter
import textwrap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import matplotlib.font_manager as fm


font_path = "Montserrat/static/Montserrat-Regular.ttf"
fm.fontManager.addfont(font_path)
# Get the font name (it may not be the filename!)
font_prop = fm.FontProperties(fname=font_path)
font_name = font_prop.get_name()
# Set it globally
plt.rcParams["font.family"] = font_name

# v1
# race_color_map = {
#     "American Indian or Alaska Native": "#D45087",
#     "Asian": "#FFA600",
#     "Black or African American": "#665191",
#     "Hispanic or Latino": "#FF7C43",
#     "Native Hawaiian or Other Pacific Islander": "#2F4B7C",
#     "Two or More Races": "#F95D6A",
#     "White": "#003F5C",
# }

# v2
# race_color_map = {
#     "American Indian or Alaska Native": "#D45087",
#     "Asian": "#665191",
#     "Black or African American": "#FFA600",
#     "Hispanic or Latino": "#FF7C43",
#     "Native Hawaiian or Other Pacific Islander": "#2F4B7C",
#     "Two or More Races": "#F95D6A",
#     "White": "#003F5C",
# }

race_color_map = {
    "American Indian or Alaska Native": "#EF5675",
    "Asian": "#FF764A",
    "Black or African American": "#7A5195",
    "Hispanic or Latino": "#FFA600",
    "Native Hawaiian or Other Pacific Islander": "#003F5C",
    "Two or More Races": "#374c80",
    "White": "#BC5090",
}


race_order = [
    "White",
    "Hispanic or Latino",
    "Asian",
    "Black or African American",
    "Two or More Races",
    "American Indian or Alaska Native",
    "Native Hawaiian or Other Pacific Islander",
]

org_size_order = ["Very Large", "Large", "Medium", "Small"]

gender_color_map = {"Female": "#5c6068", "Male": "#dddddd"}
gender_order = ["Female", "Male"]

output_dir = "./pythonplots"


def figure1():
    labels = []
    sizes = []
    colors = []
    hidden_races = {
        "Native Hawaiian or Other Pacific Islander",
        "American Indian or Alaska Native",
    }

    # Temp dict to collect counts
    race_counts = {}

    # hidden_races = {}
    with open("EEO1/Employee_Distribution_by_Race.csv", "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            race = row["Race"]
            if race not in hidden_races:
                race_counts[race] = race_counts.get(race, 0) + float(row["Count"])

    for race in race_order:
        if race in race_counts:
            labels.append(race)
            sizes.append(race_counts[race])
            colors.append(race_color_map[race])

    explode = [0.05] * len(sizes)

    # Plot pie chart
    plt.figure(1)
    wedges, _, autotexts = plt.pie(
        sizes,
        colors=colors,
        autopct=lambda pct: f"{int(round(pct))}%",
        startangle=90,
        explode=explode,
        pctdistance=1.15,
        textprops={"fontsize": 12},
    )
    plt.legend(
        wedges,
        labels,
        title="Race",
        loc="center left",
        bbox_to_anchor=(1, 0.5),
        fontsize=12,
        title_fontsize=13,
    )
    plt.axis("equal")  # Equal aspect ratio ensures pie is a circle
    plt.savefig(f"{output_dir}/figure1.svg", format="svg", bbox_inches="tight")


def figure2():
    df = pd.read_csv("EEO1/Gender_Race_contingency.csv")

    # Pivot the data by Race and Gender
    pivot_df = df.pivot_table(
        values="Count", index="Race", columns="Gender", aggfunc="sum"
    )

    # Reorder columns according to gender_order
    gender_cols = [g for g in gender_order if g in pivot_df.columns]
    pivot_df = pivot_df[gender_cols]

    # Total count per race
    pivot_df["Total"] = pivot_df.sum(axis=1)

    # Sort races by total count descending
    pivot_df = pivot_df.sort_values(by="Total", ascending=False)

    # Plot grouped bar chart manually to control edge color
    fig, ax = plt.subplots(figsize=(12, 7))
    bar_width = 0.3
    indices = range(len(pivot_df))

    for j, gender in enumerate(gender_cols):
        color = gender_color_map[gender]
        edgecolor = "black" if gender == "Male" else color
        ax.bar(
            [i + j * bar_width for i in indices],
            pivot_df[gender],
            width=bar_width,
            label=gender,
            color=color,
            edgecolor=edgecolor,
            linewidth=1 if gender == "Male" else 0,
        )

    # Add percentage labels above bars
    for i, (idx, row) in enumerate(pivot_df.iterrows()):
        total = row["Total"]
        for j, gender in enumerate(gender_cols):
            value = row[gender]
            pct = f"{round(value / total * 100)}%"
            bar_offset = j * bar_width
            ax.text(
                x=i + bar_offset,
                y=value + 5,
                s=pct,
                ha="center",
                va="bottom",
                fontsize=10,
            )

    # Style the axes and legend
    ax.set_ylabel("")
    ax.set_xticks([i + bar_width * (len(gender_cols) - 1) / 2 for i in indices])
    ax.set_xticklabels(
        [textwrap.fill(label, 10) for label in pivot_df.index],
        rotation=0,
        fontsize=13,
        ha="center",
    )

    legend_patches = [
        plt.Rectangle(
            (0, 0),
            1,
            1,
            facecolor=gender_color_map[g],
            edgecolor="black" if g == "Male" else gender_color_map[g],
            linewidth=1 if g == "Male" else 0,
        )
        for g in gender_cols
    ]
    ax.legend(
        handles=legend_patches,
        labels=gender_cols,
        title="Gender",
        fontsize=12,
        title_fontsize=13,
    )

    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{int(x/1000)}k"))

    plt.tight_layout()
    plt.savefig(f"{output_dir}/figure2.svg", format="svg", bbox_inches="tight")


def figure3():
    df = pd.read_csv("EEO1/Gender_Race_contingency.csv")

    # Filter out hidden races
    hidden_races = {
        "Native Hawaiian or Other Pacific Islander",
        "American Indian or Alaska Native",
    }
    df = df[~df["Race"].isin(hidden_races)]

    # Aggregate by Gender and Race
    grouped = df.groupby(["Gender", "Race"])["Count"].sum().unstack(fill_value=0)

    # Reorder columns according to race_order
    grouped = grouped[[race for race in race_order if race in grouped.columns]]

    # Separate gender data
    female_counts = grouped.loc["Female"]
    male_counts = grouped.loc["Male"]

    # Ensure pie sizes are proportional
    total_female = female_counts.sum()
    total_male = male_counts.sum()
    max_total = max(total_female, total_male)

    radius_female = max(0.3, total_female / max_total)
    radius_male = max(0.3, total_male / max_total)

    fig, axes = plt.subplots(1, 2, figsize=(12, 6))

    # Female Pie
    wedges1, _, autotexts1 = axes[0].pie(
        female_counts,
        labels=None,
        colors=[race_color_map[r] for r in female_counts.index],
        autopct=lambda pct: f"{int(round(pct))}%" if pct > 0 else "",
        startangle=90,
        radius=radius_female,
        pctdistance=1.10,
        explode=[0.05] * len(female_counts),
        textprops={"fontsize": 12},
    )
    axes[0].set_title("Female", fontsize=14)

    # Male Pie
    wedges2, _, autotexts2 = axes[1].pie(
        male_counts,
        labels=None,
        colors=[race_color_map[r] for r in male_counts.index],
        autopct=lambda pct: f"{int(round(pct))}%" if pct > 0 else "",
        startangle=90,
        radius=radius_male,
        pctdistance=1.10,
        explode=[0.05] * len(male_counts),
        textprops={"fontsize": 12},
    )
    axes[1].set_title("Male", fontsize=14)

    # Create shared legend
    handles = [
        Line2D(
            [0],
            [0],
            marker="s",
            linestyle="None",
            markerfacecolor=race_color_map[r],
            markeredgewidth=0,
            markersize=12,
        )
        for r in race_order
        if r in female_counts.index or r in male_counts.index
    ]
    labels = [
        r for r in race_order if r in female_counts.index or r in male_counts.index
    ]

    fig.legend(
        handles,
        labels,
        title="Race",
        loc="lower center",
        ncol=3,
        fontsize=12,
        title_fontsize=13,
        bbox_to_anchor=(0.5, -0.1),
    )

    plt.tight_layout(rect=[0, 0.05, 1, 1])  # Space for legend
    plt.savefig(f"{output_dir}/figure3.svg", format="svg", bbox_inches="tight")

def figure4a():
    data_path = "EEO1/combined_op_split/JobCategory_Race_Gender_conting-Table 1.csv"
    df = pd.read_csv(data_path)

    job_categories = sorted(df["JobCategory"].unique())
    gender_df = (
        df.groupby(["JobCategory", "Gender"])["Count"]
        .sum()
        .reset_index()
        .pivot(index="JobCategory", columns="Gender", values="Count")
        .reindex(job_categories)
        .fillna(0)
    )

    x = range(len(job_categories))
    bar_width = 0.35

    fig, ax = plt.subplots(figsize=(15, 5))
    legend_patches = []

    for i, gender in enumerate(gender_order):
        offsets = [xi + (i - 0.5) * bar_width for xi in x]
        counts = gender_df[gender]
        total = gender_df.sum(axis=1)
        percentages = (counts / total * 100).fillna(0)

        edgecolor = "black" if gender == "Male" else gender_color_map[gender]
        linewidth = 1 if gender == "Male" else 0

        bars = ax.bar(
            offsets,
            counts,
            width=bar_width,
            label=gender,
            color=gender_color_map[gender],
            edgecolor=edgecolor,
            linewidth=linewidth,
        )

        for bar, pct in zip(bars, percentages):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(gender_df.values.max() * 0.01, 5),
                f"{round(pct)}%",
                ha="center",
                va="bottom",
                fontsize=10,
            )

        legend_patches.append(
            plt.Rectangle(
                (0, 0), 1, 1,
                facecolor=gender_color_map[gender],
                edgecolor=edgecolor,
                linewidth=linewidth,
            )
        )

    ax.set_ylabel("Count")
    ax.set_xticks(x)
    ax.set_xticklabels(
        ["\n".join(label.split()) for label in job_categories],
        rotation=0,
        fontsize=11,
        ha="center",
    )
    ax.legend(
        handles=legend_patches,
        labels=gender_order,
        title="Gender",
        fontsize=12,
        title_fontsize=13,
    )
    plt.tight_layout()
    plt.savefig(f"{output_dir}/figure4a.svg", format="svg", bbox_inches="tight")

def figure4b():
    data_path = "EEO1/combined_op_split/JobCategory_Race_Gender_conting-Table 1.csv"
    df = pd.read_csv(data_path)

    shown_races_order = ["Black or African American", "White"]
    job_categories = sorted(df["JobCategory"].unique())

    race_counts_full = (
        df.groupby(["JobCategory", "Race"])["Count"]
        .sum()
        .reset_index()
        .pivot(index="JobCategory", columns="Race", values="Count")
        .reindex(job_categories)
        .fillna(0)
    )
    race_percentages = (race_counts_full.div(race_counts_full.sum(axis=1), axis=0) * 100).fillna(0)
    race_counts = race_counts_full[shown_races_order]
    race_percentages = race_percentages[shown_races_order]

    x = range(len(job_categories))
    bar_width = 0.35

    fig, ax = plt.subplots(figsize=(15, 5))

    for i, race in enumerate(shown_races_order):
        offsets = [xi + (i - 0.5) * bar_width for xi in x]
        counts = race_counts[race]
        percentages = race_percentages[race]

        bars = ax.bar(
            offsets, counts, width=bar_width, label=race, color=race_color_map[race]
        )
        for bar, pct in zip(bars, percentages):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(race_counts.values.max() * 0.01, 5),
                f"{round(pct)}%",
                ha="center",
                va="bottom",
                fontsize=11,
            )

    ax.set_ylabel("Count")
    ax.set_xticks(x)
    ax.set_xticklabels(
        ["\n".join(label.split()) for label in job_categories],
        rotation=0,
        fontsize=11,
        ha="center",
    )
    ax.legend(title="Race", fontsize=12, title_fontsize=13)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/figure4b.svg", format="svg", bbox_inches="tight")

def figure4ab():
    data_path = "EEO1/combined_op_split/JobCategory_Race_Gender_conting-Table 1.csv"
    df = pd.read_csv(data_path)
    
    shown_races_order = ["Black or African American", "White"]
    job_categories = sorted(df["JobCategory"].unique())

    # --- Gender data ---
    gender_df = (
        df.groupby(["JobCategory", "Gender"])["Count"]
        .sum()
        .reset_index()
        .pivot(index="JobCategory", columns="Gender", values="Count")
        .reindex(job_categories)
        .fillna(0)
    )

    # --- Race data: calculate all, then filter ---
    race_counts_full = (
        df.groupby(["JobCategory", "Race"])["Count"]
        .sum()
        .reset_index()
        .pivot(index="JobCategory", columns="Race", values="Count")
        .reindex(job_categories)
        .fillna(0)
    )
    race_percentages = (race_counts_full.div(race_counts_full.sum(axis=1), axis=0) * 100).fillna(0)

    race_counts = race_counts_full[shown_races_order]
    race_percentages = race_percentages[shown_races_order]

    # --- Plotting ---
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)

    x = range(len(job_categories))
    bar_width = 0.35

    # --- Gender bars ---
    legend_patches = []
    for i, gender in enumerate(gender_order):
        offsets = [xi + (i - 0.5) * bar_width for xi in x]
        counts = gender_df[gender]
        total = gender_df.sum(axis=1)
        percentages = (counts / total * 100).fillna(0)

        edgecolor = "black" if gender == "Male" else gender_color_map[gender]
        linewidth = 1 if gender == "Male" else 0

        bars = ax1.bar(
            offsets,
            counts,
            width=bar_width,
            label=gender,
            color=gender_color_map[gender],
            edgecolor=edgecolor,
            linewidth=linewidth,
        )

        for bar, pct in zip(bars, percentages):
            ax1.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(gender_df.values.max() * 0.01, 5),
                f"{round(pct)}%",
                ha="center",
                va="bottom",
                fontsize=10,
            )

        legend_patches.append(
            plt.Rectangle(
                (0, 0),
                1,
                1,
                facecolor=gender_color_map[gender],
                edgecolor=edgecolor,
                linewidth=linewidth,
            )
        )

    ax1.set_ylabel("Count")
    ax1.legend(
        handles=legend_patches,
        labels=gender_order,
        title="Gender",
        fontsize=12,
        title_fontsize=13,
    )

    # --- Race bars ---
    for i, race in enumerate(shown_races_order):
        offsets = [xi + (i - 0.5) * bar_width for xi in x]
        counts = race_counts[race]
        percentages = race_percentages[race]
        bars = ax2.bar(
            offsets, counts, width=bar_width, label=race, color=race_color_map[race]
        )
        for bar, pct in zip(bars, percentages):
            ax2.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(race_counts.values.max() * 0.01, 5),
                f"{round(pct)}%",
                ha="center",
                va="bottom",
                fontsize=11,
            )

    ax2.set_ylabel("Count")
    ax2.set_xticks(x)
    ax2.set_xticklabels(
        ["\n".join(label.split()) for label in job_categories],
        rotation=0,
        fontsize=11,
        ha="center",
    )
    ax2.legend(title="Race", fontsize=12, title_fontsize=13)

    plt.tight_layout(rect=[0, 0.05, 1, 1])
    plt.savefig(f"{output_dir}/figure4ab.svg", format="svg", bbox_inches="tight")

def figure5():
    data_path = "EEO1/Gender_Organizational Size Binned_contingency.csv"
    df = pd.read_csv(data_path)

    # Ensure category order
    df["Organizational Size Binned"] = pd.Categorical(
        df["Organizational Size Binned"], categories=org_size_order, ordered=True
    )

    # Group by ordered org size
    grouped = dict(tuple(df.groupby("Organizational Size Binned")))

    # === Plot Setup ===
    fig, axes = plt.subplots(2, 2, figsize=(5, 5))
    axes = axes.flatten()

    # Find the max total count for scaling
    max_total = max(
        group["Count"].sum() for key, group in grouped.items() if key in org_size_order
    )

    for i, org_size in enumerate(org_size_order):
        ax = axes[i]
        group = grouped.get(org_size)

        if group is None:
            ax.axis("off")
            continue

        # Build values in shown_races_order
        values = [
            (group.loc[group["Gender"] == gender, "Count"].sum())
            for gender in gender_order
        ]

        # Filter out 0 values (i.e., hidden races or zero-count races)
        filtered = [
            (gender, val) for gender, val in zip(gender_order, values) if val > 0
        ]
        labels, counts = zip(*filtered)
        colors = [gender_color_map[gender] for gender in labels]

        # Compute proportional radius
        total = sum(counts)
        radius = 1.0 * (total / max_total)  # Scale relative to max
        radius = max(0.3, radius)  # Prevent too small pies

        # Apply custom pctdistance for smaller orgs
        if org_size in {"Large", "Medium", "Small"}:
            pctdistance = max(1.4, min(1.8, 1.5 + (0.5 - radius)))
        else:
            pctdistance = max(1.25, min(1.6, 1.35 + (0.5 - radius)))

        # pctdistance = max(1.25, min(1.6, 1.35 + (0.5 - radius)))

        wedges, texts, autotexts = ax.pie(
            counts,
            labels=None,
            colors=colors,
            startangle=90,
            radius=radius,
            autopct=lambda pct: f"{int(round(pct))}%" if pct > 0 else "",
            pctdistance=pctdistance,
            textprops={"fontsize": 12},
        )

        ax.set_title(org_size, fontsize=13)

    # Remove any unused axes
    for j in range(len(org_size_order), 4):
        fig.delaxes(axes[j])

    # Shared legend excluding hidden races
    handles = [
        Patch(facecolor=gender_color_map[gender], label=gender)
        for gender in gender_order
    ]
    fig.legend(
        handles=handles,
        loc="lower center",
        ncol=3,
        title="Gender",
        title_fontsize=13,
        bbox_to_anchor=(0.5, -0.05),
        fontsize=12,
    )

    plt.tight_layout(rect=[0, 0.05, 1, 1])  # reserve space for legend
    plt.savefig(f"{output_dir}/figure5.svg", format="svg", bbox_inches="tight")


def figure6():
    data_path = "EEO1/Organizational Size Binned_Race_contingency.csv"
    df = pd.read_csv(data_path)
    hidden_races = {
        "Native Hawaiian or Other Pacific Islander",
        "American Indian or Alaska Native",
    }

    df["Organizational Size Binned"] = pd.Categorical(
        df["Organizational Size Binned"], categories=org_size_order, ordered=True
    )
    grouped = dict(tuple(df.groupby("Organizational Size Binned")))

    fig, axes = plt.subplots(2, 2, figsize=(12, 7))
    axes = axes.flatten()

    max_total = max(
        group["Count"].sum() for key, group in grouped.items() if key in org_size_order
    )

    for i, org_size in enumerate(org_size_order):
        ax = axes[i]
        group = grouped.get(org_size)

        if group is None:
            ax.axis("off")
            continue

        values = [
            (
                group.loc[group["Race"] == race, "Count"].sum()
                if race not in hidden_races
                else 0
            )
            for race in race_order
        ]

        filtered = [(race, val) for race, val in zip(race_order, values) if val > 0]
        labels, counts = zip(*filtered)
        colors = [race_color_map[race] for race in labels]

        total = sum(counts)
        radius = 1.0 * (total / max_total)
        radius = max(0.5, radius)

        if org_size in {"Medium", "Small"}:
            pctdistance = max(1.2, min(1.5, 1.25 + (0.5 - radius)))
        else:
            pctdistance = max(1.15, min(1.45, 1.2 + (0.5 - radius)))

        explode = [0.05] * len(colors)

        wedges, texts, autotexts = ax.pie(
            counts,
            labels=None,
            colors=colors,
            startangle=90,
            radius=radius,
            autopct=lambda pct: f"{int(round(pct))}%" if pct > 0 else "",
            explode=explode,
            pctdistance=pctdistance,
            textprops={"fontsize": 11},
        )

        ax.set_title(org_size, fontsize=13)

    for j in range(len(org_size_order), 4):
        fig.delaxes(axes[j])

    handles = [
        Patch(facecolor=race_color_map[race], label=race)
        for race in race_order
        if race not in hidden_races
    ]
    fig.legend(
        title="Race",
        fontsize=12,
        title_fontsize=13,
        handles=handles,
        loc="lower center",
        ncol=3,
        bbox_to_anchor=(0.5, -0.05),
    )

    plt.tight_layout(rect=[0, 0.05, 1, 1])
    plt.savefig(f"{output_dir}/figure6.svg", format="svg", bbox_inches="tight")


def figure7():
    data_path = "EEO1/combined_op_split/Gender_NAICS_label_contingency-Table 1.csv"
    df = pd.read_csv(data_path)

    # Pivot: Group by NAICS_label and Gender
    pivot_df = df.pivot(index="NAICS_label", columns="Gender", values="Count").fillna(0)

    # Sort NAICS by total count
    pivot_df["Total"] = pivot_df.sum(axis=1)
    pivot_df = pivot_df.sort_values(by="Total", ascending=True).drop(columns="Total")

    pivot_df = pivot_df[
        [gender for gender in gender_order if gender in pivot_df.columns]
    ]

    # --- Dynamically adjust height with more space between labels ---
    n_bars = len(pivot_df)
    row_height = 0.6
    fig_height = max(6, n_bars * row_height)

    # Plot
    fig, ax = plt.subplots(figsize=(12, fig_height))

    # Manual stacked bar plot with border around Male
    left = [0] * len(pivot_df)
    legend_patches = []

    for gender in pivot_df.columns:
        values = pivot_df[gender]
        edgecolor = "black"
        linewidth = 0.5

        bars = ax.barh(
            y=range(len(pivot_df)),
            width=values,
            left=left,
            color=gender_color_map[gender],
            edgecolor=edgecolor,
            linewidth=linewidth,
            label=gender,
        )

        # Update left position for stacking
        left = [l + v for l, v in zip(left, values)]

        # Add to custom legend
        legend_patches.append(
            plt.Rectangle(
                (0, 0),
                1,
                1,
                facecolor=gender_color_map[gender],
                edgecolor=edgecolor,
                linewidth=linewidth,
            )
        )

    # Wrap y-tick labels
    wrapped_labels = [textwrap.fill(label, 30) for label in pivot_df.index]
    ax.set_yticks(range(len(pivot_df)))
    ax.set_yticklabels(wrapped_labels, fontsize=12)

    # Axis labels
    ax.set_ylabel("")
    ax.set_xlabel("Count")

    # Custom legend
    fig.legend(
        handles=legend_patches,
        labels=list(pivot_df.columns),
        title="Gender",
        loc="lower center",
        bbox_to_anchor=(0.5, 0),
        ncol=2,
        fontsize=12,
        title_fontsize=13,
        frameon=True,
    )

    # Layout adjustment
    plt.tight_layout(rect=[0, 0.05, 1, 1])
    plt.savefig(f"{output_dir}/figure7.svg", format="svg", bbox_inches="tight")


def figure8():
    data_path = "EEO1/combined_op_split/NAICS_label_Race_contingency-Table 1.csv"
    df = pd.read_csv(data_path)

    # Pivot the table to have NAICS_label as index, Race as columns
    pivot_df = df.pivot(index="NAICS_label", columns="Race", values="Count").fillna(0)

    # Sort NAICS_labels by total count (ascending)
    pivot_df["Total"] = pivot_df.sum(axis=1)
    pivot_df = pivot_df.sort_values(by="Total", ascending=True).drop(columns="Total")

    # Reorder race columns by desired stack order
    pivot_df = pivot_df[[race for race in race_order if race in pivot_df.columns]]

    # Get corresponding colors
    colors = [race_color_map[race] for race in pivot_df.columns]

    # --- Dynamically adjust height with extra spacing between labels ---
    n_bars = len(pivot_df)
    row_height = 0.6  # Increased for better spacing
    fig_height = max(6, n_bars * row_height)

    # Create figure and axis
    fig, ax = plt.subplots(figsize=(12, fig_height))
    pivot_df.plot(kind="barh", stacked=True, color=colors, ax=ax)

    # Wrap y-axis labels and set font size
    wrapped_labels = [textwrap.fill(label, 30) for label in pivot_df.index]
    ax.set_yticks(range(len(pivot_df)))
    ax.set_yticklabels(wrapped_labels, fontsize=12)

    # Axis labels
    ax.set_xlabel("Count")
    ax.set_ylabel("")

    # Remove automatic legend
    ax.legend_.remove()

    # Custom legend below the chart
    fig.legend(
        title="Race",
        loc="lower center",
        bbox_to_anchor=(0.5, -0.05),
        ncol=3,
        fontsize=12,
        title_fontsize=13,
        frameon=True,
    )

    # Adjust layout to accommodate labels and legend
    plt.tight_layout(rect=[0, 0.08, 1, 1])
    plt.savefig(f"{output_dir}/figure8.svg", format="svg", bbox_inches="tight")


# EEO 5
def figure9():
    data_path = (
        "EEO5/eeo5_contingency_tables_dp-May-1/Employee_Distribution_by_Gender.csv"
    )
    df = pd.read_csv(data_path)
    # Extract data in order
    counts = df["Count"]
    labels = df["Gender"]

    colors = [gender_color_map[g] for g in labels]

    plt.figure(figsize=(6, 6))
    wedges, texts, autotexts = plt.pie(
        counts,
        colors=colors,
        autopct=lambda pct: f"{round(pct)}%",
        startangle=90,
        pctdistance=1.2,  # Push percentages outward
        labeldistance=1.4,  # No labels on wedges themselves
    )

    # Add legend
    plt.legend(
        wedges, labels, title="Gender", loc="center left", bbox_to_anchor=(1, 0.5)
    )

    # Style the percentage texts
    for autotext in autotexts:
        autotext.set_color("black")
        autotext.set_fontsize(10)

    # Title and layout
    plt.axis("equal")
    plt.tight_layout()
    plt.savefig(f"{output_dir}/figure9.svg", format="svg", bbox_inches="tight")


def figure10():
    data_path = (
        "EEO5/eeo5_contingency_tables_dp-May-1/Employee_Distribution_by_Race.csv"
    )
    df = pd.read_csv(data_path)

    # Races to exclude
    hidden_races = {
        "Native Hawaiian or Other Pacific Islander",
    }

    # Filter out hidden races
    df = df[~df["Race"].isin(hidden_races)]

    # Reorder by race_order and drop any not present
    ordered_races = [r for r in race_order if r in df["Race"].values]
    df = df.set_index("Race").loc[ordered_races].reset_index()

    # Extract values
    labels = df["Race"]
    counts = df["Count"]
    colors = [race_color_map[r] for r in labels]
    explode = [0.05] * len(labels)

    # Plot pie chart
    plt.figure(figsize=(7, 7))
    wedges, texts, autotexts = plt.pie(
        counts,
        colors=colors,
        explode=explode,
        autopct=lambda pct: f"{round(pct)}%",
        startangle=90,
        pctdistance=1.20,
        labeldistance=1.45,
    )

    # Add legend
    plt.legend(
        wedges,
        labels,
        title="Race",
        loc="center left",
        bbox_to_anchor=(1, 0.5),
        fontsize=11,
        title_fontsize=12,
        frameon=True,
    )

    # Style the percentage texts
    for autotext in autotexts:
        autotext.set_color("black")
        autotext.set_fontsize(10)

    # Final layout
    plt.axis("equal")
    plt.tight_layout()
    plt.savefig(f"{output_dir}/figure10.svg", format="svg", bbox_inches="tight")


def figure11():
    data_path = (
        "EEO5/eeo5_contingency_tables_dp-May-1/two_way/Gender_Race_contingency.csv"
    )
    df = pd.read_csv(data_path)

    # Pivot: Group by Race and Gender
    pivot_df = df.pivot(index="Race", columns="Gender", values="Count").fillna(0)

    # Sort by total count
    pivot_df["Total"] = pivot_df.sum(axis=1)
    pivot_df = pivot_df.sort_values(by="Total", ascending=True).drop(columns="Total")

    # Keep gender columns in desired order
    pivot_df = pivot_df[
        [gender for gender in gender_order if gender in pivot_df.columns]
    ]

    # Plot
    fig, ax = plt.subplots(figsize=(12, 5))

    # Manual stacked horizontal bars with black border for 'Male'
    left = [0] * len(pivot_df)
    legend_patches = []

    for gender in pivot_df.columns:
        values = pivot_df[gender]
        edgecolor = "black"
        linewidth = 0.5

        bars = ax.barh(
            y=range(len(pivot_df)),
            width=values,
            left=left,
            color=gender_color_map[gender],
            edgecolor=edgecolor,
            linewidth=linewidth,
            label=gender,
        )

        left = [l + v for l, v in zip(left, values)]

        legend_patches.append(
            plt.Rectangle(
                (0, 0), 1, 1,
                facecolor=gender_color_map[gender],
                edgecolor=edgecolor,
                linewidth=linewidth
            )
        )

    # Wrap y-axis labels
    ax.set_yticks(range(len(pivot_df)))
    ax.set_yticklabels(
        [textwrap.fill(label, 20) for label in pivot_df.index],
        fontsize=12,
    )

    # Axis labels
    ax.set_ylabel("")
    ax.set_xlabel("Count", fontsize=12)
    ax.tick_params(axis="x", labelsize=12)

    # Custom legend below chart
    fig.legend(
        handles=legend_patches,
        labels=list(pivot_df.columns),
        title="Gender",
        loc="lower center",
        bbox_to_anchor=(0.5, -0.06),
        ncol=2,
        frameon=True,
        fontsize=12,
        title_fontsize=13,
    )

    # Final layout
    plt.tight_layout(rect=[0, 0.05, 1, 1])
    plt.savefig(f"{output_dir}/figure11.svg", format="svg", bbox_inches="tight")

def figure12():
    data_path = "EEO5/eeo5_contingency_tables_dp-May-1/Employee_Distribution_by_Job Category.csv"
    df = pd.read_csv(data_path)
    # Sort by Count for better visual ordering (optional)
    df = df.sort_values("Count")

    # Compute total and percentage
    total = df["Count"].sum()
    df["Percentage"] = df["Count"] / total * 100

    # Plot
    fig, ax = plt.subplots(figsize=(12, 8))
    bars = ax.barh(df["Job Category"], df["Count"], color="#003F5C")

    # Annotate each bar with the percentage (outside right)
    for bar, percent in zip(bars, df["Percentage"]):
        width = bar.get_width()
        ax.text(
            width + 2,
            bar.get_y() + bar.get_height() / 2,
            f"{round(percent)}%",
            va="center",
            ha="left",
            fontsize=11,
        )

    # Labels and title
    ax.set_xlabel("Count")
    plt.tight_layout()
    plt.savefig(f"{output_dir}/figure12.svg", format="svg", bbox_inches="tight")


def figure13():
    data_path = "EEO5/eeo5_contingency_tables_dp-May-1/two_way/Gender_Job_Category_contingency-corrected.csv"
    df = pd.read_csv(data_path)

    # Pivot: Group by Job Category and Gender
    pivot_df = df.pivot(index="Job Category", columns="Gender", values="Count").fillna(0)

    # Sort Job Categories by total count
    pivot_df["Total"] = pivot_df.sum(axis=1)
    pivot_df = pivot_df.sort_values(by="Total", ascending=True).drop(columns="Total")

    # Ensure gender order
    pivot_df = pivot_df[[gender for gender in gender_order if gender in pivot_df.columns]]

    # Plot manually to add black edge to Male bars
    fig, ax = plt.subplots(figsize=(12, 8))

    left = [0] * len(pivot_df)
    legend_patches = []

    for gender in pivot_df.columns:
        values = pivot_df[gender]
        edgecolor = "black"
        linewidth = 0.5

        ax.barh(
            y=range(len(pivot_df)),
            width=values,
            left=left,
            color=gender_color_map[gender],
            edgecolor=edgecolor,
            linewidth=linewidth,
            label=gender,
        )

        left = [l + v for l, v in zip(left, values)]

        legend_patches.append(
            plt.Rectangle(
                (0, 0), 1, 1,
                facecolor=gender_color_map[gender],
                edgecolor=edgecolor,
                linewidth=linewidth
            )
        )

    # Axis and labels
    ax.set_ylabel("")
    ax.set_xlabel("Count")
    ax.set_yticks(range(len(pivot_df)))
    ax.set_yticklabels(pivot_df.index, fontsize=12)

    # Custom legend
    fig.legend(
        handles=legend_patches,
        labels=list(pivot_df.columns),
        title="Gender",
        loc="lower center",
        bbox_to_anchor=(0.5, 0),
        ncol=2,
        frameon=True,
        fontsize=12,
        title_fontsize=13,
    )

    # Layout
    plt.tight_layout(rect=[0, 0.05, 1, 1])
    plt.savefig(f"{output_dir}/figure13.svg", format="svg", bbox_inches="tight")

def figure13b():
    data_path = "EEO5/eeo5_contingency_tables_dp-May-1/two_way/Gender_Job_Category_contingency-corrected.csv"
    df = pd.read_csv(data_path)

    job_categories_to_plot = {
        "Elementary Classroom Teachers",
        "Principals",
    }

    # Filter for just CatA and CatB
    df = df[df["Job Category"].isin(job_categories_to_plot)]

    # Group by Job Category
    grouped = dict(tuple(df.groupby("Job Category")))

    # Compute max total to scale pie sizes
    max_total = max(group["Count"].sum() for group in grouped.values())

    # === Plot Setup ===
    fig, axes = plt.subplots(
        1, len(job_categories_to_plot), figsize=(6 * len(job_categories_to_plot), 6)
    )
    if len(job_categories_to_plot) == 1:
        axes = [axes]  # Ensure iterable

    for i, job_cat in enumerate(job_categories_to_plot):
        ax = axes[i]
        group = grouped.get(job_cat)

        # Ensure gender order and fill missing with 0
        group = group.set_index("Gender").reindex(gender_order).fillna(0)
        counts = group["Count"].astype(int).tolist()
        labels = group.index.tolist()
        colors = [gender_color_map[g] for g in labels]

        total = sum(counts)
        radius = total / max_total
        radius = max(0.3, radius)  # avoid tiny pies

        pctdistance = max(1.05, min(1.3, 1.1 + (0.5 - radius)))  # adjust label distance

        wedges, texts, autotexts = ax.pie(
            counts,
            labels=None,
            colors=colors,
            startangle=90,
            radius=radius,
            autopct=lambda pct: f"{int(round(pct))}%" if pct > 0 else "",
            pctdistance=pctdistance,
            textprops={"fontsize": 12},
        )

        ax.set_title(f"{job_cat}", fontsize=14)

    # === Shared Legend ===
    handles = [
        Patch(facecolor=gender_color_map[gender], label=gender)
        for gender in gender_order
    ]
    fig.legend(
        handles=handles,
        loc="lower center",
        ncol=len(gender_order),
        title="Gender",
        title_fontsize=13,
        bbox_to_anchor=(0.5, -0.05),
        fontsize=12,
    )

    plt.tight_layout(rect=[0, 0.05, 1, 1])  # reserve space for legend
    plt.savefig(f"{output_dir}/figure13b.svg", format="svg", bbox_inches="tight")


if __name__ == "__main__":
    figure1()
    figure2()
    figure3()
    # figure4ab()
    figure4a()
    figure4b()
    figure5()
    figure6()
    figure7()
    figure8()
    figure9()
    figure10()
    figure11()
    figure12()
    figure13()
    figure13b()
