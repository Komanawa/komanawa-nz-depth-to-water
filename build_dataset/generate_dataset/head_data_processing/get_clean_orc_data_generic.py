"""
created Evelyn_Charlesworth 
on: 1/06/2023
"""
"""This Python script cleans and processes the ORC data"""

import os

import numpy as np
import pandas as pd

from build_dataset.generate_dataset.head_data_processing.data_processing_functions import find_overlapping_files, \
    copy_with_prompt, \
    _get_summary_stats, append_to_other, needed_cols_and_types, data_checks, \
    metadata_checks, renew_hdf5_store, assign_flags_based_on_null_values, aggregate_water_data
from build_dataset.generate_dataset.project_base import groundwater_data, unbacked_dir
from build_dataset.generate_dataset.head_data_processing.merge_rows import merge_rows_if_possible

needed_gw_columns = ['well_name', 'date', 'depth_to_water', 'gw_elevation', 'dtw_flag', 'water_elev_flag',
                     'data_source', 'elevation_datum', 'other']

needed_gw_columns_type = {'well_name': "str", 'depth_to_water': "float", 'gw_elevation': "float", 'dtw_flag': "int",
                          'water_elev_flag': 'int',
                          'data_source': 'str', 'elevation_datum': "str", 'other': "str"}


def _get_clutha_logger_data(local_paths, meta_data_requirements):
    """This function reads in the Clutha logger data provided by ORC
    :return dataframe
    """

    # reading in the data
    clutha_logger_data = pd.read_excel((
            local_paths['local_path'] / 'Clutha GWL data NZVD2016 hourly.xlsx'),
        sheet_name='Combined_elevation')

    # turning data from wide to long by melting
    # keynote the groundwater elevation data is in NZVD2016
    clutha_logger_data = pd.melt(clutha_logger_data, id_vars=['Date'], var_name='well_name', value_name='water_level')

    # renaming the date column
    clutha_logger_data.rename(columns={'Date': 'date', "water_level": 'gw_elevation'}, inplace=True)
    clutha_logger_data['date'] = pd.to_datetime(clutha_logger_data['date'], format='mixed')
    clutha_logger_data = clutha_logger_data.dropna(subset=['gw_elevation'])

    clutha_logger_data['date'] = pd.to_datetime(clutha_logger_data['date'])
    clutha_logger_data['year'] = clutha_logger_data['date'].dt.year
    clutha_logger_data['month'] = clutha_logger_data['date'].dt.month
    clutha_logger_data['day'] = clutha_logger_data['date'].dt.day

    # Group by 'well_name' and the extracted date parts, then calculate mean for the specified columns
    daily_average_data = \
        clutha_logger_data.groupby(['well_name', 'year', 'month', 'day'])[
            ['gw_elevation']].mean().reset_index()
    # If needed, reconstruct the 'date' from the grouped year, month, and day
    daily_average_data['date'] = pd.to_datetime(daily_average_data[['year', 'month', 'day']])
    # Drop the year, month, and day columns if they are no longer needed
    daily_average_data = daily_average_data.drop(columns=['year', 'month', 'day'])
    clutha_logger_data = daily_average_data

    clutha_logger_data['well_name'] = clutha_logger_data['well_name'].str.replace('_', '/')

    for column in needed_gw_columns:
        if column not in clutha_logger_data.columns:
            # Add the missing column and initialize with NaNs or another suitable default value
            clutha_logger_data[column] = np.nan

    return clutha_logger_data


def _get_orc_gwl_data(local_paths, meta_data_requirements, recalc=False):
    """
    A function that reads in the raw ORC groundwater level data and combines them into one dataframe
    :return: dataframe, the combined GWL data from the 8 spreadsheets provided
    """

    # uses a recalc method
    save_path = local_paths['local_path'] / 'Groundwater levels all sites' / 'combined_orc_data.hdf'
    store_key = 'orc_gwl_data'

    # Check if the combined data already exists and if recalculation is not requested
    if save_path.exists() and not recalc:
        # Load the combined groundwater level data from the HDF5 store
        combined_orc_gwl_df = pd.read_hdf(save_path, store_key)
    else:
        # list of file names in the folder
        path = local_paths['local_path'] / 'Groundwater levels all sites'
        # Initialize a list to store the DataFrames for each CSV file
        list_dfs = []
        # Loop through each file in the directory
        for file in os.listdir(path):
            # Construct the full path to the file
            file_path = path / file
            # Check if the current file is a CSV file
            if file_path.suffix == '.csv':
                # Read the CSV file, skipping the first 20 rows
                raw_df = pd.read_csv(file_path, skiprows=20)
                # Melt the DataFrame to restructure it
                melted_raw_df = pd.melt(raw_df, id_vars=['TimeStamp'], var_name='well_name',
                                        value_name='gw_elevation')
                # Simplify the 'well_name' column to only include the well number
                melted_raw_df['well_name'] = melted_raw_df['well_name'].str.split('@').str[1]
                # Add the processed DataFrame to the list
                list_dfs.append(melted_raw_df)
        combined_orc_gwl_df = pd.concat(list_dfs, ignore_index=True)

        # renaming the time stamp column
        combined_orc_gwl_df.rename(columns={'TimeStamp': 'date'}, inplace=True)
        combined_orc_gwl_df['date'] = pd.to_datetime(combined_orc_gwl_df['date'], format='mixed')

        combined_orc_gwl_df['year'] = combined_orc_gwl_df['date'].dt.year
        combined_orc_gwl_df['month'] = combined_orc_gwl_df['date'].dt.month
        combined_orc_gwl_df['day'] = combined_orc_gwl_df['date'].dt.day

        # Group by 'well_name' and the extracted date parts, then calculate mean for the specified columns
        daily_average_data = \
            combined_orc_gwl_df.groupby(['well_name', 'year', 'month', 'day'])[
                ['gw_elevation']].mean().reset_index()
        # If needed, reconstruct the 'date' from the grouped year, month, and day
        daily_average_data['date'] = pd.to_datetime(daily_average_data[['year', 'month', 'day']])
        # Drop the year, month, and day columns if they are no longer needed
        daily_average_data = daily_average_data.drop(columns=['year', 'month', 'day'])
        combined_orc_gwl_df = daily_average_data
        combined_orc_gwl_df = combined_orc_gwl_df.dropna(subset=['gw_elevation'])
        for column in needed_gw_columns:
            if column not in combined_orc_gwl_df.columns:
                # Add the missing column and initialize with NaNs or another suitable default value
                combined_orc_gwl_df[column] = np.nan

        renew_hdf5_store(new_data=combined_orc_gwl_df, old_path=save_path, store_key=store_key)

    return combined_orc_gwl_df


def _get_discrete_orc_data(local_paths, meta_data_requirements):
    """This function reads in the static water levels sent by Marc Ettema
    :return dataframe
    """

    # keynote this is depth to water data

    # reading in the data - doing the static water level data first
    all_data = pd.read_excel((local_paths['local_path'] / 'Copy of orc_metadata_site_list.xlsx'),
                             sheet_name='Well Details')

    # selecting columns for the static water level data
    static_water_level_data = all_data[['WellNumber', 'DepthToWater (initial or later 1st dipping)', "DrillDate"]]
    # renaming the columns
    new_names = {'WellNumber': 'well_name', 'DepthToWater (initial or later 1st dipping)': 'depth_to_water',
                 'DrillDate': 'date'}
    static_water_level_data = static_water_level_data.rename(columns=new_names)

    for column in needed_gw_columns:
        if column not in static_water_level_data.columns:
            # Add the missing column and initialize with NaNs or another suitable default value
            static_water_level_data[column] = np.nan
    static_water_level_data['date'] = pd.to_datetime(static_water_level_data['date'])

    return static_water_level_data


def _get_orc_metadata(local_paths, meta_data_requirements):
    """
    A function that reads in the raw ORC metadata
    :return: dataframe, the raw data read directly from the Excel spreadsheet
    """

    # defining the path
    orc_metadata_path = local_paths['local_path'] / 'ORC GW sites list.xlsx'

    # reading in the raw data
    metadata = pd.read_excel(orc_metadata_path)
    metadata['well_name'] = metadata['well_name'] = metadata['Data Set Id'].str.split('@').str[-1]
    metadata.rename(columns={'Start of Record': 'start_date', 'End of Record': 'end_date', 'Easting': 'nztm_x',
                             'Northing': 'nztm_y', 'WellDepth': 'well_depth', 'ScreenBottom': 'bottom_bottomscreen',
                             'ScreenTop': 'top_topscreen'}, inplace=True)

    for col in meta_data_requirements['needed_columns']:
        if col not in metadata.columns:
            metadata[col] = meta_data_requirements['default_values'].get(col)

    for col, dtype in meta_data_requirements['col_types'].items():
        metadata[col] = metadata[col].astype(dtype)

    metadata = append_to_other(df=metadata, needed_columns=meta_data_requirements['needed_columns'])
    metadata = metadata.drop(columns=[col for col in metadata.columns if
                                      col not in meta_data_requirements['needed_columns'] and col != 'other'])

    metadata['start_date'] = pd.to_datetime(metadata['start_date'], format='mixed')

    metadata['end_date'] = pd.to_datetime(metadata['end_date'], format='mixed')
    return metadata


def _get_discrete_orc_metadata(local_paths, meta_data_requirements):
    """ This function reads in the metadata for the discrete data sent by Marc Ettema
    :return dataframe
    """

    # reading in data
    metadata = pd.read_excel(local_paths['local_path'] / 'Copy of orc_metadata_site_list.xlsx',
                             sheet_name='Well Details')

    # dropping unnecessary columns
    drop_columns = ['Type', 'Owner', 'Driller', 'Use1', 'Use2', 'Use3', 'last_edited date', 'BoreLog', 'DrillMethod',
                    'Road_OR_Street', 'CasingMaterial', 'FMU', 'Rohe', 'DistrictCouncil', 'PumpRate_L_s',
                    'Location Accuracy QAR 1=best 4 is worst', 'ScreenNumber']

    metadata.drop(columns=drop_columns, inplace=True)

    # renaming columns
    metadata.rename(
        columns={
            'WellNumber': 'well_name',
            'WellName': 'alt_well_name',
            'Depth': 'well_depth',
            'Diameter': 'diameter',
            'DepthToWater (initial or later 1st dipping)': 'depth_to_water',
            'DrillDate': 'date',
            'EastingTM': 'nztm_x',
            'NorthingTM': 'nztm_y',
            'Elevation (MSD or Otago Datum =+100)': 'elevation unreliable',
            'AquiferType': 'aquifer_type',
            'ScreenFrom (M GL)': 'top_topscreen',
            'ScreenTo': 'bottom_bottomscreen',
            'Notes': 'comments',
            'MP_NZVD2016': 'mp_elevation_NZVD2016',
            'QAR_RL accuracy MP': 'elevation_accuracy',
            'Ground_RL Neg = GL below MP': 'ground_rl'
        }, inplace=True
    )

    for col in meta_data_requirements['needed_columns']:
        if col not in metadata.columns:
            metadata[col] = meta_data_requirements['default_values'].get(col)

    for col, dtype in meta_data_requirements['col_types'].items():
        metadata[col] = metadata[col].astype(dtype)

    metadata = append_to_other(df=metadata, needed_columns=meta_data_requirements['needed_columns'])
    metadata = metadata.drop(columns=[col for col in metadata.columns if
                                      col not in meta_data_requirements['needed_columns'] and col != 'other'])

    metadata['start_date'] = pd.to_datetime(metadata['start_date'], format='mixed')
    metadata['end_date'] = pd.to_datetime(metadata['end_date'], format='mixed')

    return metadata


def _get_clutha_logger_metadata(local_paths, meta_data_requirements):
    """This function reads in the clutha metadata
    :return dataframe
    """

    # reading data in
    metadata = pd.read_csv(local_paths['local_path'] / 'gis_piezo_base_info.csv')

    # dropping unnecessary columns
    drop_columns = ['Type', 'Owner', 'Driller', 'Use1', 'ScreenNumber', 'BoreLog', 'DrillMethod', 'Road_OR_Street',
                    'CasingMaterial']
    metadata.drop(columns=drop_columns, inplace=True)

    metadata.rename(
        columns={'WellNumber': 'well_name', 'WellName': 'alt_well_name', 'Depth': 'well_depth', 'Diameter': 'diameter',
                 'DepthToWater': 'depth_to_water', 'DrillDate': 'date', 'EastingTM': 'nztm_x',
                 'NorthingTM': 'nztm_y',
                 'Elevation': 'elevation', 'Location': 'location', 'Aquifer': 'aquifer', 'ScreenFrom': 'top_topscreen',
                 'ScreenTo': 'bottom_bottomscreen',
                 'Notes': 'comments', 'MP_NZVD2016': 'mp_elevation_NZVD', 'Ground_RL': 'ground_rl'}, inplace=True)

    for col in meta_data_requirements['needed_columns']:
        if col not in metadata.columns:
            metadata[col] = meta_data_requirements['default_values'].get(col)

    for col, dtype in meta_data_requirements['col_types'].items():
        metadata[col] = metadata[col].astype(dtype)

    metadata = append_to_other(df=metadata, needed_columns=meta_data_requirements['needed_columns'])
    metadata = metadata.drop(columns=[col for col in metadata.columns if
                                      col not in meta_data_requirements['needed_columns'] and col != 'other'])

    metadata['start_date'] = pd.to_datetime(metadata['start_date'], format='mixed')
    metadata['end_date'] = pd.to_datetime(metadata['end_date'], format='mixed')

    return metadata


def output(local_paths, meta_data_requirements, recalc=False):  #
    """This function pulls all the data and metadata together and outputs it to a hdf5 file
    :return: dataframe"""
    water_data_store_path = local_paths['save_path']
    store_key_water_data = local_paths['wl_store_key']
    store_key_metadata = local_paths['otago_metadata_store_key']

    # Check if data needs to be recalculated or if the HDF files don't exist
    if not recalc and water_data_store_path.exists():
        combined_water_data = pd.read_hdf(water_data_store_path, store_key_water_data)
        combined_metadata = pd.read_hdf(water_data_store_path, store_key_metadata)

    else:
        needed_gw_columns_type = {'well_name': "str", 'depth_to_water': "float", 'gw_elevation': "float",
                                  'dtw_flag': "int",
                                  'water_elev_flag': 'int', 'data_source': 'str', 'elevation_datum': "str",
                                  'other': "str"}

        cld = _get_clutha_logger_data(local_paths, meta_data_requirements)
        assign_flags_based_on_null_values(cld, 'depth_to_water', 'dtw_flag', 1, 0)
        # Assign 'water_elev_flag' based on 'gw_elevation'
        assign_flags_based_on_null_values(cld, 'gw_elevation', 'water_elev_flag', 1, 0)

        orc_gwl_data = _get_orc_gwl_data(local_paths, meta_data_requirements, recalc=False)
        assign_flags_based_on_null_values(orc_gwl_data, 'depth_to_water', 'dtw_flag', 1, 0)
        # Assign 'water_elev_flag' based on 'gw_elevation'
        assign_flags_based_on_null_values(orc_gwl_data, 'gw_elevation', 'water_elev_flag', 1, 0)

        orc_discrete_data = _get_discrete_orc_data(local_paths, meta_data_requirements)
        assign_flags_based_on_null_values(orc_discrete_data, 'depth_to_water', 'dtw_flag', 2, 0)
        # Assign 'water_elev_flag' based on 'gw_elevation'
        assign_flags_based_on_null_values(orc_discrete_data, 'gw_elevation', 'water_elev_flag', 2, 0)

        orc_metadata = _get_orc_metadata(local_paths, meta_data_requirements)
        orc_discrete_metadata = _get_discrete_orc_metadata(local_paths, meta_data_requirements)
        clutha_logger_metadata = _get_clutha_logger_metadata(local_paths, meta_data_requirements)

        combined_water_data = pd.concat([orc_gwl_data, cld, orc_discrete_data], ignore_index=True)
        combined_water_data['date'] = pd.to_datetime(combined_water_data['date']).dt.date
        combined_water_data['date'] = pd.to_datetime(combined_water_data['date'])
        combined_water_data = aggregate_water_data(combined_water_data)
        combined_water_data = combined_water_data.sort_values(by=['depth_to_water', "well_name"],
                                                              ascending=[True, True])

        combined_metadata = pd.concat([orc_metadata, orc_discrete_metadata, clutha_logger_metadata], ignore_index=True)
        default_precision = 0.1  # for example, default precision is 2 decimal places
        # create dict of precisis ofr none str columns
        precisions = {col: default_precision for col in combined_metadata.columns
                      if combined_metadata[col].dtype != object and not pd.api.types.is_datetime64_any_dtype(
                combined_metadata[col])}
        precisions['nztm_x'] = 50
        precisions['nztm_y'] = 50

        # Create a list of columns to skip, which are of string type
        skip_cols = [col for col in combined_metadata.columns
                     if
                     combined_metadata[col].dtype == object or pd.api.types.is_datetime64_any_dtype(
                         combined_metadata[col])]

        aggregation_functions = {col: np.nanmean for col in precisions}

        combined_metadata = merge_rows_if_possible(combined_metadata, on='well_name', precision=precisions,
                                                   skip_cols=skip_cols, actions=aggregation_functions)
        combined_metadata = combined_metadata.sort_values(by='well_name')
        combined_metadata = combined_metadata.reset_index(drop=True)

        # this should return an empty list (test)
        combined_water_data_names = combined_water_data['well_name'].unique()
        # check names in metadata
        combined_metadata_names = combined_metadata['well_name'].unique()
        test = [name for name in combined_water_data_names if name not in combined_metadata_names]
        if len(test) > 0: raise ValueError(
            f"The following well names are in the water data but not in the metadata: {test}")

        stats = _get_summary_stats(combined_water_data)
        stats = stats.set_index('well_name')
        combined_metadata = combined_metadata.set_index('well_name')
        combined_metadata = combined_metadata.combine_first(stats)
        combined_metadata = combined_metadata.reset_index()

        combined_metadata = combined_metadata.sort_values(by=['well_name', 'start_date'], ascending=[True, True])
        combined_metadata["artesian"] = np.where(
            combined_metadata['min_dtw'] < 0,  # Else, if 'min_gwl' < 0 (regardless of 'depth_to_water_static')
            True,  # Then also set to True
            False  # Else, set to False
        )

        if 'other' not in combined_metadata.columns:
            combined_metadata['other'] = ''

        combined_metadata = append_to_other(df=combined_metadata,
                                            needed_columns=meta_data_requirements["needed_columns"])

        combined_metadata.drop(columns=[col for col in combined_metadata.columns if
                                        col not in meta_data_requirements["needed_columns"] and col != 'other'],
                               inplace=True)

        data_checks(combined_water_data)
        metadata_checks(combined_metadata)
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

        renew_hdf5_store(new_data=combined_water_data, old_path=local_paths['save_path'],
                         store_key=local_paths['wl_store_key'])
        renew_hdf5_store(new_data=combined_metadata, old_path=local_paths['save_path'],
                         store_key=local_paths['otago_metadata_store_key'])
        return combined_water_data, combined_metadata

    return {'combined_water_data': combined_water_data, 'combined_metadata': combined_metadata}


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
        'orc_local_save_path': local_base_path.joinpath("gwl_orc", "cleaned_data", "orc_gw_data.hdf"),
        'local_path': local_path_mapping
    }

    # Store keys are hardcoded as they are specific to this setup
    local_paths['wl_store_key'] = 'otago_gwl_data'
    local_paths['otago_metadata_store_key'] = 'otago_metadata'
    local_paths['save_path'] = groundwater_data.joinpath('gwl_orc_data', 'cleaned_data', 'combined_otago_data.hdf')

    return local_paths


def get_orc_data(recalc=False, redownload=False):
    local_paths = _get_folder_and_local_paths(source_dir=groundwater_data.joinpath('gwl_orc_data'),
                                              local_dir=unbacked_dir.joinpath('otago_working/'), redownload=redownload)
    meta_data_requirements = needed_cols_and_types('ORC')
    return output(local_paths, meta_data_requirements, recalc=recalc)


if __name__ == '__main__':
    data = get_orc_data(recalc=True)

    pass
