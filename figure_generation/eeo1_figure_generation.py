import pandas as pd
from eeo1_figure_config import INPUT_DIR, OUTPUT_DIR, TABLE_DIR, apply_style
from figures import (
    figure_1, figure_2, figure_3, figure_4, figure_5, figure_6, figure_7,
    figure_8, figure_9, figure_10, figure_11, figure_12, figure_13
)


def load_data():
    return {
        "main": pd.read_csv(INPUT_DIR / "main_adj.csv"),
        "org_size_gender": pd.read_csv(INPUT_DIR / "side_JOG_adj.csv"),
        "org_size_race": pd.read_csv(INPUT_DIR / "side_JOR_adj.csv"),
    }


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)

    apply_style()
    data = load_data()

    figure_1(data["main"], OUTPUT_DIR, TABLE_DIR)
    figure_2(data["main"], OUTPUT_DIR, TABLE_DIR)
    figure_3(data["main"], OUTPUT_DIR, TABLE_DIR)
    figure_4(data["main"], OUTPUT_DIR, TABLE_DIR)
    figure_5(data["main"], OUTPUT_DIR, TABLE_DIR)
    figure_6(data["main"], OUTPUT_DIR, TABLE_DIR)
    figure_7(data["main"], OUTPUT_DIR, TABLE_DIR)
    figure_8(data["org_size_gender"], OUTPUT_DIR, TABLE_DIR)
    figure_9(data["org_size_race"], OUTPUT_DIR, TABLE_DIR)
    figure_10(data["org_size_gender"], OUTPUT_DIR, TABLE_DIR)
    figure_11(data["main"], OUTPUT_DIR, TABLE_DIR)
    figure_12(data["main"], OUTPUT_DIR, TABLE_DIR)
    figure_13(data["main"], OUTPUT_DIR, TABLE_DIR)