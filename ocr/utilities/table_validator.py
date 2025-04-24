"""
table_validator.py

This module provides functions to validate tabular data extracted from EEO-1 and EEO-5 forms.
The primary goal is to check whether row and column totals match their expected values.
It also includes tolerance mechanisms for handling OCR uncertainty using confidence scores.

---

Key Features:
- Row and column validation with expected totals
- Correction logic when one low-confidence cell is likely to cause a mismatch
- Support for both EEO-1 and EEO-5 table formats
- Utility to update the grand total cell when intermediate sums are valid
"""

from typing import List, Tuple
import pandas as pd


def table_validator(
    form_type: str, data: List[List[int]], confidence_table: List[List[float]]
) -> Tuple[List[bool], List[bool]]:
    """
    Main validation function to check both rows and columns.

    Args:
        form_type (str): Either 'eeo1' or 'eeo5'.
        data (List[List[int]]): Table of values from OCR.
        confidence_table (List[List[float]]): Corresponding confidence scores.

    Returns:
        Tuple[List[bool], List[bool]]: Booleans for row and column validity.
    """
    is_row_valid = row_validator_with_correction(form_type, data, confidence_table)
    is_col_valid = column_validator(form_type, data)
    return is_row_valid, is_col_valid


def column_validator(form_type: str, data: List[List[int]]) -> List[bool]:
    """
    Validate that each column sum matches the reported total.

    Args:
        form_type (str): 'eeo1' or 'eeo5'.
        data (List[List[int]]): Table content.

    Returns:
        List[bool]: Validity of each column.
    """
    df = pd.DataFrame(data)
    isValid = [False for _ in range(len(df.columns))]
    h, w = len(data), len(data[0])

    for col in df.columns:
        if form_type == "eeo1":
            total = df.loc[0 : h - 3, col].sum()
            target = df.loc[h - 2, col]
        elif form_type == "eeo5":
            total = df.loc[0 : h - 2, col].sum()
            target = df.loc[h - 1, col]
        else:
            continue

        if total == target:
            isValid[int(col)] = True

    return isValid


def row_validator_with_correction(
    form_type: str, data: List[List[int]], confidence_table: List[List[float]]
) -> List[bool]:
    """
    Validate that each row sum matches the reported total, with correction if one low-confidence cell is off.

    Args:
        form_type (str): 'eeo1' or 'eeo5'.
        data (List[List[int]]): Table content.
        confidence_table (List[List[float]]): Cell confidence levels.

    Returns:
        List[bool]: Row validity list.
    """
    df = pd.DataFrame(data)
    isValid = [False for _ in range(len(df.index))]
    h, w = len(data), len(data[0])

    for row_index in df.index:
        total = df.loc[row_index, 0 : w - 2].sum()
        target = df.loc[row_index, w - 1]

        if total == target:
            isValid[int(row_index)] = True
        else:
            conf_row = confidence_table[row_index]
            low_conf_indices = [i for i, conf in enumerate(conf_row) if conf < 0.7]

            if len(low_conf_indices) == 1:
                low_conf_index = low_conf_indices[0]

                # Try correcting the low-confidence value
                if low_conf_index != w - 1:
                    rest_sum = (
                        sum(data[row_index][:-1]) - data[row_index][low_conf_index]
                    )
                    new_value = data[row_index][-1] - rest_sum
                    data[row_index][low_conf_index] = new_value
                else:
                    data[row_index][low_conf_index] = sum(data[row_index][:-1])

                isValid[int(row_index)] = True

    return isValid


def row_validator(data: List[List[int]]) -> List[bool]:
    """
    Validate rows without correction logic.

    Args:
        data (List[List[int]]): Table content.

    Returns:
        List[bool]: Row validity.
    """
    df = pd.DataFrame(data)
    isValid = [False for _ in range(len(df.index))]

    for row_index in df.index:
        total = df.loc[row_index, 0:13].sum()
        target = df.loc[row_index, 14]
        if total == target:
            isValid[int(row_index)] = True

    return isValid


def update_total(data: List[List[int]]) -> bool:
    """
    Update the grand total cell if intermediate row and column totals agree.

    Args:
        data (List[List[int]]): Table content.

    Returns:
        bool: True if update succeeded, False otherwise.
    """
    df = pd.DataFrame(data)
    h, w = len(data), len(data[0])
    sum1 = df.iloc[0 : h - 3, -1].sum()
    sum2 = df.iloc[h - 2, 0 : w - 1].sum()

    if sum1 == sum2:
        data[-2][-1] = sum1
        return True

    return False
