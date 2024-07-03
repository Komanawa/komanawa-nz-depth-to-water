"""
This Python script : does xxx
created by: Patrick_Durney
on: 26/02/24
"""

import logging
import os
import numpy as np
import pandas as pd

from build_dataset.generate_dataset.project_base import groundwater_data, unbacked_dir
from build_dataset.generate_dataset.head_data_processing.data_processing_functions import (find_overlapping_files,
                                                                                           copy_with_prompt, \
                                                                                           _get_summary_stats,
                                                                                           needed_cols_and_types,
                                                                                           metadata_checks, \
                                                                                           data_checks,
                                                                                           append_to_other,
                                                                                           assign_flags_based_on_null_values,
                                                                                           renew_hdf5_store,
                                                                                           aggregate_water_data)
from build_dataset.generate_dataset.head_data_processing.merge_rows import merge_rows_if_possible


def _get_metadata(local_paths, file_name, skiprows=1):
    """
    Reads in metadata from an Excel or CSV spreadsheet.
    :param file_path: Path to the file (Excel or CSV) containing metadata.
    :param skiprows: Number of rows to skip at the start of the file (default 0).
    :return: DataFrame with the raw data read from the file.
    """
    try:
        # Ensure the file path is a Path object
        file_path = local_paths['local_path'] / file_name

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
        return None


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
    ts_wl['rl'] = ts_wl['well_name'].map(rl_key).fillna(np.nan)
    ts_wl['diff_moturiki_nzdv2016'] = ts_wl['well_name'].map(rl_key1).fillna(np.nan)
    ts_wl['depth_to_water'] = ts_wl['rl'] - ts_wl['gw_elevation']
    ts_wl.drop(columns=['rl'], inplace=True)
    ts_wl['other'] = ts_wl['other'].astype(
        str) + "datum is motoriki, but rl data is nzvd2016 therefore depth to water???+-0.3m"
    return ts_wl


def process_st_wl(st_wl, rl_key):
    """
    Process static water level data. e.g. take the data out of the metadata and into format to merge with ts
    """
    st_wl['rl'] = st_wl['well_name'].map(rl_key).fillna(np.nan)
    st_wl['gw_elevation'] = st_wl['rl'] - st_wl['depth_to_water_static']
    st_wl.rename(columns={'depth_to_water_static': 'depth_to_water'}, inplace=True)
    assign_flags_based_on_null_values(st_wl, 'depth_to_water', 'dtw_flag', 2, 0)
    # Assign 'water_elev_flag' based on 'gw_elevation'
    assign_flags_based_on_null_values(st_wl, 'gw_elevation', 'water_elev_flag', 2, 0)
    st_wl.loc[:, 'data_source'] = "tccRC"
    st_wl.loc[:, 'elevation_datum'] = "NZVD2016"
    st_wl.loc[:, 'other'] = "static_wl"
    st_wl.loc[:, 'date'] = pd.to_datetime(None)
    st_wl['date'] = pd.to_datetime(st_wl['date'])
    st_wl = st_wl.drop(columns=['rl'])
    return st_wl


def determine_prefix(location):
    location = location.lower()
    if 'gw' in location or 'GW' in location:
        return 'gw-'
    else:
        return location.split()[0] + '-' if location else ''


def create_well_name(row):
    # Check if the extracted number is NaN or empty
    if pd.isna(row['extracted_number']):
        return row['prefix']
    if row['prefix'] == 'BN-':
        return row['prefix'] + str(row['extracted_number'])
    else:
        return row['prefix'].rstrip('-')


def convert_data_to_csv(local_paths):
    """This function reads in an Excel file, with each sheet containing data for a different site,
       and saves each sheet as a separate CSV file."""
    # Define the path to the Excel file
    data_path = local_paths[
                    'local_path'] / 'Copy of 20240614 BOPRC Breda Bavoldelli - GW Bore data All - up to Feb 2024 (A16072154).xlsx'

    # Load the Excel file metadata to get the sheet names
    xls = pd.ExcelFile(data_path)

    # Iterate over each sheet in the Excel file
    for sheet_name in xls.sheet_names:
        # Print the progress
        print(f"Processing sheet: {sheet_name}")

        # Read the sheet into a DataFrame
        df = pd.read_excel(xls, sheet_name=sheet_name)

        # Add a new column to DataFrame to store the site name
        df['site_name'] = sheet_name

        # Define the path for the CSV file
        csv_path = local_paths['local_path'].joinpath(f"{sheet_name}.csv")

        # Save the DataFrame to CSV
        df.to_csv(csv_path, index=False)

        # Print completion of the current sheet
        print(f"Completed saving {sheet_name} to CSV")

def _get_wl_tcc_data(local_paths, metadata):
    """This reads in the continuous timeseries data"""
    # need to read each sheet as it contains each sites data
    save_path = local_paths['local_path'].joinpath('tcc_wls.csv')

    if save_path.exists():
        merged = pd.read_csv(save_path)
        return merged
    else:

        data_path = local_paths['local_path']

        # Load the csv files
        df_dict = {}
        for file in data_path.glob('*.csv'):
            df = pd.read_csv(file)
            df_dict[file.stem] = df

        # List to collect modified DataFrames
        dataframes_to_concat = []

        # Iterate over dictionary items
        for site_name, df in df_dict.items():
            # Add a new column to DataFrame to store the site name
            df['site_name'] = site_name
            # Append the modified DataFrame to the list
            dataframes_to_concat.append(df)

        # Concatenate all DataFrames into a single DataFrame
        combined_df = pd.concat(dataframes_to_concat, ignore_index=True)
        combined_df.to_csv(local_paths['local_path'].joinpath('combined_wl_data.csv'))

        data_quality = combined_df[combined_df['site_name']== "Qualities"]
        wl_data = combined_df[combined_df['site_name'] != "Qualities"]
        # drop the first column in wl_data eg Qualities
        wl_data = wl_data.drop(columns=['Qualities:'])
        wl_data.reset_index(drop=True, inplace=True)
        wl_data = wl_data.rename(columns={'Bore Level (m)': 'gw_elev', 'site_name': 'well_name', 'Date': 'date', 'Time': 'time'})
        # merge date and time
        wl_data['date'] = pd.to_datetime(wl_data['date'], errors='coerce').dt.date

        # join date and time as new column
        wl_data['date_time'] = (wl_data['date'].astype(str) + ' ' + wl_data['time'].astype(str))
        wl_data['date_time'] = pd.to_datetime(wl_data['date_time'], errors='coerce')
        wl_data.drop(columns=['date', 'time'], inplace=True)



        df = wl_data.copy()
        df['data_source'] = "tcc"
        df['elevation_datum'] = "nzvd2016"
        # to account for the fact the data is average for period between midnight to midnight
        df = df.sort_values(['well_name', 'date_time'])
        # drop the '.GW' from the well name
        df['well_name'] = df['well_name'].str.replace('.GW', '')
        df['site_name'] = df['well_name'] + '_tcc'
        df = df[['well_name', 'date_time', 'gw_elev', 'data_source', 'site_name']]
        # make well_name and site_name lower case
        df['well_name'] = df['well_name'].str.lower()
        df['site_name'] = df['site_name'].str.lower()
        metadata['well_name'] = metadata['well_name'].str.lower()

        merged = df.merge(metadata, how='left', on='well_name')
        merged = merged.dropna()
        merged['rl_elevation'] = merged['rl_elevation'].astype(float)
        merged['gw_elev'] = merged['gw_elev'].astype(float)
        merged['depth_to_water'] = merged['rl_elevation'] - merged['gw_elev']
        merged= merged.rename(columns={'gw_elev': 'gw_elevation', 'date_time': 'date'})
        merged['other'] = 'na'
        merged['elevation_datum'] = 'nzvd2016'


        assign_flags_based_on_null_values(merged, 'depth_to_water', 'dtw_flag', 1, 0)
        # Assign 'water_elev_flag' based on 'gw_elevation'
        assign_flags_based_on_null_values(merged, 'gw_elevation', 'water_elev_flag', 1, 0)

        merged = merged.loc[:,
                ['well_name', 'date', 'depth_to_water', 'gw_elevation', 'dtw_flag', 'water_elev_flag', 'data_source',
                 'elevation_datum', 'other']]
        merged.to_csv(local_paths['local_path'].joinpath('tcc_wls.csv'))

        merged.dropna(subset=['gw_elevation'], inplace=True)

    return merged


def output(local_paths, meta_data_requirements, recalc=False):  #todo
    """This function pulls all the data and metadata together and outputs it to a hdf5 file
    :return: dataframe"""
    water_data_store_path = local_paths['save_path']
    store_key_water_data = local_paths['wl_store_key']
    store_key_metadata = local_paths['tcc_metadata_store_key']

    # Check if data needs to be recalculated or if the HDF files don't exist
    if not recalc and water_data_store_path.exists():
        combined_water_data = pd.read_hdf(water_data_store_path, store_key_water_data, )
        combined_metadata = pd.read_hdf(water_data_store_path, store_key_metadata)

    else:
        needed_gw_columns_type = {'well_name': "str", 'depth_to_water': "float", 'gw_elevation': "float",
                                  'dtw_flag': "int",
                                  'water_elev_flag': 'int', 'data_source': 'str', 'elevation_datum': "str",
                                  'other': "str"}
        needed_gw_columns = ['well_name', 'date', 'depth_to_water', 'gw_elevation',
                                  'dtw_flag','water_elev_flag', 'data_source', 'elevation_datum',
                                  'other']

        tcc_metadata = _get_metadata(local_paths=local_paths, file_name='GW Bore Metadata - For Breda.xlsx')
        tcc_metadata = tcc_metadata.drop(
            columns=['Coordinates World Geodetic System 1972 Easting ', 'Coordinates World Geodetic System 1972 Northing'])
        tcc_metadata = tcc_metadata.rename(
            columns={'HYDSTRA ID': 'well_name',
                     'Easting': 'nztm_x', 'Northing': 'nztm_y',
                     'Bore Depth (m)': 'well_depth',
                     'Ground Elevation (RL)\n': 'rl_elevation'})

        combined_water_data = _get_wl_tcc_data(local_paths=local_paths, metadata=tcc_metadata)

        combined_water_data['date'] = pd.to_datetime(combined_water_data['date']).dt.date
        combined_water_data['date'] = pd.to_datetime(combined_water_data['date'])
        combined_water_data = aggregate_water_data(combined_water_data)
        combined_water_data = combined_water_data.sort_values(by=['depth_to_water', "well_name"],
                                                              ascending=[True, True])

        stats = _get_summary_stats(combined_water_data)
        stats = stats.set_index('well_name')
        combined_metadata = tcc_metadata.copy()
        combined_metadata['well_name'] = combined_metadata['well_name'].str.lower()
        combined_metadata = combined_metadata.set_index('well_name')

        combined_metadata = combined_metadata.combine_first(stats)
        combined_metadata = combined_metadata.reset_index()
        combined_metadata = combined_metadata.dropna()

        combined_metadata = combined_metadata.sort_values(by='well_name')
        combined_metadata = combined_metadata.reset_index(drop=True)
        combined_metadata = combined_metadata.dropna(subset=['well_name'])

        # this should return an empty list (test)
        combined_water_data_names = combined_water_data['well_name'].unique()
        # check names in metadata
        combined_metadata_names = combined_metadata['well_name'].unique()
        missing_names = [name for name in combined_water_data_names if name not in combined_metadata_names]
        if len(missing_names) > 0:
            raise ValueError(
                f"The following well names are in the water data but not in the metadata: {missing_names}"
            )

        combined_metadata = combined_metadata.sort_values(by=['well_name', 'start_date'], ascending=[True, True])
        combined_metadata["artesian"] = np.where(
            combined_metadata['min_dtw'] < 0,  # Else, if 'min_gwl' < 0 (regardless of 'depth_to_water_static')
            True,  # Then also set to True
            False  # Else, set to False
        )

        if 'other' not in combined_metadata.columns:
            combined_metadata['other'] = ''

        for col in meta_data_requirements['needed_columns']:
            if col not in combined_metadata.columns:
                combined_metadata[col] = meta_data_requirements['default_values'].get(col)

        for col, dtype in meta_data_requirements['col_types'].items():
            combined_metadata[col] = combined_metadata[col].astype(dtype)

        combined_metadata = append_to_other(df=combined_metadata,
                                            needed_columns=meta_data_requirements["needed_columns"])

        combined_metadata.drop(columns=[col for col in combined_metadata.columns if
                                        col not in meta_data_requirements["needed_columns"] and col != 'other'],
                               inplace=True)

        combined_metadata['start_date'] = pd.to_datetime(combined_metadata['start_date'])
        combined_metadata['end_date'] = pd.to_datetime(combined_metadata['end_date'])

        data_checks(combined_water_data)
        metadata_checks(combined_metadata)

        # Condition for finding NaNs in both column1 and column2
        condition = combined_metadata['mean_dtw'].isna() & combined_metadata['mean_gwl'].isna()

        # Inverting the condition to keep rows that do not meet the criteria
        rows_to_keep = ~condition

        # Applying the condition to the DataFrame
        combined_metadata = combined_metadata[rows_to_keep]

        combined_metadata['rl_elevation'] = combined_metadata['mp_elevation_NZVD'].astype(float)

        cols_to_keep = [
            'well_name', 'rl_elevation', 'rl_datum', 'rl_source',
            'ground_level_datum', 'ground_level_source', 'well_depth', 'top_topscreen',
            'bottom_bottomscreen', 'nztm_x', 'nztm_y', 'other', 'dist_mp_to_ground_level'
        ]

        combined_metadata = append_to_other(df=combined_metadata, needed_columns=cols_to_keep)
        combined_metadata.drop(columns=[col for col in combined_metadata.columns if
                                        col not in cols_to_keep and col != 'other'],
                               inplace=True)

        combined_water_data = combined_water_data[needed_gw_columns]
        # set to the right data types from dict
        combined_water_data = combined_water_data.astype(needed_gw_columns_type)

        # check save path exists
        if not local_paths['save_path'].parent.exists():
            os.makedirs(local_paths['save_path'].parent)

        renew_hdf5_store(new_data=combined_water_data, old_path=local_paths['save_path'],
                         store_key=local_paths['wl_store_key'])
        renew_hdf5_store(new_data=combined_metadata, old_path=local_paths['save_path'],
                         store_key=local_paths['tcc_metadata_store_key'])
        return combined_metadata, combined_water_data

    return {'combined_metadata': combined_metadata, 'combined_water_data': combined_water_data}


########################################################################################################################
""" read in the file paths and create local dirs"""


def _get_folder_and_local_paths(source_dir, local_dir, redownload=False):
    """This function reads in the file paths and creates local directories"""
    # Source directory based on the provided 'directory' parameter
    local_base_path = local_dir
    src_dir = groundwater_data.joinpath(source_dir)
    dst_dir = local_dir.joinpath(src_dir.name)
    # Initialize the local directory map
    local_dir_map = {}

    # Determine the destination directory

    if redownload:
        if src_dir.is_file():
            overlapping_items = [dst_dir] if dst_dir.exists() else []
        else:
            overlapping_items = find_overlapping_files(src_dir, dst_dir)
        copy_with_prompt(src_dir, dst_dir, overlapping_items)

    local_dir_map[src_dir.name] = dst_dir

    # Construct paths for specific data within the local directory
    local_path_mapping = local_dir_map.get(src_dir.name)
    local_paths = {
        'water_level_data': local_path_mapping.joinpath("tethys_water_level_data"),
        'water_depth_data': local_path_mapping.joinpath("tethys_gw_depth_data"),
        'water_level_metadata': local_path_mapping.joinpath("water_level_all_stations.csv"),
        'water_depth_metadata': local_path_mapping.joinpath("groundwater_depth_all_stations.csv"),
        'thethys_local_save_path': local_base_path.joinpath("gwl_tcc", "cleaned_data", "tethys_gw_data.hdf"),
        'local_path': local_path_mapping
    }

    # Store keys are hardcoded as they are specific to this setup
    local_paths['wl_store_key'] = 'tcc_gwl_data'
    local_paths['tcc_metadata_store_key'] = 'tcc_metadata'
    local_paths['save_path'] = groundwater_data.joinpath('gwl_tcc', 'cleaned_data', 'combined_tcc_data.hdf')

    return local_paths


def get_tcc_data(recalc=False, redownload=False):
    local_paths = _get_folder_and_local_paths(source_dir=groundwater_data.joinpath('gwl_tauranga'),
                                              local_dir=unbacked_dir.joinpath('tcc_working/'), redownload=redownload)
    meta_data_requirements = needed_cols_and_types("TCC")
    return output(local_paths, meta_data_requirements, recalc=recalc)


########################################################################################################################


save_path = groundwater_data.joinpath('gwl_tauranga', 'cleaned_data', 'combined_tcc_data.hdf')
wl_store_key = 'tcc_gwl_data'
tauranga_metadata_store_key = 'tcc_metadata'

if __name__ == '__main__':
    local_paths = _get_folder_and_local_paths(source_dir=groundwater_data.joinpath('gwl_tauranga'),
                                              local_dir=unbacked_dir.joinpath('tcc_working/'), redownload=False)
    data = get_tcc_data(recalc=False, redownload=False)
    # keynote gwc1ai is unreliable
    t=1
