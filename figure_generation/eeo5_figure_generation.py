import pandas as pd
from eeo5_figure_config import INPUT_DIR, OUTPUT_DIR, TABLE_DIR, apply_style
from figures import (
    figure_30, figure_31, figure_32, figure_33, figure_34, figure_35,
    figure_36, figure_37, figure_38, figure_39, figure_40, figure_41,
)


def load_data():
    return {
        "jrg_df":  pd.read_csv(INPUT_DIR / "JRG_adj.csv"),
        "wcrg_df": pd.read_csv(INPUT_DIR / "WCRG_adj.csv"),
        "twg_df":  pd.read_csv(INPUT_DIR / "TWG_adj.csv"),
        "twr_df":  pd.read_csv(INPUT_DIR / "TWR_adj.csv"),
    }


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)

    apply_style()
    data = load_data()

    figure_30(data["jrg_df"],  OUTPUT_DIR, TABLE_DIR)
    figure_31(data["jrg_df"],  OUTPUT_DIR, TABLE_DIR)
    figure_32(data["jrg_df"],  OUTPUT_DIR, TABLE_DIR)
    figure_33(data["twg_df"],  OUTPUT_DIR, TABLE_DIR)
    figure_34(data["twg_df"],  OUTPUT_DIR, TABLE_DIR)
    figure_35(data["twr_df"],  OUTPUT_DIR, TABLE_DIR)
    figure_36(data["twg_df"],  OUTPUT_DIR, TABLE_DIR)
    figure_37(data["wcrg_df"], OUTPUT_DIR, TABLE_DIR)
    figure_38(data["jrg_df"],  OUTPUT_DIR, TABLE_DIR)
    figure_39(data["jrg_df"],  OUTPUT_DIR, TABLE_DIR)
    figure_40(data["wcrg_df"], OUTPUT_DIR, TABLE_DIR)
    figure_41(data["jrg_df"],  OUTPUT_DIR, TABLE_DIR)
