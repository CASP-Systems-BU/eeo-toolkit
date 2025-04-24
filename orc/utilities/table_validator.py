import pandas as pd
from typing import List, Tuple


def table_validator(
    form_type: str, data: List[List[int]], confidence_table: List[List[float]]
) -> Tuple[List[bool], List[bool]]:
    """
    Validate EEO1 Section H Table:
    - Validate the sum of each row
    - Validate the sum of each column
    """
    is_row_valid = row_validator_with_correction(form_type, data, confidence_table)
    is_col_valid = column_validator(form_type, data)

    return is_row_valid, is_col_valid


def column_validator(form_type: str, data: List[List[int]]) -> List[bool]:
    """
    Validate the sum of each column
    Attention: The last element of each column is the total value from the last year.
    Currently, there is not a strictly confident approach to validate the element.
    """
    df = pd.DataFrame(data)
    isValid = [False for _ in range(len(df.columns))]
    h, w = len(data), len(data[0])
    for col in df.columns:
        if form_type == "eeo1":
            total = df.loc[0:h-3, col].sum()
            target = df.loc[h-2, col]
            if total == target:
                isValid[int(col)] = True
        elif form_type == "eeo5":
            total = df.loc[0:h - 2, col].sum()
            target = df.loc[h - 1, col]
            if total == target:
                isValid[int(col)] = True
    return isValid


def row_validator_with_correction(
    form_type: str, data: List[List[int]], confidence_table: List[List[float]]
) -> List[bool]:
    """
    Validate the sum of each row

    Attention: The last row is the total value from the last year.
    The current approach to validate the last row is to compare the sum of the first 9 rows with the sum of the last row.
    If the checksum does not pass and there is only one element whose confidence score < 0.9, then we can update the score.
    """
    df = pd.DataFrame(data)
    isValid = [False for _ in range(len(df.index))]
    h, w = len(data), len(data[0])
    for row_index in df.index:
        total = df.loc[row_index, 0:w-2].sum()
        target = df.loc[row_index, w-1]
        if total == target:
            isValid[int(row_index)] = True

        if not isValid[int(row_index)]:
            conf_row = confidence_table[row_index]
            low_conf_indices = [i for i, conf in enumerate(conf_row) if conf < 0.7]
            if len(low_conf_indices) == 1:
                low_conf_index = low_conf_indices[0]
                if low_conf_index != w-1:
                    rest_sum = sum(data[row_index][:-1]) - data[row_index][low_conf_index]
                    new_value = data[row_index][-1] - rest_sum
                    data[row_index][low_conf_index] = new_value
                    isValid[int(row_index)] = True
                else:
                    data[row_index][low_conf_index] = sum(data[row_index][:-1])
                    isValid[int(row_index)] = True
    return isValid

def row_validator(
    data: List[List[int]]) -> List[bool]:
    """
    Validate the sum of each row

    Attention: The last row is the total value from the last year.
    The current approach to validate the last row is to compare the sum of the first 9 rows with the sum of the last row.
    If the checksum does not pass and there is only one element whose confidence score < 0.9, then we can update the score.
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
    df = pd.DataFrame(data)
    h, w = len(data), len(data[0])
    sum1 = df.iloc[0:h-3, -1].sum()
    sum2 = df.iloc[h-2, 0:w-1].sum()
    # print(f"TOTAL: {sum1}, {sum2}")
    if sum1 == sum2:
        data[-2][-1] = sum1
        return True
    return False

