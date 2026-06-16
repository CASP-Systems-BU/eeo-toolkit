"""
This script post-processes differentially private EEO-1 contingency tables.
It expects the outputs of eeo1_dp.py (main.csv and side_*.csv) and produces:
1. An adjusted 4-way main table with non-negative marginals (cvxpy MIP).
2. A CNR side table derived from the adjusted main (no extra epsilon cost).
3. Adjusted 3-way side tables with non-negative marginals (cvxpy MIP).
4. Structural zeroes applied to impossible industry x org-size combinations.
5. Excel workbooks (with and without structural zeroes) for publication.
"""

import os
import pandas as pd
import numpy as np
import cvxpy as cp
from itertools import combinations
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.hyperlink import Hyperlink
from openpyxl.worksheet.table import Table, TableStyleInfo

# Directory containing main.csv and side_*.csv
input_dir = "/home/node0/Documents/csv_output"

# Directory for Excel workbook output
output_dir = "/home/node0/Documents/csv_output"

# Per-cell change budget for the 4-way main table adjustment.
MAX_CELL_CHANGE = 4

# Column renames: DP script output names → publication-format names
PUBLISH_RENAME = {
    'JobCategory':                'Job_Category',
    'Organizational Size Binned': 'Organization_Size',
    'County Name':                'County_Name',
    'Race':                       'Race_Ethnicity',
    'Gender':                     'Sex',
}


# =============================================================================
# 4-way table adjustment helpers
# =============================================================================

def create_consistent_4way_table_integer(df_4way, count_col='Count', use_l1=True):
    """
    Correct a noisy 4-way DP contingency table to enforce non-negativity and
    integer values while minimizing L1 (or L2) error.

    Constraints:
    - All 2-way and 3-way marginals >= 0
    - 1-way marginals == original (exact)
    - Per-cell change <= MAX_CELL_CHANGE
    """
    all_vars = [col for col in df_4way.columns if col != count_col]

    if len(all_vars) != 4:
        raise ValueError(f"Expected 4 categorical columns + 1 count column, "
                         f"but found {len(all_vars)} categorical columns.")

    print(f"Detected categorical columns: {all_vars}")

    categories = {var: sorted(df_4way[var].unique()) for var in all_vars}
    n_cats = {var: len(cats) for var, cats in categories.items()}
    index_map = {var: {cat: i for i, cat in enumerate(cats)}
                 for var, cats in categories.items()}

    print(f"\nDimensions:")
    for var in all_vars:
        print(f"  {var}: {n_cats[var]} categories")
    print(f"  Total 4-way cells: {np.prod(list(n_cats.values()))}")

    shape_4way = tuple(n_cats[var] for var in all_vars)
    X_4way = cp.Variable(shape_4way, integer=True)

    Y_4way = np.zeros(shape_4way)
    for _, row in df_4way.iterrows():
        idx = tuple(index_map[var][row[var]] for var in all_vars)
        Y_4way[idx] = row[count_col]

    print(f"\nInput data statistics:")
    print(f"  Total: {Y_4way.sum():.2f}")
    print(f"  Min: {Y_4way.min():.2f}, Max: {Y_4way.max():.2f}")
    print(f"  Negative cells: {(Y_4way < 0).sum()} out of {Y_4way.size}")

    objective = (cp.Minimize(cp.sum(cp.abs(X_4way - Y_4way))) if use_l1
                 else cp.Minimize(cp.sum_squares(X_4way - Y_4way)))

    constraints = []

    marginal_2way_sets = list(combinations(all_vars, 2))
    for marginal_vars in marginal_2way_sets:
        axes_to_sum = tuple(i for i, v in enumerate(all_vars) if v not in marginal_vars)
        constraints.append(cp.sum(X_4way, axis=axes_to_sum) >= 0)

    marginal_3way_sets = list(combinations(all_vars, 3))
    for marginal_vars in marginal_3way_sets:
        axis_to_sum = next(i for i, v in enumerate(all_vars) if v not in marginal_vars)
        constraints.append(cp.sum(X_4way, axis=axis_to_sum) >= 0)

    for i, var in enumerate(all_vars):
        axes_to_sum = tuple(j for j in range(len(all_vars)) if j != i)
        X_1way = cp.sum(X_4way, axis=axes_to_sum)
        Y_1way = np.sum(Y_4way, axis=axes_to_sum)
        constraints.append(X_1way == Y_1way)

    constraints.append(X_4way >= Y_4way - MAX_CELL_CHANGE)
    constraints.append(X_4way <= Y_4way + MAX_CELL_CHANGE)
    print(f"\nPer-cell change limit: |X - Y| <= {MAX_CELL_CHANGE}")

    problem = cp.Problem(objective, constraints)
    solved = False

    for name, solver in [("CBC", cp.CBC), ("SCIP", cp.SCIP), ("GLPK_MI", cp.GLPK_MI)]:
        try:
            print(f"  Trying {name} solver...")
            problem.solve(solver=solver, verbose=False)
            if problem.status in ["optimal", "optimal_inaccurate"]:
                solved = True
                print(f"  ✓ {name} succeeded!")
                break
        except Exception as e:
            print(f"  {name} not available: {str(e)[:50]}")

    if not solved:
        raise RuntimeError(
            f"No solver succeeded (status: {problem.status}). "
            f"Try increasing MAX_CELL_CHANGE."
        )

    print(f"\n✓ Optimization status: {problem.status}, obj = {problem.value:.2f}")

    X_4way_int = np.round(X_4way.value).astype(int)
    print(f"  Total: {X_4way_int.sum()}, min: {X_4way_int.min()}, "
          f"negative cells: {(X_4way_int < 0).sum()}")

    df_4way_corrected = []
    for idx in np.ndindex(shape_4way):
        row = {var: list(categories[var])[idx[i]] for i, var in enumerate(all_vars)}
        row[count_col] = X_4way_int[idx]
        df_4way_corrected.append(row)
    df_4way_corrected = pd.DataFrame(df_4way_corrected)

    marginals_2way = {
        ''.join(mv): df_4way_corrected.groupby(list(mv))[count_col].sum().reset_index()
        for mv in marginal_2way_sets
    }
    marginals_3way = {
        ''.join(mv): df_4way_corrected.groupby(list(mv))[count_col].sum().reset_index()
        for mv in marginal_3way_sets
    }

    return df_4way_corrected, marginals_2way, marginals_3way


def verify_results(df_corrected, df_original, count_col='Count'):
    """Print a verification report for the 4-way table adjustment."""
    print("\n" + "=" * 70 + "\nVERIFICATION\n" + "=" * 70)
    all_vars = [col for col in df_corrected.columns if col != count_col]

    print(f"\n2-way marginals (must be non-negative):")
    for marginal_vars in combinations(all_vars, 2):
        df_m = df_corrected.groupby(list(marginal_vars))[count_col].sum().reset_index()
        neg = (df_m[count_col] < 0).sum()
        print(f"  {'✓' if neg == 0 else '✗'} {''.join(marginal_vars)}: "
              f"min={df_m[count_col].min()}, negative={neg}")

    print(f"\n3-way marginals (must be non-negative):")
    for marginal_vars in combinations(all_vars, 3):
        df_m = df_corrected.groupby(list(marginal_vars))[count_col].sum().reset_index()
        neg = (df_m[count_col] < 0).sum()
        print(f"  {'✓' if neg == 0 else '✗'} {''.join(marginal_vars)}: "
              f"min={df_m[count_col].min()}, negative={neg}")

    merged = df_original.merge(df_corrected, on=all_vars, suffixes=('_orig', '_corr'))
    cell_deltas = (merged[f'{count_col}_corr'] - merged[f'{count_col}_orig']).abs()
    violations = (cell_deltas > MAX_CELL_CHANGE).sum()
    print(f"\nPer-cell change (limit={MAX_CELL_CHANGE}): "
          f"{'✓' if violations == 0 else '✗'} max={cell_deltas.max()}, violations={violations}")

    print(f"\n1-way marginals (must EXACTLY match original):")
    for var in all_vars:
        orig_m = df_original.groupby(var)[count_col].sum().reset_index()
        corr_m = df_corrected.groupby(var)[count_col].sum().reset_index()
        mm = orig_m.merge(corr_m, on=var, suffixes=('_orig', '_corr'))
        max_diff = (mm[f'{count_col}_orig'] - mm[f'{count_col}_corr']).abs().max()
        print(f"  {'✓' if max_diff == 0 else '✗'} {var}: max deviation = {max_diff}")


# =============================================================================
# 3-way table adjustment helpers
# =============================================================================

def _effective_delta(orig, corr):
    """Asymmetric cost: reaching 0 from a negative cell is free; excess above 0 is charged."""
    return pd.Series(np.where(
        orig >= 0,
        (corr - orig).abs(),
        corr.clip(lower=0),
    ), index=orig.index)


def _print_3way_report(csv_path, df_orig, df_corr, all_vars, count_col,
                       max_cell_change, max_1way, max_2way, solver_used, obj_value):
    orig_neg  = (df_orig[count_col] < 0).sum()
    corr_neg  = (df_corr[count_col] < 0).sum()
    orig_tot  = df_orig[count_col].sum()
    corr_tot  = df_corr[count_col].sum()
    pct_shift = (corr_tot - orig_tot) / orig_tot * 100 if orig_tot else 0

    print(f"\n{'='*60}")
    print(f"  {csv_path}")
    print(f"  Solver : {solver_used}  |  obj = {obj_value:.1f}")
    print(f"  Neg cells : {orig_neg} → {corr_neg}  |  "
          f"total : {orig_tot:.1f} → {corr_tot} ({pct_shift:+.3f}%)")
    print(f"{'='*60}")

    merged    = df_orig.merge(df_corr, on=all_vars, suffixes=('_orig', '_corr'))
    orig_vals = merged[f'{count_col}_orig']
    corr_vals = merged[f'{count_col}_corr']
    merged['eff_change'] = _effective_delta(orig_vals, corr_vals)
    merged['raw_change'] = corr_vals - orig_vals

    changed = (merged[orig_vals != corr_vals]
               .assign(_abs=lambda d: d['raw_change'].abs())
               .sort_values('_abs', ascending=False)
               .drop(columns='_abs')
               .copy())

    print(f"  Cells changed: {len(changed)}")
    if not changed.empty:
        print(changed[all_vars + [f'{count_col}_orig', f'{count_col}_corr',
                                  'raw_change', 'eff_change']]
              .rename(columns={f'{count_col}_orig': 'original',
                               f'{count_col}_corr': 'corrected'})
              .to_string(index=False))

    print()
    for v in all_vars:
        delta  = (df_corr.groupby(v)[count_col].sum() - df_orig.groupby(v)[count_col].sum()).abs()
        status = "✓" if max_1way is None or delta.max() <= max_1way else f"✗ max exceeded ({delta.max()})"
        print(f"  1-way [{v}]: max |Δ| = {delta.max():.0f}  "
              f"(limit={max_1way if max_1way is not None else '—'})  {status}")

    for v0, v1 in combinations(all_vars, 2):
        delta  = (df_corr.groupby([v0, v1])[count_col].sum() - df_orig.groupby([v0, v1])[count_col].sum()).abs()
        status = "✓" if max_2way is None or delta.max() <= max_2way else f"✗ max exceeded ({delta.max()})"
        print(f"  2-way [{v0} × {v1}]: max |Δ| = {delta.max():.0f}  "
              f"(limit={max_2way if max_2way is not None else '—'})  {status}")

    violations = (merged['eff_change'] > max_cell_change).sum()
    print(f"  Cell change (limit={max_cell_change}): "
          f"{'✓' if not violations else f'✗ {violations} violation(s)'}")


def adjust_3way_table(
    csv_path,
    count_col='Count',
    use_l1=True,
    max_cell_change=10,
    max_1way_marginal_change=None,
    max_2way_marginal_change=None,
    output_csv=None,
):
    """
    Correct a noisy 3-way DP contingency table so every cell is non-negative.

    Objective: minimize L1 (or L2) error on the 3-way cells.
    Constraints:
      * All cells >= 0
      * Per-cell budget (asymmetric for originally-negative cells):
          - positive original: |corrected - original| <= max_cell_change
          - negative original: corrected <= max_cell_change (reaching 0 is free)
      * Each 1-way marginal entry may change by at most max_1way_marginal_change
      * Each 2-way marginal entry may change by at most max_2way_marginal_change
    """
    df_3way  = pd.read_csv(csv_path)
    all_vars = [c for c in df_3way.columns if c != count_col]

    if len(all_vars) != 3:
        raise ValueError(
            f"{csv_path}: expected 3 categorical columns + '{count_col}', "
            f"found {len(all_vars)}: {all_vars}"
        )

    categories = {v: sorted(df_3way[v].unique()) for v in all_vars}
    n_cats     = {v: len(c) for v, c in categories.items()}
    index_map  = {v: {cat: i for i, cat in enumerate(cats)} for v, cats in categories.items()}
    shape      = tuple(n_cats[v] for v in all_vars)

    Y = np.zeros(shape)
    for _, row in df_3way.iterrows():
        idx    = tuple(index_map[v][row[v]] for v in all_vars)
        Y[idx] = row[count_col]

    X = cp.Variable(shape, integer=True)
    objective = cp.Minimize(cp.sum(cp.abs(X - Y)) if use_l1 else cp.sum_squares(X - Y))

    upper_bound = np.maximum(Y, 0) + max_cell_change
    lower_bound = Y - max_cell_change
    constraints = [X >= 0, X >= lower_bound, X <= upper_bound]

    if max_1way_marginal_change is not None:
        for i, v in enumerate(all_vars):
            other_axes = tuple(j for j in range(3) if j != i)
            X_1way = cp.sum(X, axis=other_axes)
            Y_1way = np.sum(Y, axis=other_axes)
            constraints += [
                X_1way - Y_1way <= max_1way_marginal_change,
                Y_1way - X_1way <= max_1way_marginal_change,
            ]

    if max_2way_marginal_change is not None:
        for v_pair in combinations(range(3), 2):
            remaining_axis = next(j for j in range(3) if j not in v_pair)
            X_2way = cp.sum(X, axis=remaining_axis)
            Y_2way = np.sum(Y, axis=remaining_axis)
            constraints += [
                X_2way - Y_2way <= max_2way_marginal_change,
                Y_2way - X_2way <= max_2way_marginal_change,
            ]

    problem     = cp.Problem(objective, constraints)
    solved      = False
    solver_used = None

    for name, solver in [("CBC", cp.CBC), ("SCIP", cp.SCIP), ("GLPK_MI", cp.GLPK_MI)]:
        try:
            problem.solve(solver=solver, verbose=False)
            if problem.status in ("optimal", "optimal_inaccurate"):
                solved      = True
                solver_used = name
                break
        except Exception:
            pass

    if not solved:
        raise RuntimeError(
            f"No MIP solver succeeded for {csv_path} (status: {problem.status})."
        )

    X_int = np.round(X.value).astype(int)

    rows = []
    for idx in np.ndindex(shape):
        row            = {v: list(categories[v])[idx[i]] for i, v in enumerate(all_vars)}
        row[count_col] = X_int[idx]
        rows.append(row)
    df_corrected = pd.DataFrame(rows)

    _print_3way_report(
        csv_path, df_3way, df_corrected, all_vars, count_col,
        max_cell_change, max_1way_marginal_change, max_2way_marginal_change,
        solver_used, problem.value,
    )

    if output_csv:
        df_corrected.to_csv(output_csv, index=False)
        print(f"  → saved to {output_csv}")

    return df_corrected


# =============================================================================
# Excel generation helpers
# =============================================================================

def _group(df, col_list, remove_zeros=False):
    """Group by col_list, sum Count, and optionally drop zero rows."""
    result = df.groupby(col_list)['Count'].sum().reset_index()
    return result[result['Count'] != 0] if remove_zeros else result


def _combine(list_of_dfs, col_list):
    """
    Project each side table down to col_list, then take the median Count across
    all frames that contain every column in col_list.  Median is more robust
    to outlier noise than mean (see idea.ipynb for details).
    """
    temp = pd.concat([
        df.groupby(col_list)['Count'].sum().reset_index()
        for df in list_of_dfs
        if all(col in df.columns for col in col_list)
    ]).groupby(col_list)['Count'].median()
    return np.round(temp).astype(int).reset_index()


def write_tables_with_titles(filename, dataframes_dict):
    """Write DataFrames to Excel, each on its own sheet with a title row and a formatted table."""
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        for sheet_name, df in dataframes_dict.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=1)

    wb = load_workbook(filename)

    for sheet_name, df in dataframes_dict.items():
        ws = wb[sheet_name]

        ws['A1'] = sheet_name
        ws['A1'].font = Font(bold=True, size=12)

        max_row = ws.max_row
        max_col = ws.max_column
        tab_ref = f"A2:{get_column_letter(max_col)}{max_row}"

        tab = Table(displayName=sheet_name.replace('-', '_'), ref=tab_ref)
        tab.tableStyleInfo = TableStyleInfo(
            name=None, showFirstColumn=False, showLastColumn=False,
            showRowStripes=True, showColumnStripes=False,
        )
        ws.add_table(tab)

        for row in ws.iter_rows(min_row=1, max_row=max_row, min_col=1, max_col=max_col):
            for cell in row:
                cell.font = Font(
                    name=cell.font.name, size=12,
                    bold=cell.font.bold, italic=cell.font.italic,
                    color=cell.font.color,
                )

        for col in ws.columns:
            letter = get_column_letter(col[0].column)
            max_len = max((len(str(c.value)) for c in col if c.value is not None), default=0)
            ws.column_dimensions[letter].width = min(max_len + 2, 50)

        ws[f'A{max_row + 2}'] = 'End of worksheet'
        ws[f'A{max_row + 2}'].font = Font(size=12)

    wb.save(filename)


def create_about_sheet_eeo1(filename):
    """Prepend an About sheet with a table of contents to an existing EEO-1 workbook."""
    sheet_descriptions = {
        'Category-NAICS-Sex':   'Job Category × NAICS Industry × Gender',
        'Category-Race-Sex':    'Job Category × Race/Ethnicity × Gender',
        'NAICS-Race-Sex':       'NAICS Industry × Race/Ethnicity × Gender',
        'Category-NAICS-Race':  'Job Category × NAICS Industry × Race/Ethnicity',
        'Category-Size-Race':   'Job Category × Organization Size × Race/Ethnicity',
        'Category-Sex-Size':    'Job Category × Gender × Organization Size',
        'Category-County-Race': 'Job Category × County × Race/Ethnicity',
        'Category-County-Sex':  'Job Category × County × Gender',
        'NAICS-Size-Race':      'NAICS Industry × Organization Size × Race/Ethnicity',
        'NAICS-Size-Sex':       'NAICS Industry × Organization Size × Gender',
        'NAICS-County-Race':    'NAICS Industry × County × Race/Ethnicity',
        'NAICS-County-Sex':     'NAICS Industry × County × Gender',
    }

    wb = load_workbook(filename)
    if 'About' in wb.sheetnames:
        del wb['About']
    ws = wb.create_sheet('About', 0)

    ws['A1'] = 'About'
    ws['A1'].font = Font(bold=True, size=14)
    ws['A1'].alignment = Alignment(horizontal='left', vertical='center')

    ws['A2'] = (
        'This data has been collected from EEO-1 reports submitted by Massachusetts employers '
        ' (private employers with 100+ employees) under the Frances Perkins '
        'Workplace Equity Act of 2024. Several steps were taken to protect data and identity of '
        'respondents. These include physical and logical access controls, cryptographically secure '
        'multi-party computation to provide end-to-end data confidentiality, and differential privacy '
        'techniques. In particular, all counts shown in these tables are approximate. '
        ' More information about data security can be found in the methodology section of the '
        'full 2026 Massachusetts Workforce Data Report. A table of contents is below.'
    )
    ws['A2'].font = Font(size=12)
    ws['A2'].alignment = Alignment(wrap_text=True)
    ws.row_dimensions[2].height = 60

    ws['A3'] = 'For more information, visit mass.gov/Workforce2026'
    ws['A3'].font = Font(size=12)

    ws['A4'] = 'Table of Contents'
    ws['A4'].font = Font(bold=True, size=12)

    row = 5
    for sheet_name, description in sheet_descriptions.items():
        ws[f'A{row}'] = sheet_name
        ws[f'A{row}'].font = Font(color='0563C1', underline='single', size=12)
        ws[f'A{row}'].hyperlink = Hyperlink(ref=f'A{row}', location=f"'{sheet_name}'!A1")
        ws[f'B{row}'] = description
        ws[f'B{row}'].font = Font(size=11)
        row += 1

    ws[f'A{ws.max_row + 2}'] = 'End of worksheet'
    ws[f'A{ws.max_row + 2}'].font = Font(size=12)

    ws.column_dimensions['A'].width = 80
    ws.column_dimensions['B'].width = 50

    wb.save(filename)


# =============================================================================
# Step 1: Adjust 4-way main table and derive CNR side table
# =============================================================================

main_df = pd.read_csv(os.path.join(input_dir, "main.csv"))

print("=" * 70)
print(f"Adjusting main table — all 2/3-way marginals >= 0, "
      f"1-way == original, per-cell change <= {MAX_CELL_CHANGE}")
print("=" * 70)

df_corrected, marginals_2way, marginals_3way = create_consistent_4way_table_integer(
    main_df, count_col='Count', use_l1=True
)

verify_results(df_corrected, main_df)

df_corrected.to_csv(os.path.join(input_dir, "main_adj.csv"), index=False)
print(f"\n→ saved to main_adj.csv")

# Derive CNR (JobCategory x NAICS x Race) by marginalizing Gender from main_adj.
# This costs no extra epsilon — it is pure post-processing of the adjusted table.
cnr_df = df_corrected.groupby(['JobCategory', 'NAICS_label', 'Race'])['Count'].sum().reset_index()
cnr_df.to_csv(os.path.join(input_dir, "side_CNR.csv"), index=False)
print(f"→ saved to side_CNR.csv")


# =============================================================================
# Step 2: Adjust each 3-way side table
# =============================================================================

# side_CNR.csv is excluded — it is derived from main_adj so non-negativity is
# already guaranteed; no second cvxpy pass needed.
SIDE_TABLE_CONFIGS = [
    {"files": ["side_GOR.csv", "side_JOG.csv", "side_NOG.csv"], "max_cell_change": 10, "max_1way": 0,   "max_2way": 30},
    {"files": ["side_JCG.csv"],                                  "max_cell_change": 10, "max_1way": 130, "max_2way": 110},
    {"files": ["side_JCR.csv"],                                  "max_cell_change": 10, "max_1way": 310, "max_2way": 150},
    {"files": ["side_JOR.csv"],                                  "max_cell_change": 10, "max_1way": 10,  "max_2way": 85},
    {"files": ["side_NCG.csv"],                                  "max_cell_change": 10, "max_1way": 95,  "max_2way": 120},
    {"files": ["side_NCR.csv"],                                  "max_cell_change": 10, "max_1way": 385, "max_2way": 140},
    {"files": ["side_NOR.csv"],                                  "max_cell_change": 10, "max_1way": 95,  "max_2way": 70},
]

for config in SIDE_TABLE_CONFIGS:
    for filename in config["files"]:
        csv_path = os.path.join(input_dir, filename)
        adjust_3way_table(
            csv_path=csv_path,
            count_col='Count',
            use_l1=True,
            max_cell_change=config["max_cell_change"],
            max_1way_marginal_change=config["max_1way"],
            max_2way_marginal_change=config["max_2way"],
            output_csv=csv_path.replace(".csv", "_adj.csv"),
        )


# =============================================================================
# Step 3: Apply structural zeroes (impossible NAICS × org-size combinations)
# =============================================================================

# Only NOG and NOR are affected: NAICS × Org-Size is the only pair where
# small totals are physically impossible (each org-size tier has a hard
# minimum headcount that some industries can't reach).

nog_df = pd.read_csv(os.path.join(input_dir, "side_NOG_adj.csv"))
nor_df = pd.read_csv(os.path.join(input_dir, "side_NOR_adj.csv"))

rename_dict = {'Organizational Size Binned': 'Organization_Size'}
nog_df.rename(columns=rename_dict, inplace=True)
nor_df.rename(columns=rename_dict, inplace=True)

# Minimum plausible headcount for each org-size tier
org_size_lower_bound = {'Medium': 200, 'Large': 600, 'Very Large': 2500}


def get_disallowed_pairs(df, min_size):
    """Return (NAICS_label, Organization_Size) pairs whose summed Count falls below the tier minimum."""
    totals = df.groupby(["NAICS_label", "Organization_Size"])["Count"].sum()
    pairs = [(n, o) for (n, o), total in totals.items() if total < min_size.get(o, 0)]
    return pd.DataFrame(pairs, columns=["NAICS_label", "Organization_Size"])


print("Disallowed (NAICS, Organization_Size) pairs:")
print(get_disallowed_pairs(nog_df, org_size_lower_bound))

# Impossible industry × org-size combinations — counts redistributed to
# (Wholesale Trade, Very Large), the nearest plausible neighbor, to preserve marginals.
D = {
    ("Agriculture, Forestry, Fishing and Hunting",    "Large"),
    ("Agriculture, Forestry, Fishing and Hunting",    "Medium"),
    ("Agriculture, Forestry, Fishing and Hunting",    "Very Large"),
    ("Arts, Entertainment, and Recreation",           "Very Large"),
    ("Construction",                                  "Large"),
    ("Construction",                                  "Very Large"),
    ("Educational Services",                          "Very Large"),
    ("Mining, Quarrying, and Oil and Gas Extraction", "Large"),
    ("Mining, Quarrying, and Oil and Gas Extraction", "Medium"),
    ("Mining, Quarrying, and Oil and Gas Extraction", "Very Large"),
    ("Other Services (except Public Administration)", "Large"),
    ("Other Services (except Public Administration)", "Very Large"),
    ("Utilities",                                     "Large"),
}

target_n = "Wholesale Trade"
target_o = "Very Large"


def redistribute_disallowed(df, D, target_n, target_o, other_col):
    """
    Zeroize counts for disallowed (NAICS_label, Organization_Size) pairs and
    add those counts to the (target_n, target_o) row with the same other_col value.
    """
    df = df.copy()
    mask = df.apply(lambda row: (row["NAICS_label"], row["Organization_Size"]) in D, axis=1)
    redistributed = df[mask].groupby(other_col)["Count"].sum().reset_index()
    redistributed["NAICS_label"] = target_n
    redistributed["Organization_Size"] = target_o
    df.loc[mask, "Count"] = 0
    for _, row in redistributed.iterrows():
        target_mask = (
            (df["NAICS_label"] == target_n)
            & (df["Organization_Size"] == target_o)
            & (df[other_col] == row[other_col])
        )
        if target_mask.any():
            df.loc[target_mask, "Count"] += row["Count"]
        else:
            df = pd.concat([df, pd.DataFrame([{
                "NAICS_label": target_n,
                "Organization_Size": target_o,
                other_col: row[other_col],
                "Count": row["Count"],
            }])], ignore_index=True)
    return df


nog_structured_df = redistribute_disallowed(nog_df, D, target_n, target_o, "Gender")
nor_structured_df = redistribute_disallowed(nor_df, D, target_n, target_o, "Race")

nog_structured_df.to_csv(os.path.join(input_dir, "side_NOG_adj_structured.csv"), index=False)
nor_structured_df.to_csv(os.path.join(input_dir, "side_NOR_adj_structured.csv"), index=False)
print("→ saved side_NOG_adj_structured.csv and side_NOR_adj_structured.csv")


# =============================================================================
# Step 4: Write Excel workbooks
# =============================================================================

# side_CNR.csv is loaded directly — it was derived from main_adj, no separate adjustment needed
SIDE_FILENAMES = [
    "side_JCG_adj.csv", "side_JCR_adj.csv", "side_JOG_adj.csv", "side_JOR_adj.csv",
    "side_NCG_adj.csv", "side_NCR_adj.csv", "side_GOR_adj.csv", "side_CNR.csv",
    "side_NOG_adj_structured.csv", "side_NOR_adj_structured.csv",
]

# --- Workbook A: remove ALL zero-count rows from every table ---

main_df_pub = pd.read_csv(os.path.join(input_dir, "main_adj.csv"))
main_df_pub.rename(columns=PUBLISH_RENAME, inplace=True)

side_dfs_all = []
for filename in SIDE_FILENAMES:
    df = pd.read_csv(os.path.join(input_dir, filename))
    df.rename(columns=PUBLISH_RENAME, inplace=True)
    side_dfs_all.append(df[df['Count'] != 0])

dataframes_all_zeroes = {
    'Category-NAICS-Sex':   _group(main_df_pub, ['Job_Category', 'NAICS_label', 'Sex'],           remove_zeros=True),
    'Category-Race-Sex':    _group(main_df_pub, ['Job_Category', 'Race_Ethnicity', 'Sex'],         remove_zeros=True),
    'NAICS-Race-Sex':       _group(main_df_pub, ['NAICS_label',  'Race_Ethnicity', 'Sex'],         remove_zeros=True),
    'Category-NAICS-Race':  _combine(side_dfs_all, ['Job_Category', 'NAICS_label',       'Race_Ethnicity']),
    'Category-Size-Race':   _combine(side_dfs_all, ['Job_Category', 'Organization_Size', 'Race_Ethnicity']),
    'Category-Sex-Size':    _combine(side_dfs_all, ['Job_Category', 'Sex',               'Organization_Size']),
    'Category-County-Race': _combine(side_dfs_all, ['Job_Category', 'County_Name',       'Race_Ethnicity']),
    'Category-County-Sex':  _combine(side_dfs_all, ['Job_Category', 'County_Name',       'Sex']),
    'NAICS-Size-Race':      _combine(side_dfs_all, ['NAICS_label',  'Organization_Size', 'Race_Ethnicity']),
    'NAICS-Size-Sex':       _combine(side_dfs_all, ['NAICS_label',  'Organization_Size', 'Sex']),
    'NAICS-County-Race':    _combine(side_dfs_all, ['NAICS_label',  'County_Name',       'Race_Ethnicity']),
    'NAICS-County-Sex':     _combine(side_dfs_all, ['NAICS_label',  'County_Name',       'Sex']),
}

out_all = os.path.join(output_dir, "MA_Workforce_2026_EEO1_remove_all_zeroes.xlsx")
write_tables_with_titles(out_all, dataframes_all_zeroes)
create_about_sheet_eeo1(out_all)
print(f"→ saved {out_all}")

# --- Workbook B: remove only the structural-zeroes rows from NOG and NOR ---

main_df_pub = pd.read_csv(os.path.join(input_dir, "main_adj.csv"))
main_df_pub.rename(columns=PUBLISH_RENAME, inplace=True)

# Structured tables first so index 0 and 1 are NOG and NOR (matching the D mask below)
SIDE_FILENAMES_STRUCTURED = [
    "side_NOG_adj_structured.csv", "side_NOR_adj_structured.csv",
    "side_JCG_adj.csv", "side_JCR_adj.csv", "side_JOG_adj.csv", "side_JOR_adj.csv",
    "side_NCG_adj.csv", "side_NCR_adj.csv", "side_GOR_adj.csv", "side_CNR.csv",
]

side_dfs_structured = []
for filename in SIDE_FILENAMES_STRUCTURED:
    df = pd.read_csv(os.path.join(input_dir, filename))
    df.rename(columns=PUBLISH_RENAME, inplace=True)
    side_dfs_structured.append(df)

# Strip rows whose (NAICS_label, Organization_Size) pair is in D from NOG and NOR only
for i in range(2):
    temp = side_dfs_structured[i]
    mask = ~pd.Series(list(zip(temp['NAICS_label'], temp['Organization_Size']))).isin(D)
    side_dfs_structured[i] = temp[mask.values]

dataframes_structured = {
    'Category-NAICS-Sex':   _group(main_df_pub, ['Job_Category', 'NAICS_label',       'Sex']),
    'Category-Race-Sex':    _group(main_df_pub, ['Job_Category', 'Race_Ethnicity',     'Sex']),
    'NAICS-Race-Sex':       _group(main_df_pub, ['NAICS_label',  'Race_Ethnicity',     'Sex']),
    'Category-NAICS-Race':  _combine(side_dfs_structured, ['Job_Category', 'NAICS_label',       'Race_Ethnicity']),
    'Category-Size-Race':   _combine(side_dfs_structured, ['Job_Category', 'Organization_Size', 'Race_Ethnicity']),
    'Category-Sex-Size':    _combine(side_dfs_structured, ['Job_Category', 'Sex',               'Organization_Size']),
    'Category-County-Race': _combine(side_dfs_structured, ['Job_Category', 'County_Name',       'Race_Ethnicity']),
    'Category-County-Sex':  _combine(side_dfs_structured, ['Job_Category', 'County_Name',       'Sex']),
    'NAICS-Size-Race':      _combine(side_dfs_structured, ['NAICS_label',  'Organization_Size', 'Race_Ethnicity']),
    'NAICS-Size-Sex':       _combine(side_dfs_structured, ['NAICS_label',  'Organization_Size', 'Sex']),
    'NAICS-County-Race':    _combine(side_dfs_structured, ['NAICS_label',  'County_Name',       'Race_Ethnicity']),
    'NAICS-County-Sex':     _combine(side_dfs_structured, ['NAICS_label',  'County_Name',       'Sex']),
}

out_structured = os.path.join(output_dir, "MA_Workforce_2026_EEO1_remove_structured_zeroes.xlsx")
write_tables_with_titles(out_structured, dataframes_structured)
create_about_sheet_eeo1(out_structured)
print(f"→ saved {out_structured}")
