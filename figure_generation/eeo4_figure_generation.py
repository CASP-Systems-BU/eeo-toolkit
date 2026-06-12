import pandas as pd
from eeo4_figure_config import INPUT_DIR, OUTPUT_DIR, TABLE_DIR, apply_style
from figures import (
    figure_14, figure_15, figure_16, figure_17, figure_18, figure_19, figure_20,
    figure_21, figure_22, figure_23, figure_24, figure_25, figure_26, figure_27,
    figure_28, figure_29
)


def load_data():
    return {
        "jrg_df": pd.read_csv(INPUT_DIR / "JRG_all_adj.csv"),
        "wfrg_df": pd.read_csv(INPUT_DIR / "WFRG_all_and_new_adj.csv")
    }


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)

    apply_style()
    data = load_data()

    figure_14(data["jrg_df"], OUTPUT_DIR, TABLE_DIR)
    figure_15(data["jrg_df"], OUTPUT_DIR, TABLE_DIR)
    figure_16(data["jrg_df"], OUTPUT_DIR, TABLE_DIR)
    figure_17(data["wfrg_df"], OUTPUT_DIR, TABLE_DIR)
    figure_18(data["wfrg_df"], OUTPUT_DIR, TABLE_DIR)
    figure_19(data["wfrg_df"], OUTPUT_DIR, TABLE_DIR)
    figure_20(data["wfrg_df"], OUTPUT_DIR, TABLE_DIR)
    figure_21(data["wfrg_df"], OUTPUT_DIR, TABLE_DIR)
    figure_22(data["wfrg_df"], OUTPUT_DIR, TABLE_DIR)
    figure_23(data["wfrg_df"], OUTPUT_DIR, TABLE_DIR)
    figure_24(data["wfrg_df"], OUTPUT_DIR, TABLE_DIR)
    figure_25(data["jrg_df"], OUTPUT_DIR, TABLE_DIR)
    figure_26(data["jrg_df"], OUTPUT_DIR, TABLE_DIR)
    figure_27(data["wfrg_df"], OUTPUT_DIR, TABLE_DIR)
    figure_28(data["wfrg_df"], OUTPUT_DIR, TABLE_DIR)
    figure_29(data["wfrg_df"], OUTPUT_DIR, TABLE_DIR)