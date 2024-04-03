"""
This Python script : does xxx
created by: Patrick_Durney
on: 31/01/24
"""

import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from dateutil import parser
from pandas.api.types import is_string_dtype, is_float_dtype, is_datetime64_any_dtype

def parse_and_identify(date_str):
    try:
        # Parse the date string
        parsed_date = parser.parse(date_str)

        # Convert all dates to datetime objects by adding a default time if missing
        if parsed_date.time() == pd.Timestamp(0).time():
            return pd.to_datetime(parsed_date.date()), 'Date'
        else:
            return pd.to_datetime(parsed_date), 'Datetime'
    except ValueError:
        # Return NaT (Not a Time) and Unknown type if parsing fails
        return pd.NaT, 'Unknown'

    # Function to parse and identify times (placeholder for your actual function)

def _get_summary_stats(wl_output, group_column='well_name'):
    # Group the data by 'well_name'
    grouped_data = wl_output.groupby(group_column)

    # Perform aggregations
    summary_stats = grouped_data.agg({
        'well_name': ['count'],
        'depth_to_water': ['mean', 'median', 'std', 'max', 'min'],
        'gw_elevation': ['mean', 'median', 'std', 'max', 'min'],
        'date': ['min', 'max']
    })

    # Flatten the column names
    summary_stats.columns = ['_'.join(col).strip() for col in summary_stats.columns.values]

    # Rename columns for clarity
    summary_stats.rename(columns={
        'well_name_count': 'reading_count',
        'depth_to_water_mean': 'mean_dtw',
        'depth_to_water_median': 'median_dtw',
        'depth_to_water_std': 'std_dtw',
        'depth_to_water_max': 'max_dtw',
        'depth_to_water_min': 'min_dtw',
        'gw_elevation_mean': 'mean_gwl',
        'gw_elevation_median': 'median_gwl',
        'gw_elevation_std': 'std_gwl',
        'gw_elevation_max': 'max_gwl',
        'gw_elevation_min': 'min_gwl',
        'date_min': 'start_date',
        'date_max': 'end_date'
    }, inplace=True)

    # Reset index to turn 'well_name' back into a column
    summary_stats.reset_index(inplace=True)
    summary_stats['reading_count'] = summary_stats['reading_count'].astype(int)

    # Convert datatypes
    summary_stats['start_date'] = pd.to_datetime(summary_stats['start_date'], format='%Y-%m-%d')
    summary_stats['end_date'] = pd.to_datetime(summary_stats['end_date'], format='%Y-%m-%d')

    return summary_stats


def find_overlapping_files(src, dst):
    """
    Find files in the source directory that already exist in the destination directory.
    """
    overlapping_files = []
    for src_dir, _, files in os.walk(src):
        dst_dir = src_dir.replace(str(src), str(dst), 1)
        for file in files:
            src_file = Path(src_dir).joinpath(file)
            dst_file = Path(dst_dir).joinpath(file)
            if dst_file.exists():
                overlapping_files.append((src_file, dst_file))
    return overlapping_files


def copy_with_prompt(src, dst, overlapping_items):
    """
    Copy files or directories from src to dst, with a single prompt for overwriting overlapping items.
    Pressing Enter without typing anything defaults to 'no'.
    """
    if overlapping_items:
        print(f"Found {len(overlapping_items)} items that would be overwritten.")
        response = input(
            "Do you want to overwrite these items? (y/n, default=n): ") or 'n'  # Default to 'n' if no input
        overwrite = response.lower() == 'y'
    else:
        overwrite = True  # If there are no overlapping items, proceed with copying

    if os.path.isfile(src):
        # Ensure the destination directory exists
        os.makedirs(dst, exist_ok=True)
        dst_file = Path(dst).joinpath(src.name)
        if dst_file.exists() and not overwrite:
            print(f"Skipping {dst_file} as it already exists.")
        else:
            shutil.copy2(src, dst_file)
            print(f"Copied file {src} to {dst_file}")
    elif os.path.isdir(src):
        if not os.path.exists(dst):
            os.makedirs(dst)
        for src_dir, _, files in os.walk(src):
            dst_dir = src_dir.replace(str(src), str(dst), 1)
            os.makedirs(dst_dir, exist_ok=True)
            for file in files:
                src_file = Path(src_dir).joinpath(file)
                dst_file = Path(dst_dir).joinpath(file)
                if dst_file.exists() and not overwrite:
                    continue
                shutil.copy2(src_file, dst_file)
                print(f"Copied {src_file} to {dst_file}")
    else:
        print(f"The source {src} is neither a file nor a directory.")


######################################
def pull_tethys_data_store(save_path, data_keys, council):
    # Convert save_path to a Path object if it is not already
    save_path = Path(save_path)

    # Initialize a dictionary to aggregate data from keys containing 'Horizons'
    council_data = {}

    # Check if the save_path exists
    if save_path.exists():
        with pd.HDFStore(save_path, mode='r') as store:
            # Loop through the provided data_keys
            for key in data_keys:
                # Check if 'Horizons' is in the key and the key exists in the store
                if council in key and key in store.keys():
                    # Read the data for the key and store it in the horizons_data dictionary
                    council_data[key] = store.get(key)
                    # You can also process the data here as needed before storing
    else:
        print(f"The file {save_path} does not exist.")
        return None  # Ensure a None is returned if the file doesn't exist

    # Return the aggregated data from keys containing 'Horizons'
    return council_data


########################################################################################################################


def process_hdf5_data(save_path, store_key, new_save_path, recalc=False):
    if new_save_path.exists() and not recalc:
        with pd.HDFStore(new_save_path, mode='r') as store:  # Open the file in read mode
            if f'/{store_key}' in store.keys():  # Check if the store_key exists
                combined_tethys_gw_depth_data = pd.read_hdf(store, store_key)
                return combined_tethys_gw_depth_data

    with pd.HDFStore(save_path, mode='r') as store:
        combined_tethys_gw_depth_data = pd.read_hdf(store, store_key)

        drop_columns = ['quality_code', 'lon', 'lat']
        combined_tethys_gw_depth_data.drop(columns=drop_columns, inplace=True)

        # Perform data processing here (e.g., renaming columns, dropping unnecessary columns)
        new_names = {'time': 'date', 'name': 'site_name', 'groundwater_depth': 'depth_to_water',
                     'alt_name': 'alt_well_name', 'reference_level': 'tethys_elevation',
                     'bore_depth': 'well_depth', 'bore_top_of_screen': 'top_topscreen',
                     'bore_bottom_of_screen': 'bottom_bottomscreen'}
        # Filter out keys from new_names that are not columns in the DataFrame
        filtered_new_names = {old: new for old, new in new_names.items() if
                              old in combined_tethys_gw_depth_data.columns}

        # Rename the columns using the filtered dictionary
        combined_tethys_gw_depth_data.rename(columns=filtered_new_names, inplace=True)

        type_mapping = {
            'site_name': 'str',
            'alt_well_name': 'str',
            'depth_to_water': 'float',
            'tethys_elevation': 'float',
            'well_depth': 'float',
            'top_topscreen': 'float',
            'bottom_bottomscreen': 'float'
        }

        # Filter out keys from type_mapping that are not columns in the DataFrame
        filtered_type_mapping = {column: dtype for column, dtype in type_mapping.items() if
                                 column in combined_tethys_gw_depth_data.columns}

        # Convert the data types of the filtered columns
        combined_tethys_gw_depth_data = combined_tethys_gw_depth_data.astype(filtered_type_mapping)

        with pd.HDFStore(new_save_path, mode='a') as store:  # Open the file in append mode
            if f'/{store_key}' in store.keys():  # Check if the key exists
                store.remove(store_key)  # Remove the data associated with the key if it exists
            store.put(store_key, combined_tethys_gw_depth_data, format='fixed')  # Write new data
        return combined_tethys_gw_depth_data

    return combined_tethys_gw_depth_data


def append_to_other(df, needed_columns):
    for index, row in df.iterrows():
        other_values = []
        for col in df.columns:
            if col not in needed_columns:
                # Append "column_name: value" to the list
                other_values.append(f"{col}: {row[col]}")
        # Update the 'other' column after processing all columns for the row
        df.at[index, 'other'] = ', '.join(other_values)  # Join all "col: value" pairs with ', '
    # Return the DataFrame after processing all rows
    return df


def needed_cols_and_types(council_name):
    needed_columns = ['well_name',
                      'well_depth',
                      'mp_elevation_NZVD',
                      'dist_mp_to_ground_level',
                      'nztm_x',
                      'nztm_y',
                      'top_topscreen',
                      'bottom_bottomscreen',
                      'screen_count',
                      'reading_count',
                      'start_date',
                      'end_date',
                      'mean_gwl',
                      'median_gwl',
                      'std_gwl',
                      'max_gwl',
                      'min_gwl',
                      'mean_dtw',
                      'median_dtw',
                      'std_dtw',
                      'max_dtw',
                      'min_dtw',
                      'artesian',
                      'dry_well',
                      'rl_elevation',
                      'rl_datum',
                      'rl_source',
                      'ground_level_datum',
                      'other'
                      ]

    default_values = {
        'mp_elevation_NZVD': np.nan,
        'dist_mp_to_ground_level': np.nan,
        'top_topscreen': np.nan,
        'bottom_bottomscreen': np.nan,
        'screen_count': np.nan,
        'reading_count': np.nan,
        'start_date': None,
        'end_date': None,
        'mean_gwl': np.nan,
        'median_gwl': np.nan,
        'std_gwl': np.nan,
        'max_gwl': np.nan,
        'min_gwl': np.nan,
        'mean_dtw': np.nan,
        'median_dtw': np.nan,
        'std_dtw': np.nan,
        'max_dtw': np.nan,
        'min_dtw': np.nan,
        'artesian': False,
        'dry_well': False,
        'rl_datum': "NZVD2016",
        'rl_source': council_name,
        'ground_level_datum': None,
        'other': ""
    }

    col_types = (
        {'mp_elevation_NZVD': 'float',
         'dist_mp_to_ground_level': 'float',
         'top_topscreen': 'float',
         'bottom_bottomscreen': 'float',
         'screen_count': 'float',
         'reading_count': 'Int64',
         'mean_gwl': 'float',
         'median_gwl': 'float',
         'std_gwl': 'float',
         'max_gwl': 'float',
         'min_gwl': 'float',
         'mean_dtw': 'float',
         'median_dtw': 'float',
         'std_dtw': 'float',
         'max_dtw': 'float',
         'min_dtw': 'float',
         'rl_elevation': 'float',
         'artesian': 'boolean',
         'dry_well': 'boolean',
         'rl_datum': 'str',
         'rl_source': 'str',
         'ground_level_datum': 'str',
         'other': 'str',
         'well_name': 'str'
         })

    return {
        'needed_columns': needed_columns,
        'default_values': default_values,
        'col_types': col_types
    }


def data_checks(data):
    """ This function checks the timeseries data to see if there are any issues, using assertions
    drops rows where depth_to_water is less than -50 and gw_elevation is greater than 600
    :return None"""

    # first checking it's a dataframe
    assert isinstance(data, pd.DataFrame), 'data is not a dataframe'

    # checking all the strings
    string_columns = ['well_name']
    for col in string_columns:
        assert is_string_dtype(data[col]), f'{col} is not a string'

    # checking all the floats
    float_columns = ['depth_to_water', 'gw_elevation']
    for col in float_columns:
        assert is_float_dtype(data[col]), f'{col} is not a float'

    # checking datetime
    datetime_columns = ['date']
    for col in datetime_columns:
        assert is_datetime64_any_dtype(data[col]), f'{col} is not a datetime'

    data.drop(data[data['depth_to_water'] < -50].index, inplace=True)
    data.drop(data[data['gw_elevation'] > 600].index, inplace=True)


def metadata_checks(data, external_column=None, metadata_column='well_name'):
    """
    This function checks the metadata for any issues using assertions and also checks for the presence of items from
    another DataFrame's column in a specified column of the metadata.

    Parameters:
    - data: The pandas DataFrame containing the metadata to check.
    - external_column: Optional; a pandas Series containing the items to check against the metadata.
    - metadata_column: The column name in the metadata DataFrame against which to check the external_column items.

    Returns:
    - missing_items: A list of items from external_column that are missing in the metadata_column of the metadata DataFrame.
    """

    # first checking it's a dataframe
    assert isinstance(data, pd.DataFrame), 'data is not a dataframe'

    # Checking all strings
    string_columns = ['well_name', 'ground_level_datum', 'other', 'rl_datum', 'rl_source']
    for col in string_columns:
        if not is_string_dtype(data[col]):
            print(f"Warning: {col} is not a string. Converting to string.")
            data[col] = data[col].astype(str)

    # Checking all floats
    float_columns = ['nztm_x', 'nztm_y', 'bottom_bottomscreen', 'top_topscreen', 'dist_mp_to_ground_level',
                     'mp_elevation_NZVD', 'rl_elevation', 'well_depth']
    for col in float_columns:
        if not is_float_dtype(data[col]):
            print(f"Warning: {col} is not a float. Attempting conversion.")
            data[col] = pd.to_numeric(data[col], errors='coerce')  # Convert to float, coerce errors to NaN

    int_columns = ['reading_count', 'screen_count']
    for col in int_columns:
        if not pd.api.types.is_integer_dtype(data[col]):
            print(f"Warning: {col} is not an integer type. Attempting conversion.")
            # First, convert to numeric (float) and coerce errors to NaN
            data[col] = pd.to_numeric(data[col], errors='coerce')
            # Then, convert the result to nullable integer type
            data[col] = data[col].astype('Int64')

    # checking datetimes
    datetime_columns = ['start_date', 'end_date']
    for col in datetime_columns:
        assert is_datetime64_any_dtype(data[col]), f'{col} is not a datetime'

    missing_items = []

    # Check for presence of external column items in metadata
    if external_column is not None and metadata_column in data.columns:
        # Find items in external_column that are not present in metadata_column
        missing_items = external_column[~external_column.isin(data[metadata_column])].unique().tolist()
        if missing_items:
            print(
                f"Warning: The following items are present in the external column but missing in '{metadata_column}': {missing_items}")
        else:
            print(f"All items in the external column are present in '{metadata_column}'.")

    return missing_items


def renew_hdf5_store(old_path, store_key, new_data):
    old_path = Path(old_path)
    temp_path = old_path.with_name('Temp.hdf')

    # Open a new store to write data to
    with pd.HDFStore(temp_path, mode='w') as new_store:
        # Check if the old HDF5 file exists
        if old_path.exists():
            # Open the existing HDF5 file to copy data from
            with pd.HDFStore(old_path, mode='r') as old_store:
                for key in old_store.keys():
                    if key != f'/{store_key}':
                        # Copy data from the old store to the new store, excluding the target key
                        new_store.put(key, old_store[key])

        # Write the new data to the new store under the specified key
        new_store.put(store_key, new_data, format='table', data_columns=True)

    # Check if the old file exists before trying to remove it
    if old_path.exists():
        old_path.unlink()  # Safely remove the old file

    temp_path.rename(old_path)  # Rename the temp file to the old file's name


def get_hdf5_store_keys(hdf5_path):
    with pd.HDFStore(hdf5_path, mode='r') as store:  # Open the file in read mode
        keys = store.keys()  # Get a list of all keys in the store
    return keys


def assign_flags_based_on_null_values(dataframe, check_column, flag_column, true_value, false_value):
    """
    Assigns flags to a dataframe based on the presence or absence of null values in a specified column.

    Parameters:
    - dataframe: The pandas DataFrame to operate on.
    - check_column: The name of the column to check for null/non-null values.
    - faggregate_water_datalag_column: The name of the column where the flag values will be assigned.
    - true_value: The value to assign if the condition (non-null) is True.
    - false_value: The value to assign if the condition is False.

    Returns:
    - Modifies the dataframe in place by adding/updating the flag_column with the assigned values.
    """

    # Ensure the check_column exists in the dataframe, create it with np.nan if it doesn't
    if check_column not in dataframe.columns:
        dataframe[check_column] = np.nan

    # Use np.where to assign the flag values based on the non-null status of check_column
    dataframe[flag_column] = np.where(
        pd.notnull(dataframe[check_column]),  # Condition: check_column is not NaN
        true_value,  # Value to assign if condition is True
        false_value  # Value to assign if condition is False
    )


def aggregate_water_data_base(df, group_by_columns):
    # Function to calculate conditional mean
    def conditional_mean(series, flag_series):
        filtered_series = series[(flag_series <= 4) | (flag_series.min() > 4)]
        return filtered_series.mean()

    # Function to find minimum non-zero value
    def min_non_zero(series):
        non_zeros = series[series != 0]
        return non_zeros.min() if not non_zeros.empty else 0

    # Function to find mode
    def mode_agg(series):
        return series.mode().iloc[0] if not series.mode().empty else np.nan

    # Define aggregation dictionary
    agg_dict = {
        'depth_to_water': lambda x: conditional_mean(x, df.loc[x.index, 'dtw_flag']),
        'gw_elevation': lambda x: conditional_mean(x, df.loc[x.index, 'water_elev_flag']),
        'dtw_flag': min_non_zero,
        'water_elev_flag': min_non_zero
    }

    # Add 'first' or 'mode' for other columns
    for col in df.columns:
        if col not in agg_dict and col not in group_by_columns:
            agg_dict[col] = 'first'  # Use mode_agg for categorical columns

    # Aggregate the data
    aggregated_df = df.groupby(group_by_columns, as_index=False).agg(agg_dict)

    return aggregated_df


def aggregate_water_data(df):
    # Split the DataFrame into two: one with missing dates and one with present dates
    df_with_date = df.dropna(subset=['date'])
    df_missing_date = df[df['date'].isna()]

    # Perform aggregation on the DataFrame with dates
    aggregated_with_date = aggregate_water_data_base(df_with_date, ['well_name', 'date'])

    # Perform aggregation on the DataFrame with missing dates, only by 'well_name'
    aggregated_missing_date = aggregate_water_data_base(df_missing_date, ['well_name'])

    # Combine the two aggregated DataFrames
    aggregated_combined = pd.concat([aggregated_with_date, aggregated_missing_date], ignore_index=True)

    return aggregated_combined
