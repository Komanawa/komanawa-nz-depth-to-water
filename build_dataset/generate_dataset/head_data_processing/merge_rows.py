"""
created matt_dumont 
on: 26/01/24
"""
import pandas as pd
import numpy as np


def merge_rows_if_possible(df, on, precision=None, skip_cols=None, actions=None):
    """
    merge rows if possible, otherwise retain duplicates for manual inspection
    :param df: dataframe
    :param on: column to merge on
    :param precision: None or dictionary of precisions for columns
    :param skip_cols: None or list of columns to skip (just take first value)
    :param actions: None or dictionary of actions to take for columns (e.g. {dtw:np.nanmean})
    :return:
    """
    if skip_cols is None:
        skip_cols = []
    if precision is None:
        precision = {}
    if actions is None:
        actions = {}
    for col in df.columns:
        if col not in precision:
            precision[col] = 1e-08
    assert isinstance(df, pd.DataFrame)
    out = []
    for ref in df.loc[:, on].unique():
        temp = df.loc[df.loc[:, on] == ref]
        if len(temp) == 1:  # 1 value
            out.append(temp)
            continue
        keep_new = True
        temp_out = pd.DataFrame(index=[0], columns=temp.columns)
        temp_out.loc[0, on] = ref  # Explicitly set the value for the 'on' column
        for col in df.keys():
            if col in skip_cols or col == on:  # Skip processing for skipped columns and the 'on' column
                continue
            t = temp.loc[:, col].dropna()
            if len(t) == 0:  # no data
                temp_out.loc[0, col] = np.nan
            elif len(t) == 1:  # one value
                temp_out.loc[0, col] = t.iloc[0]
            elif len(set(t)) == 1:  # one value repeated
                temp_out.loc[0, col] = t.iloc[0]
            else:
                numeric = pd.to_numeric(t, 'coerce')
                nums_close = np.allclose(numeric, np.full(numeric.shape, numeric.iloc[0]), atol=precision[col])
                if pd.notna(numeric).all() and nums_close:
                    # same numbers within float precision
                    temp_out.loc[0, col] = t.iloc[0]
                elif pd.notna(numeric).sum() >= 5:
                    temp_out.loc[0, col] = t.mode()[0]
                elif col in actions:
                    temp_out.loc[0, col] = actions[col](t)
                else:
                    strings = t.astype(str).str.lower().str.strip()
                    strings = strings.loc[~(strings == 'nan')]  # handle nan strings
                    if strings.empty:
                        temp_out.loc[0, col] = 'nan'
                    elif (strings == strings.iloc[0]).all():
                        # string matching
                        temp_out.loc[0, col] = t.iloc[0]
                    else:
                        keep_new = False
        if keep_new:
            out.append(temp_out)
        else:
            out.append(temp)

    return pd.concat(out, ignore_index=True)