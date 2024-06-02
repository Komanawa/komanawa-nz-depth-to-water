"""
This Python script : cleans the waikato data
created by: Patrick_Durney
this was originally created by Evelyn_Charlesworth and is simply a modification to bring into tandard format
on: 30/01/24
"""
import logging
import os
import re
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
from dateutil import parser

from build_dataset.generate_dataset.head_data_processing.data_processing_functions import (_get_summary_stats,
                                                                                           renew_hdf5_store,
                                                                                           assign_flags_based_on_null_values,
                                                                                           metadata_checks,
                                                                                           data_checks,
                                                                                           needed_cols_and_types)
from build_dataset.generate_dataset.project_base import groundwater_data, unbacked_dir


def _get_metadata(file_path, skiprows=0):
    """
    Reads in metadata from an Excel or CSV spreadsheet.
    :param file_path: Path to the file (Excel or CSV) containing metadata.
    :param skiprows: Number of rows to skip at the start of the file (default 0).
    :return: DataFrame with the raw data read from the file.
    """
    try:
        # Ensure the file path is a Path object
        file_path = Path(file_path)

        # Check if the file exists
        if not file_path.exists():
            logging.error(f"File not found: {file_path}")
            return None
        # Determine file extension and read data accordingly
        if file_path.suffix == '.xlsx':
            metadata = pd.read_excel(file_path, skiprows=skiprows)
        elif file_path.suffix == '.csv':
            metadata = pd.read_csv(file_path, skiprows=skiprows)
        else:
            logging.error(f"Unsupported file format: {file_path}")
            return None
        return metadata
    except Exception as e:
        logging.error(f"Error reading file {file_path}: {e}")
        raise e


def _clean_metadata(file_path, drop_columns, rename_columns, skiprows, special_handling=None):
    """
    Enhanced function to clean metadata, accommodating both ts_meta_data and other datasets.
    :param file_path: Path to the metadata file.
    :param drop_columns: List of columns to drop.
    :param rename_columns: Dictionary for renaming columns.
    :param skiprows: Number of rows to skip at the start of the file (default 0).
    :param special_handling: Optional function for special data handling.
    :return: Cleaned DataFrame.
    """
    # Read in the raw data
    metadata = _get_metadata(file_path, skiprows=skiprows)
    if metadata is None:
        raise ValueError(f"Error reading metadata file: {file_path}")
    # Process 'Location' column if it exists, specific to ts_meta_data
    if 'Location' in metadata.columns:
        metadata['extracted_number'] = metadata["Location"].str.extract(r'(\d+)')
        metadata['well_name'] = 'BN-' + metadata['extracted_number']
        metadata = metadata.drop_duplicates(subset=['well_name'])
    else:
        # If 'Location' column is not found, log a message and continue
        logging.info("Column 'Location' not found. Proceeding with general metadata cleaning.")
    # Drop unnecessary columns
    metadata = metadata.drop(columns=drop_columns, errors='ignore')
    # Rename columns
    metadata = metadata.rename(columns=rename_columns)
    # Apply sall_columnspecial handling if provided
    if special_handling is not None:
        metadall_columnsata = special_handling(metadata)
    # Preprocess numeric columns to replace non-numeric values with NaN
    numeric_cols = [col for col in metadata.columns if
                    'depth' in col or 'elevation' in col or 'nztm' in col or 'dem' in col]
    for col in numeric_cols:
        metadata[col] = pd.to_numeric(metadata[col], errors='coerce')
    # Handle datatypes
    metadata = metadata.astype({col: 'float' if col in numeric_cols else 'bool' if 'artesian' in col else 'str' for
                                col in metadata.columns})
    return metadata


# Special handling function for artesian values
def _handle_artesian(metadata, set_negative_to_zero=False):
    # Initialize 'artesian' column
    metadata['artesian'] = False
    # Identify non-numeric and special cases in 'depth_to_water_static'
    special_cases = ['(+)0.42', '-', 'artesian']
    for case in special_cases:
        metadata.loc[metadata['depth_to_water_static'] == case, 'artesian'] = True
    # Replace non-numeric values with NaN (or 0 if needed)
    metadata['depth_to_water_static'] = pd.to_numeric(metadata['depth_to_water_static'], errors='coerce')
    # Handle negative values in 'depth_to_water_static'
    metadata.loc[metadata['depth_to_water_static'] < 0, 'artesian'] = True
    condition = pd.isna(metadata['depth_to_water_static']) & (metadata['artesian'] is True)
    if set_negative_to_zero:
        # Set values that meet the condition to 0
        metadata.loc[condition, 'depth_to_water_static'] = 0
    else:
        # Set values that meet the condition to NaN
        metadata.loc[condition, 'depth_to_water_static'] = np.nan
    # Drop temporary columns if any
    metadata = metadata.drop(columns=['temp_artesian'], errors='ignore')
    return metadata


def _rename_duplicates(df, suffix):
    """
    Rename duplicate columns in a DataFrame by appending a suffix.
    """
    cols = pd.Series(df.columns)
    for dup in cols[cols.duplicated()].unique():
        cols[cols[cols == dup].index.values.tolist()] = [dup + '_' + str(i) + suffix for i in
                                                         range(1, sum(cols == dup) + 1)]
    df.columns = cols
    return df


def process_st_wl(st_wl, data_source, metadata):
    """
    Process static water level data. e.g. take the data out of the metadata and into format to merge with ts
    dtw_flag = 1= logger, 2= manual, 3= static_oneoff, 4= calculated frm gw_elevation, 5= aquifer test, 6= other
    water_ele_flag = 1= logger, 2= manual, 3= static_oneoff, 4= aquifer test, 5= other
    """
    if data_source == "BOPRC":
        rl_data = metadata[
            ['well_name', 'rl_elevation', 'well_depth_elevation_NZVD', 'well_depth', 'diff_moturiki_nzdv2016']]
        rl_key, rl_key1 = process_reference_levels(rl_data)
        st_wl['rl'] = st_wl['well_name'].map(rl_key).fillna(np.nan)
    else:
        st_wl['rl'] = st_wl['rl_elevation']

    mask = st_wl['rl'].isna()
    # Where 'rl' is not NaN, compute 'gw_elevation'
    st_wl.loc[~mask, 'gw_elevation'] = st_wl.loc[~mask, 'rl'] - st_wl.loc[~mask, 'depth_to_water_static']
    # Where 'rl' is NaN, set 'gw_elevation' to NaN
    st_wl.loc[mask, 'gw_elevation'] = np.nan

    st_wl = st_wl.rename(columns={'depth_to_water_static': 'depth_to_water'})
    assign_flags_based_on_null_values(st_wl, 'depth_to_water', 'dtw_flag', 3, 0)
    assign_flags_based_on_null_values(st_wl, 'gw_elevation', 'water_elev_flag', 3, 0)

    st_wl.loc[:, 'data_source'] = data_source
    st_wl.loc[:, 'elevation_datum'] = datum  #
    st_wl.loc[:, 'other'] = "static_wl"
    st_wl.loc[:, 'date'] = pd.to_datetime(None)
    st_wl['date'] = pd.to_datetime(st_wl['date'])
    st_wl = st_wl.drop(columns=['rl'])
    return st_wl


def determine_prefix(location):
    location = location.lower()
    if 'piezo' in location or 'bore' in location:
        return 'BN-'
    else:
        return location.split()[0] + '-' if location else ''


def parse_and_identify(date_str):
    try:
        # Parse the date string
        parsed_date = parser.parse(date_str)

        # Check if the time component is 00:00:00 (indicating just a date)
        if parsed_date.time() == pd.Timestamp(0).time():
            return parsed_date.date(), 'Date'
        else:
            return parsed_date, 'Datetime'
    except ValueError:
        # Return None and Unknown type if parsing fails
        return None, 'Unknown'

    # Function to parse and identify times (placeholder for your actual function)


def parse_and_identify_time(time_str):
    try:
        # Use dateutil.parser to flexibly parse the time string
        parsed_time = parser.parse(time_str)

        # Format the time to HH:MM:SS to check the structure
        time_format = parsed_time.strftime('%H:%M:%S')

        # Identify common time formats based on the structure
        if time_format.endswith('00:00'):  # HH:MM format
            identified_format = 'HH:MM'
        elif time_format.endswith(':00'):  # HH:MM:SS where SS is 00
            identified_format = 'HH:MM:SS'
        else:  # General case, includes seconds
            identified_format = 'HH:MM:SS'

        return parsed_time.time(), identified_format
    except ValueError:
        # Return None and 'Unknown' if parsing fails
        return None, 'Unknown'


def process_reference_levels(df):
    """
    Process reference level data.
    """
    df['elevation'] = df['rl_elevation'].fillna(df['well_depth_elevation_NZVD'] + df['well_depth'])
    return dict(zip(df['well_name'], df['elevation'])), dict(zip(df['well_name'], df['diff_moturiki_nzdv2016']))


def process_ts_wl(ts_wl, rl_key, rl_key1):
    """
    Process time series water level data.
    """
    ts_wl['rl'] = ts_wl['site_name'].map(rl_key).fillna(np.nan)
    ts_wl['diff_moturiki_nzdv2016'] = ts_wl['site_name'].map(rl_key1).fillna(np.nan)
    ts_wl['depth_to_water'] = ts_wl['rl'] - ts_wl['gw_elevation']
    ts_wl.drop(columns=['rl'], inplace=True)
    ts_wl['other'] = ts_wl['other'].astype(
        str) + "datum is motoriki, but rl data is nzvd2016 therefore depth to water???+-0.3m"
    return ts_wl


def _get_wl_data(metadata_paths, folder_path, metadata, data_source, datum, skiprows=None, need_site_data=False):
    """This reads in the continuous timeseries data.
    dtw_flag = 1= logger, 2= manual, 3= static_oneoff, 4= calculated frm gw_elevation, 5= aquifer test, 6= other
    water_ele_flag = 1= logger, 2= manual, 3= static_oneoff, 4= aquifer test, 5= other
    """
    data = []
    for filename in os.listdir(folder_path):
        file_path = folder_path / filename
        well_name = ''.join(re.findall(r'(\d+(?:_\d+)?)', filename))
        # Filter out non-target files
        if file_path.suffix in ['.xlsx', '.csv']:
            try:
                if file_path.suffix == '.xlsx':
                    df = pd.read_excel(file_path, skiprows=15)
                    df['well_name'] = well_name
                elif file_path.suffix == '.csv':
                    # Specify dtype if you know the schema in advance to speed up reading
                    df = pd.read_csv(file_path, skiprows=15)  # Add dtype={'column_name': 'data_type', ...} if possible
                    df['well_name'] = well_name
                data.append(df)
            except Exception as e:
                print(f"Error processing {file_path}: {e}")

    # Concatenate all DataFrames in the list into a single DataFrame
    data = pd.concat(data, ignore_index=True)

    df = data.copy()
    # Drop the 'key' column if it exists
    if 'key' in df.columns:
        df.drop(columns=['key'], inplace=True)
    # Rename columns
    if 'Value (m)' in df.columns:
        df.rename(columns={'Value (m)': 'gw_elevation'}, inplace=True)

    if 'GWLevel [m]' in df.columns:
        df.rename(columns={'GWLevel [m]': 'gw_elevation'}, inplace=True)

    assign_flags_based_on_null_values(df, 'gw_elevation', 'water_elev_flag', 2, 0)
    assign_flags_based_on_null_values(df, 'depth_to_water', 'dtw_flag', 2, 0)

    # origin of data
    df['data_source'] = data_source

    # create gw elevation column if absent
    if 'gw_elevation' in df.columns:
        # Create 'elevation_datum' column based on 'gw_elevation' being not null
        df['elevation_datum'] = df['gw_elevation'].notnull().replace({True: datum, False: None})

    # initialise other column
    if 'other' not in df.columns:
        df['other'] = "time_series"
    elif 'other' in df.columns:
        df['other'] = df['other'].astype(str) + " time_series"
    df['date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
    df['time'] = pd.to_datetime(df['Time'], errors='coerce').dt.time
    # Combine 'date' and 'time' columns into a single 'datetime' column
    df['date'] = pd.to_datetime(df['date'].astype(str) + ' ' + df['time'].astype(str), errors='coerce')
    df = df.drop(columns=['Time', "Date", 'time'])
    df = df.sort_values(['well_name', 'date'])

    ts_wl = df

    # create static wl data
    st_wl = metadata.loc[:, ['well_name', 'depth_to_water_static', 'rl_elevation']]
    st_wl = process_st_wl(st_wl, data_source, metadata)
    st_wl = st_wl.loc[:,
            ['well_name', 'date', 'depth_to_water', 'gw_elevation', 'dtw_flag', 'water_elev_flag', 'data_source',
             'elevation_datum', 'other']]

    # merge ts and static wl data
    wl_output = pd.concat([ts_wl, st_wl[~st_wl['well_name'].isin(ts_wl['well_name'])]])
    wl_output = wl_output.sort_values(['well_name', 'date'])
    if "GAP" in wl_output['gw_elevation'].unique():
        wl_output.loc[wl_output['gw_elevation'] == "GAP", 'gw_elevation'] = np.nan

    wl_output = wl_output.astype(
        {'well_name': 'str',
         'depth_to_water': 'float',
         'gw_elevation': 'float',
         'dtw_flag': 'int',
         'water_elev_flag': 'int',
         'data_source': 'str',
         'elevation_datum': 'str',
         'other': 'str'
         })

    wl_output = wl_output[['well_name', 'date', 'depth_to_water', 'gw_elevation', 'dtw_flag', 'water_elev_flag',
                           'data_source', 'elevation_datum', 'other']]

    return wl_output


def _process_wl_data(metadata_paths, folder_path, save_path, store_key, metadata, datum, data_source, recalc=False):
    # Define the folder and file paths
    folder_path = folder_path
    save_path = save_path
    store_key = store_key
    # Check if saved file exists and recalculation is not requested
    if save_path.exists() and not recalc:
        df = pd.read_hdf(save_path, store_key)
    else:
        df = _get_wl_data(folder_path=folder_path, metadata=metadata, metadata_paths=metadata_paths,
                          datum=datum, data_source=data_source)
        return df
    return df


def output(*, metadata_paths, wl_data_path, save_path, wl_store_key, meta_data_requirements, metadata_store_key, datum,
           data_source,
           drop_columns_list=None, rename_columns_list=None, skip_rows_list=None,
           recalc=False):
    """
    A function that combines multiple metadata datasets, allowing for variable numbers of metadata inputs.
    Each metadata input can have its own set of columns to drop and rename.

    :param metadata_paths: List of paths to metadata files.
    :param drop_columns_list: List of lists, each containing columns to drop for corresponding metadata.
    :param rename_columns_list: List of dictionaries, each mapping existing columns to new names for corresponding metadata.
    :param wl_data_path: Path to well data.
    :param save_path: Path to save the final output.
    :param wl_store_key: HDF store key for well data.
    :param metadata_store_key: HDF store key for metadata.
    :param recalc: Flag to recalculate if True.
    :return: None, writes final outputs to HDF.
    """
    water_data_store_path = groundwater_data.joinpath('gwl_waikato_data', 'cleaned_data', 'combined_waikato_data.hdf')
    store_key_water_data = 'waikato_gwl_data'
    store_key_metadata = 'waikato_metadata'

    # Check if data needs to be recalculated or if the HDF files don't exist
    if not recalc and water_data_store_path.exists():
        combined_water_data = pd.read_hdf(water_data_store_path, store_key_water_data)
        combined_metadata = pd.read_hdf(water_data_store_path, store_key_metadata)

    else:
        # Initialize lists if None
        drop_columns_list = drop_columns_list or [[] for _ in metadata_paths]
        rename_columns_list = rename_columns_list or [{} for _ in metadata_paths]
        skip_rows_list = skip_rows_list or [{} for _ in metadata_paths]
        needed_columns = ['well_name',
                          'well_depth',
                          'mp_elevation_L1937',
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
                          'artesian',
                          'dry_well',
                          'rl_elevation',
                          'rl_datum',
                          'rl_source',
                          'ground_level_datum',
                          'other'
                          ]

        default_values = {
            'mp_elevation_L1937': np.nan,
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
            'artesian': False,
            'dry_well': False,
            'rl_datum': None,
            'ground_level_datum': None,
            'other': ""
        }
        # Ensure the lists match the length of metadata_paths
        assert len(drop_columns_list) == len(
            metadata_paths), "drop_columns_list length must match metadata_paths length"
        assert len(rename_columns_list) == len(
            metadata_paths), "rename_columns_list length must match metadata_paths length"

        all_metadata = []
        special_func = [_handle_artesian, _handle_artesian, _handle_artesian,
                        None]  #
        for mdp, skip, rename_cols, drop_cols, sfunc in zip(metadata_paths, skip_rows_list, rename_columns_list,
                                                            drop_columns_list,
                                                            special_func):
            temp_metadata = _clean_metadata(mdp, drop_cols, rename_cols, skip, sfunc)
            temp_metadata = temp_metadata.drop_duplicates(subset=['well_name'])
            all_metadata.append(temp_metadata)

        combined_metadata = pd.concat(all_metadata, ignore_index=True)
        # combined_metadata = _merge_and_consolidate(all_metadata)

        combined_metadata['well_name'] = combined_metadata['well_name'].replace(['nan', 'NaN', 'None', ''], None,
                                                                                )
        combined_metadata = combined_metadata.dropna(subset=['well_name'])
        cols = combined_metadata.columns.tolist()
        for col in needed_columns:
            if col not in combined_metadata.columns:
                combined_metadata[col] = default_values.get(col)

        combined_metadata['start_date'] = pd.to_datetime(combined_metadata['start_date'])
        combined_metadata['end_date'] = pd.to_datetime(combined_metadata['end_date'])

        combined_metadata = combined_metadata.astype(
            {'mp_elevation_L1937': 'float',
             'mp_elevation_NZVD': 'float',
             'dist_mp_to_ground_level': 'float',
             'top_topscreen': 'float',
             'bottom_bottomscreen': 'float',
             'screen_count': 'float',
             'reading_count': 'float',
             'mean_gwl': 'float',
             'median_gwl': 'float',
             'std_gwl': 'float',
             'max_gwl': 'float',
             'min_gwl': 'float',
             'rl_elevation': 'float',
             'artesian': 'boolean',
             'dry_well': 'boolean',
             'rl_datum': 'str',
             'rl_source': 'str',
             'ground_level_datum': 'str',
             'other': 'str',
             'well_name': 'str'
             })

        # fill nan in screen depth with casing or well depth where appropriate
        if 'casing_depth' in combined_metadata.columns:
            combined_metadata['top_topscreen'].fillna(combined_metadata['casing_depth'], inplace=True)

        if 'well_depth' in combined_metadata.columns:
            combined_metadata['bottom_bottomscreen'].fillna(combined_metadata['well_depth'], inplace=True)

        # Define the columns to keep
        cols_to_keep = [
            'well_name', 'rl_elevation', 'rl_datum', 'rl_source',
            'ground_level_datum', 'ground_level_source', 'well_depth', 'top_topscreen',
            'bottom_bottomscreen', 'nztm_x', 'nztm_y', 'other', 'dist_mp_to_ground_level'
        ]

        # Append non-kept column data to 'other', ensuring data is string format and NaN values are handled
        for col in combined_metadata.columns.difference(cols_to_keep):
            # Initialize a temporary list to hold the updated 'other' column values
            updated_other_values = []
            # Iterate over each row in the DataFrame
            for index, row in combined_metadata.iterrows():
                # Get the current value in the 'other' column
                current_other_value = row['other']
                # Get the value from the current column, ensuring it's a string and handling NaN values
                col_value = str(row[col]) if pd.notnull(row[col]) else ''
                # If there is a value in the current column, format it and append to the current 'other' value
                if col_value:
                    updated_value = f"{current_other_value}{col}= {col_value}, "
                else:
                    updated_value = current_other_value
                # Append the updated 'other' value to the temporary list
                updated_other_values.append(updated_value)
            # Update the 'other' column with the new concatenated values
            combined_metadata['other'] = updated_other_values

        # Initialize a list to hold condition results for each row
        condition_strings = pd.Series([''] * len(combined_metadata), index=combined_metadata.index)

        # Check and concatenate 'top_screen' condition string if 'casing_depth' column exists
        if 'casing_depth' in combined_metadata.columns:
            top_screen_condition_str = "top_screen = " + (
                    combined_metadata['top_topscreen'] == combined_metadata['casing_depth']).astype(str) + ", "
            condition_strings += top_screen_condition_str

        # Check and concatenate 'bottom_screen' condition string if 'well_depth' column exists
        if 'well_depth' in combined_metadata.columns:
            bottom_screen_condition_str = "bottom_screen = " + (
                    combined_metadata['bottom_bottomscreen'] == combined_metadata['well_depth']).astype(str) + ", "
            condition_strings += bottom_screen_condition_str

        # Now append the accumulated condition results to the 'other' column
        combined_metadata['other'] = combined_metadata['other'] + condition_strings

        # Optionally: Trim the final comma and space from the 'other' column
        combined_metadata['other'] = combined_metadata['other'].str.rstrip(', ')

        # processing regular readings
        combined_water_data = _process_wl_data(metadata_paths=metadata_paths, folder_path=wl_data_path,
                                               save_path=save_path,
                                               store_key=wl_store_key, datum=datum, data_source=data_source,
                                               metadata=combined_metadata, recalc=recalc)

        combined_metadata.drop(
            columns=[col for col in combined_metadata.columns if col not in cols_to_keep and col != 'other'],
            inplace=True)
        # cal stats
        stats = _get_summary_stats(combined_water_data)
        # data checks

        combined_metadata = combined_metadata.merge(stats, on='well_name', how='left')

        for col, dtype in meta_data_requirements['col_types'].items():
            if col in combined_metadata.columns:
                # If column exists, convert its data type
                combined_metadata[col] = combined_metadata[col].astype(dtype)
            else:
                combined_metadata[col] = meta_data_requirements['default_values'].get(col)

        data_checks(combined_water_data)
        metadata_checks(combined_metadata)

        combined_metadata = combined_metadata.copy()
        for index, row in combined_metadata.iterrows():
            other_values = []
            for col in combined_metadata.columns:
                if col not in cols_to_keep:
                    # Append "column_name: value" to the list
                    other_values.append(f"{col}: {row[col]}")
                    combined_metadata.at[index, 'other'] = ', '.join(
                        other_values)  # Join all "col: value" pairs with ', '

        # Drop columns not in cols_to_keep and not 'other'
        combined_metadata.drop(
            columns=[col for col in combined_metadata.columns if col not in cols_to_keep and col != 'other'],
            inplace=True)

        # writing to hdf
        renew_hdf5_store(new_data=combined_water_data, old_path=water_data_store_path,
                         store_key=store_key_water_data)
        renew_hdf5_store(new_data=combined_metadata, old_path=water_data_store_path,
                         store_key=store_key_metadata)

    return {'combined_water_data': combined_water_data, 'combined_metadata': combined_metadata}


########################################################################################################################

waikato_metadata_path = groundwater_data.joinpath('gwl_waikato_data',
                                                  'REQ195423 Future Coasts Aotearoa GW level data',
                                                  'National Wells database - Bore Data.xlsx')
drop_columns_waikato = {'Lat', 'Long'}
rename_columns_waikato = {'WELL_NO': 'well_name', 'East': 'nztm_x', 'North': 'nztm_y',
                          'Static WL': 'depth_to_water_static',
                          'Depth': 'well_depth', 'SCREEN_BOTTOM': 'bottom_bottomscreen', 'SCREEN_TOP': 'top_topscreen'}

waikato_wl_data_path = groundwater_data.joinpath('gwl_waikato_data', 'REQ195423 Future Coasts Aotearoa GW level data',
                                                 'gwl_data')

lacal_wl_data_path = unbacked_dir.joinpath('waikato_working/')
# Ensure the destination directory exists
if not os.path.exists(lacal_wl_data_path):
    os.makedirs(lacal_wl_data_path)
    # Copy the entire directory tree to the destination
    try:
        shutil.copytree(waikato_wl_data_path, lacal_wl_data_path, dirs_exist_ok=True)
        print("Directory tree copied successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")

save_path = groundwater_data.joinpath('gwl_waikato_data', 'cleaned_data', 'combined_waikato_data.hdf')
wl_store_key = 'waikato_gwl_data'
waikato_metadata_store_key = 'waikato_metadata'
metadata_paths = [waikato_metadata_path]
drop_columns_list = [drop_columns_waikato]
rename_columns_list = [rename_columns_waikato]
skip_rows_list = [0]
datum = "NZVD2016"
data_source = "WRC"


def get_wrc_data(recalc=False):
    meta_data_requirements = needed_cols_and_types('WRC')
    final_df = output(metadata_paths=metadata_paths, drop_columns_list=drop_columns_list,
                      rename_columns_list=rename_columns_list, skip_rows_list=skip_rows_list,
                      wl_data_path=waikato_wl_data_path, save_path=save_path, wl_store_key=wl_store_key,
                      metadata_store_key=waikato_metadata_store_key, datum=datum, data_source=data_source,
                      meta_data_requirements=meta_data_requirements,
                      recalc=recalc)
    return final_df


if __name__ == '__main__':
    data = get_wrc_data(recalc=True)
    pass
