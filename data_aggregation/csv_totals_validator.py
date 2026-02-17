"""
csv_totals_validator.py

Validates that total columns (both horizontal row totals and vertical column totals)
match the sum of their constituent cells in EEO-4 and EEO-5 JSON data.

This script checks:
1. Row totals: sum of columns 0-13 should equal column 14 (Row Total)
2. Column totals: sum of data rows should equal the Table Total row
3. Grand total: the intersection of row/column totals should be consistent

Usage:
    # Command-line output only (no CSV files):
    python csv_totals_validator.py --form-type eeo4 --input-dir /path/to/json/files

    # With CSV output:
    python csv_totals_validator.py --form-type eeo4 --input-dir /path/to/json/files --csv

    # Show detailed errors in terminal:
    python csv_totals_validator.py --form-type eeo4 --input-dir /path/to/json/files --show-errors
"""

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import pandas as pd

from const import (
    EEO4_TABLE_JOB_CATEGORIES,
    EEO4_TABLE_A_SALARY_RANGES,
    EEO5_COLUMN_NAMES,
    EEO5_TABLE_A_ROW_NAMES,
    EEO5_TABLE_B_ROW_NAMES,
    EEO5_TABLE_C_ROW_NAMES,
)


@dataclass
class ValidationError:
    """Represents a single validation error."""
    filename: str
    function_index: int
    table_name: str
    error_type: str  # 'row_total' or 'column_total'
    row_or_col_index: int
    row_or_col_name: str
    expected: int
    actual: int
    difference: int


@dataclass
class ValidationResult:
    """Holds all validation results for a single file."""
    filename: str
    total_tables_checked: int = 0
    total_rows_checked: int = 0
    total_columns_checked: int = 0
    row_errors: List[ValidationError] = field(default_factory=list)
    column_errors: List[ValidationError] = field(default_factory=list)
    grand_total_errors: List[ValidationError] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return (
            len(self.row_errors) == 0
            and len(self.column_errors) == 0
            and len(self.grand_total_errors) == 0
        )


def get_eeo4_row_names() -> List[str]:
    """Generate EEO-4 Table A row names (job category + salary range)."""
    return [
        f"{cat}, {sal}"
        for cat in EEO4_TABLE_JOB_CATEGORIES[:-1]
        for sal in EEO4_TABLE_A_SALARY_RANGES
    ] + ["Table Total"]


def validate_table(
    table_data: List[List[int]],
    table_name: str,
    row_names: List[str],
    col_names: List[str],
    filename: str,
    function_index: int,
) -> ValidationResult:
    """
    Validate a single table's row and column totals.

    Args:
        table_data: 2D list of integers representing the table
        table_name: Name of the table (e.g., 'table_a')
        row_names: Names for each row
        col_names: Names for each column
        filename: Source filename for error reporting
        function_index: Index of the function report

    Returns:
        ValidationResult with any errors found
    """
    result = ValidationResult(filename=filename)

    if not table_data or len(table_data) == 0:
        return result

    num_rows = len(table_data)
    num_cols = len(table_data[0]) if table_data else 0

    # The last column (index -1 or 14) is the Row Total
    # The last row is the Table Total (column totals)
    total_col_idx = num_cols - 1
    total_row_idx = num_rows - 1

    result.total_tables_checked = 1
    result.total_rows_checked = num_rows
    result.total_columns_checked = num_cols

    # Validate row totals (horizontal sums)
    # For each row, sum columns 0 to (total_col_idx - 1) and compare to column total_col_idx
    for row_idx in range(num_rows):
        row = table_data[row_idx]
        if len(row) < num_cols:
            continue

        data_sum = sum(row[:total_col_idx])
        reported_total = row[total_col_idx]

        if data_sum != reported_total:
            row_name = row_names[row_idx] if row_idx < len(row_names) else f"Row {row_idx}"
            result.row_errors.append(
                ValidationError(
                    filename=filename,
                    function_index=function_index,
                    table_name=table_name,
                    error_type="row_total",
                    row_or_col_index=row_idx,
                    row_or_col_name=row_name,
                    expected=data_sum,
                    actual=reported_total,
                    difference=reported_total - data_sum,
                )
            )

    # Validate column totals (vertical sums)
    # Sum rows 0 to (total_row_idx - 1) for each column and compare to total_row_idx
    for col_idx in range(num_cols):
        data_sum = sum(table_data[row_idx][col_idx] for row_idx in range(total_row_idx))
        reported_total = table_data[total_row_idx][col_idx]

        if data_sum != reported_total:
            col_name = col_names[col_idx] if col_idx < len(col_names) else f"Column {col_idx}"
            result.column_errors.append(
                ValidationError(
                    filename=filename,
                    function_index=function_index,
                    table_name=table_name,
                    error_type="column_total",
                    row_or_col_index=col_idx,
                    row_or_col_name=col_name,
                    expected=data_sum,
                    actual=reported_total,
                    difference=reported_total - data_sum,
                )
            )

    # Validate grand total consistency
    # The cell at (total_row_idx, total_col_idx) should equal:
    # - Sum of all row totals (excluding the grand total itself)
    # - Sum of all column totals (excluding the grand total itself)
    if num_rows > 0 and num_cols > 0:
        grand_total_cell = table_data[total_row_idx][total_col_idx]

        # Sum of row totals (last column, all rows except last)
        sum_of_row_totals = sum(
            table_data[row_idx][total_col_idx] for row_idx in range(total_row_idx)
        )

        # Sum of column totals (last row, all columns except last)
        sum_of_col_totals = sum(table_data[total_row_idx][:total_col_idx])

        if sum_of_row_totals != grand_total_cell:
            result.grand_total_errors.append(
                ValidationError(
                    filename=filename,
                    function_index=function_index,
                    table_name=table_name,
                    error_type="grand_total_row_sum",
                    row_or_col_index=-1,
                    row_or_col_name="Grand Total (from row totals)",
                    expected=sum_of_row_totals,
                    actual=grand_total_cell,
                    difference=grand_total_cell - sum_of_row_totals,
                )
            )

        if sum_of_col_totals != grand_total_cell:
            result.grand_total_errors.append(
                ValidationError(
                    filename=filename,
                    function_index=function_index,
                    table_name=table_name,
                    error_type="grand_total_col_sum",
                    row_or_col_index=-1,
                    row_or_col_name="Grand Total (from col totals)",
                    expected=sum_of_col_totals,
                    actual=grand_total_cell,
                    difference=grand_total_cell - sum_of_col_totals,
                )
            )

    return result


def validate_eeo4_json(json_path: str) -> List[ValidationResult]:
    """Validate an EEO-4 JSON file."""
    results = []
    col_names = EEO5_COLUMN_NAMES  # Same column structure
    table_a_row_names = get_eeo4_row_names()

    with open(json_path) as f:
        data = json.load(f)

    filename = data.get("filename", os.path.basename(json_path))
    function_reports = data.get("function_reports", [])

    for func_idx, report in enumerate(function_reports):
        # Validate Table A (Full-time staff with salary ranges)
        table_a = report.get("table_a", [])
        if table_a:
            result = validate_table(
                table_data=table_a,
                table_name="table_a (Full-time)",
                row_names=table_a_row_names,
                col_names=col_names,
                filename=filename,
                function_index=func_idx,
            )
            results.append(result)

        # Validate Table B (Part-time staff)
        table_b = report.get("table_b", [])
        if table_b:
            result = validate_table(
                table_data=table_b,
                table_name="table_b (Part-time)",
                row_names=EEO4_TABLE_JOB_CATEGORIES,
                col_names=col_names,
                filename=filename,
                function_index=func_idx,
            )
            results.append(result)

        # Validate Table C (New hires)
        table_c = report.get("table_c", [])
        if table_c:
            result = validate_table(
                table_data=table_c,
                table_name="table_c (New hires)",
                row_names=EEO4_TABLE_JOB_CATEGORIES,
                col_names=col_names,
                filename=filename,
                function_index=func_idx,
            )
            results.append(result)

    return results


def validate_eeo5_json(json_path: str) -> List[ValidationResult]:
    """Validate an EEO-5 JSON file."""
    results = []
    col_names = EEO5_COLUMN_NAMES

    with open(json_path) as f:
        data = json.load(f)

    filename = data.get("filename", os.path.basename(json_path))

    # EEO-5 structure may differ - adapt based on actual structure
    # Assuming similar structure with table_a, table_b, table_c
    for table_key, row_names in [
        ("table_a", EEO5_TABLE_A_ROW_NAMES),
        ("table_b", EEO5_TABLE_B_ROW_NAMES),
        ("table_c", EEO5_TABLE_C_ROW_NAMES),
    ]:
        table_data = data.get(table_key, [])
        if table_data:
            result = validate_table(
                table_data=table_data,
                table_name=table_key,
                row_names=row_names,
                col_names=col_names,
                filename=filename,
                function_index=0,
            )
            results.append(result)

    return results


def get_files_in_directory(directory: str, extension: str = "json") -> List[str]:
    """Get all files with given extension in directory."""
    files = []
    for f in os.listdir(directory):
        if f.endswith(f".{extension}"):
            files.append(f)
    return sorted(files)


def errors_to_dataframe(all_results: List[ValidationResult]) -> pd.DataFrame:
    """Convert validation errors to a DataFrame for CSV export."""
    rows = []

    for result in all_results:
        for error in result.row_errors + result.column_errors + result.grand_total_errors:
            rows.append({
                "filename": error.filename,
                "function_index": error.function_index,
                "table": error.table_name,
                "error_type": error.error_type,
                "row_or_col_index": error.row_or_col_index,
                "row_or_col_name": error.row_or_col_name,
                "expected_sum": error.expected,
                "actual_total": error.actual,
                "difference": error.difference,
            })

    return pd.DataFrame(rows)


def summary_to_dataframe(all_results: List[ValidationResult]) -> pd.DataFrame:
    """Create a summary DataFrame of validation results per file."""
    rows = []

    # Group by filename
    from collections import defaultdict
    by_file: Dict[str, List[ValidationResult]] = defaultdict(list)
    for result in all_results:
        by_file[result.filename].append(result)

    for filename, results in by_file.items():
        total_row_errors = sum(len(r.row_errors) for r in results)
        total_col_errors = sum(len(r.column_errors) for r in results)
        total_grand_errors = sum(len(r.grand_total_errors) for r in results)
        tables_checked = sum(r.total_tables_checked for r in results)

        rows.append({
            "filename": filename,
            "tables_checked": tables_checked,
            "row_total_errors": total_row_errors,
            "column_total_errors": total_col_errors,
            "grand_total_errors": total_grand_errors,
            "total_errors": total_row_errors + total_col_errors + total_grand_errors,
            "status": "PASS" if (total_row_errors + total_col_errors + total_grand_errors) == 0 else "FAIL",
        })

    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(
        description="Validate EEO form totals (row and column sums)"
    )
    parser.add_argument(
        "--form-type",
        choices=["eeo4", "eeo5"],
        required=True,
        help="Type of EEO form to validate",
    )
    parser.add_argument(
        "--input-dir",
        required=True,
        help="Directory containing JSON files to validate",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory to write validation report CSVs (default: same as input-dir)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed validation progress",
    )
    parser.add_argument(
        "--csv",
        action="store_true",
        help="Save results to CSV files (default: command-line output only)",
    )
    parser.add_argument(
        "--show-errors",
        action="store_true",
        help="Show detailed error list in terminal output",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Max number of errors to show with --show-errors (default: 20, use 0 for all)",
    )
    parser.add_argument(
        "--counts-only",
        action="store_true",
        help="Only show error counts (minimal output)",
    )

    args = parser.parse_args()

    if not os.path.isdir(args.input_dir):
        print(f"Error: Input directory does not exist: {args.input_dir}")
        sys.exit(1)

    output_dir = args.output_dir or args.input_dir

    # Get JSON files
    json_files = get_files_in_directory(args.input_dir, "json")
    if not json_files:
        print(f"No JSON files found in {args.input_dir}")
        sys.exit(0)

    print(f"Found {len(json_files)} JSON file(s) to validate")

    # Validate each file
    all_results: List[ValidationResult] = []
    validator_func = validate_eeo4_json if args.form_type == "eeo4" else validate_eeo5_json

    for json_file in json_files:
        json_path = os.path.join(args.input_dir, json_file)
        if args.verbose:
            print(f"Validating: {json_file}")

        try:
            results = validator_func(json_path)
            all_results.extend(results)
        except Exception as e:
            print(f"Error validating {json_file}: {e}")

    # Generate reports
    summary_df = summary_to_dataframe(all_results)
    errors_df = errors_to_dataframe(all_results)

    # Handle case where no files were successfully validated
    if summary_df.empty:
        print("\nError: No files could be validated. Check that you're using the correct directory.")
        print("Expected: Filtered JSON files (e.g., from filter_output_test/)")
        print("Not: Raw OCR JSON files (e.g., from output_eeo4/json/)")
        sys.exit(1)

    # Calculate stats
    total_files = len(summary_df)
    passed_files = len(summary_df[summary_df["status"] == "PASS"])
    failed_files = total_files - passed_files

    row_errors = len(errors_df[errors_df['error_type'] == 'row_total']) if not errors_df.empty else 0
    col_errors = len(errors_df[errors_df['error_type'] == 'column_total']) if not errors_df.empty else 0
    grand_errors = len(errors_df[errors_df['error_type'].str.startswith('grand_total')]) if not errors_df.empty else 0
    total_errors = len(errors_df)

    # Counts-only output
    if args.counts_only:
        if total_errors == 0:
            print(f"OK: {total_files} files, 0 errors")
        else:
            print(f"ERRORS: {total_errors} total (row: {row_errors}, col: {col_errors}, grand: {grand_errors})")
        sys.exit(1 if failed_files > 0 else 0)

    # Print summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    print(f"Files validated: {total_files}")
    print(f"Files passed:    {passed_files}")
    print(f"Files failed:    {failed_files}")

    if not errors_df.empty:
        print(f"\nTotal errors found: {total_errors}")
        print(f"  - Row total mismatches:    {row_errors}")
        print(f"  - Column total mismatches: {col_errors}")
        print(f"  - Grand total mismatches:  {grand_errors}")

    # Print per-file summary
    print("\n" + "-" * 60)
    print("PER-FILE RESULTS")
    print("-" * 60)
    for _, row in summary_df.iterrows():
        status_icon = "PASS" if row["status"] == "PASS" else "FAIL"
        print(f"[{status_icon}] {row['filename']}")
        if row["total_errors"] > 0:
            print(f"       Tables: {row['tables_checked']}, Errors: {row['total_errors']} "
                  f"(row: {row['row_total_errors']}, col: {row['column_total_errors']}, grand: {row['grand_total_errors']})")

    # Show detailed errors if requested
    if args.show_errors and not errors_df.empty:
        print("\n" + "-" * 60)
        print("ERROR DETAILS")
        print("-" * 60)

        display_errors = errors_df if args.limit == 0 else errors_df.head(args.limit)

        for _, err in display_errors.iterrows():
            diff_str = f"+{err['difference']}" if err['difference'] > 0 else str(err['difference'])
            print(f"  {err['filename']} | func={err['function_index']} | {err['table']}")
            print(f"    {err['error_type']}: {err['row_or_col_name']}")
            print(f"    Expected: {err['expected_sum']}, Got: {err['actual_total']} ({diff_str})")
            print()

        if args.limit > 0 and len(errors_df) > args.limit:
            print(f"  ... and {len(errors_df) - args.limit} more errors (use --limit 0 to show all)")

    # Save reports only if --csv flag is used
    if args.csv:
        summary_path = os.path.join(output_dir, f"{args.form_type}_validation_summary.csv")
        summary_df.to_csv(summary_path, index=False)
        print(f"\nSummary saved to: {summary_path}")

        if not errors_df.empty:
            errors_path = os.path.join(output_dir, f"{args.form_type}_validation_errors.csv")
            errors_df.to_csv(errors_path, index=False)
            print(f"Errors saved to:  {errors_path}")
    elif not errors_df.empty:
        print("\nTip: Use --csv to save detailed results to CSV files")
        print("     Use --show-errors to see error details in terminal")

    if errors_df.empty:
        print("\nAll totals match!")

    # Exit with error code if any failures
    sys.exit(1 if failed_files > 0 else 0)


if __name__ == "__main__":
    main()
