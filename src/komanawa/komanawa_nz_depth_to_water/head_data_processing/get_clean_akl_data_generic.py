"""
created Evelyn_Charlesworth 
on: 30/05/2023
"""
"""This Python script cleans and processes the Auckland GWL timeseries data"""

import os
import numpy as np
import pandas as pd
from data_processing_functions import find_overlapping_files, copy_with_prompt, \
    _get_summary_stats, append_to_other, needed_cols_and_types, data_checks, \
    metadata_checks, renew_hdf5_store, assign_flags_based_on_null_values
from project_base import groundwater_data, unbacked_dir
import re

needed_gw_columns = ['well_name', 'date', 'depth_to_water', 'gw_elevation', 'dtw_flag', 'water_elev_flag',
                     'data_source', 'elevation_datum', 'other']

needed_gw_columns_type = {'well_name': "str", 'depth_to_water': "float", 'gw_elevation': "float", 'dtw_flag': "int",
                          'water_elev_flag': 'int',
                          'data_source': 'str', 'elevation_datum': "str", 'other': "str"}


def _get_akl_gwl_data(local_paths, recalc=False):
    """ A function that reads in the raw Akl data. There are a large number of spreadsheets downloaded from the data site
    This reads them in, creates a column with the well_name and joins them all to create one big dataframe
    :return: dataframe, the combined GWL data"""

    # the folder path where the data is stored
    folder_path = local_paths['local_path'] / 'Downloaded_data'
    save_path = local_paths['local_path'] / 'combined_akl_data.hdf'
    store_key = 'akl_gwl_data'

    if save_path.exists() and not recalc:
        combined_data = pd.read_hdf(save_path, store_key)
    else:
        data = []
        for filename in os.listdir(folder_path):
            site_name = re.search(r'@(\d+)-', filename).group(1)
            file_path = os.path.join(folder_path, filename)
            df = pd.read_csv(file_path, skiprows=1)
            df['well_name'] = site_name  # Assign extracted site name to the new column
            # Process and rename columns as needed
            data.append(df)

        # Combine all dataframes into one
        combined_data = pd.concat(data, ignore_index=True)
        # Save the combined dataframe to an HDF5 file
        combined_data = combined_data.rename(columns={'Timestamp (UTC+12:00)': 'date', 'Value (m)': 'gw_elevation'})

        combined_data['date'] = pd.to_datetime(combined_data['date'], dayfirst=True, format='mixed')
        combined_data['year'] = combined_data['date'].dt.year
        combined_data['month'] = combined_data['date'].dt.month
        combined_data['day'] = combined_data['date'].dt.day

        daily_average_data = \
            combined_data.groupby(['well_name', 'year', 'month', 'day'])[
                ['gw_elevation']].mean().reset_index()
        # If needed, reconstruct the 'date' from the grouped year, month, and day
        daily_average_data['date'] = pd.to_datetime(daily_average_data[['year', 'month', 'day']])
        # Drop the year, month, and day columns if they are no longer needed
        daily_average_data = daily_average_data.drop(columns=['year', 'month', 'day'])
        combined_data = daily_average_data

        for column in needed_gw_columns:
            if column not in combined_data.columns:
                # Add the missing column and initialize with NaNs or another suitable default value
                combined_data[column] = np.nan


        renew_hdf5_store(new_data=combined_data, old_path=save_path, store_key=store_key)

    return combined_data


def _get_wq_akl_data(local_paths):
    """ This function reads the extra data sent by Akl - this is any water level data from the water quality sites
    :return: dataframe, raw wq site data
    """

    # keynote this is depth to water data
    # creating the read path
    read_path = local_paths['local_path'] / '230406_GW_bore water level.csv'
    akl_wq_sites = pd.read_csv(read_path)

    # handling date
    akl_wq_sites['Date'] = pd.to_datetime(akl_wq_sites['Date'], format='%d/%m/%Y')

    # dropping unnecessary columns
    columns_to_drop = ['Measuring program', 'Sample time', 'Laboratory', 'Analysis method (Name)',
                       'Analysis method (Short name)', 'Parameter type name', 'Parameter type short name', 'Sign',
                       'Lab raw value', 'Detection limit', 'Parameter quality code', 'Unit name', 'Sampling number',
                       'Comment of sampling ', 'Status (Excluded; Incomplete; Unconfirmed; Confirmed) (-1; 0; 1; 2)']
    akl_wq_sites.drop(columns=columns_to_drop, inplace=True)

    akl_wq_sites = akl_wq_sites.rename(columns={'Station name': 'alt_well_name', 'Station number': 'well_name', 'Date': 'date',
                 'Value': 'depth_to_water'})
    # adding in data source
    for column in needed_gw_columns:
        if column not in akl_wq_sites.columns:
            # Add the missing column and initialize with NaNs or another suitable default value
            akl_wq_sites[column] = np.nan
    akl_wq_sites = akl_wq_sites.sort_values(by=['well_name', 'date'], ascending=[True, True])
    akl_wq_sites['dtw_flag'] = 2
    akl_wq_sites['data_source'] = 'GARC'

    return akl_wq_sites


def _get_hydstra_akl_data(local_paths):
    """ This function reads and reformats the extra data sent by Akl - these are the hydstra sites
    :return dataframe, reformatted hydstra data
    """

    # reading in the first file
    read_path = local_paths['local_path'] / '230501 hydstra GWL sites 110.CSV'
    akl_hydstra_sites_110 = pd.read_csv(read_path, skiprows=[1,2,3])

    # turning the dataframe from wide to long
    #  keynote this is depth to water data
    melted_akl_hydstra_sites_110 = pd.melt(akl_hydstra_sites_110, id_vars=['Time'], var_name='well_name',
                                          value_name='depth_to_water')
    # renaming the time/date column
    melted_akl_hydstra_sites_110 = melted_akl_hydstra_sites_110.rename(columns={'Time': 'date'})
    melted_akl_hydstra_sites_110= melted_akl_hydstra_sites_110.dropna(subset='depth_to_water')

    # now reading in the second file
    file_path_1 = local_paths['local_path'] / '230501 hydstra GWL sites 115.CSV'
    akl_hydstra_sites_115 = pd.read_csv(file_path_1, skiprows=[1, 2, 3])

    # turning the dataframe from wide to long
    melted_akl_hydstra_sites_115 = pd.melt(akl_hydstra_sites_115, id_vars=['Time'], var_name='well_name',
                                           value_name='gw_elevation')

    # renaming the time/date column
    melted_akl_hydstra_sites_115 = melted_akl_hydstra_sites_115.rename(columns={'Time': 'date'})
    melted_akl_hydstra_sites_115= melted_akl_hydstra_sites_115.dropna(subset='gw_elevation')
    # combining the two dataframes
    combined_data = pd.concat([melted_akl_hydstra_sites_110, melted_akl_hydstra_sites_115],
                                          ignore_index=True)

    combined_data['date'] = pd.to_datetime(combined_data['date'], dayfirst= True, format= 'mixed')
    combined_data['year'] = combined_data['date'].dt.year
    combined_data['month'] = combined_data['date'].dt.month
    combined_data['day'] = combined_data['date'].dt.day

    daily_average_data = \
        combined_data.groupby(['well_name', 'year', 'month', 'day'])[
            ['gw_elevation', 'depth_to_water']].mean().reset_index()
    # If needed, reconstruct the 'date' from the grouped year, month, and day
    daily_average_data['date'] = pd.to_datetime(daily_average_data[['year', 'month', 'day']])
    # Drop the year, month, and day columns if they are no longer needed
    daily_average_data = daily_average_data.drop(columns=['year', 'month', 'day'])
    combined_data = daily_average_data

    for column in needed_gw_columns:
        if column not in combined_data.columns:
            # Add the missing column and initialize with NaNs or another suitable default value
            combined_data[column] = np.nan

    return combined_data


def _get_akl_metadata(local_paths, meta_data_requirements):
    """ Reads in the bulk of the metadata summary, as sent by Freya from Auckland council

    :return: dataframe, the raw Auckland metadata
    """

    # defining the path
    file_path = local_paths['local_path'] / 'Metadata' / '230509 Metadata summary.xlsx'

    # reading in the data
    metadata = pd.read_excel(file_path)
    metadata = metadata.rename(columns={'Site number': 'well_name', 'Site name': 'alt_well_name', 'Easting': 'nztm_x',
                                        'Northing': 'nztm_y', 'Elevation to top of casing': 'mp_elevation_NZVD',
                                        'Datum top of casing': 'rl_datum',
                                        'bore depth (m)': 'well_depth', 'screen top depth (m)': 'top_topscreen',
                                        'screen base depth (m)': 'bottom_bottomscreen',
                                        'Elevation of ground next to bore': 'ground_elevation',
                                        'Datum next to bore': 'ground_level_datum'})

    for col in meta_data_requirements['needed_columns']:
        if col not in metadata.columns:
            metadata[col] = meta_data_requirements['default_values'].get(col)

    metadata['dist_mp_to_ground_level'] = metadata['mp_elevation_NZVD']- metadata['ground_elevation']
    metadata['rl_elevation'] = np.where(pd.notnull(metadata['mp_elevation_NZVD']), metadata['mp_elevation_NZVD'],
                                        metadata['ground_elevation'])

    for col, dtype in meta_data_requirements['col_types'].items():
        metadata[col] = metadata[col].astype(dtype)

    metadata = append_to_other(df=metadata, needed_columns=meta_data_requirements['needed_columns'])
    metadata = metadata.drop(columns=[col for col in metadata.columns if
                                      col not in meta_data_requirements['needed_columns'] and col != 'other'])

    metadata['start_date'] = pd.to_datetime(metadata['start_date'], format='mixed')
    metadata['end_date'] = pd.to_datetime(metadata['end_date'], format='mixed')

    return metadata


def output(local_paths, meta_data_requirements, recalc= False):  #
    """This function combines the two sets of metadata and cleans it
    :return: dataframe
    dtw_flag = 0= no_data, 1= logger, 2= manual, 3= static_oneoff, 4= calculated frm gw_elevation, 5= aquifer test, 6= other
    water_ele_flag = 1= logger, 2= manual, 3= static_oneoff, 4= aquifer test, 5= other
    """
    water_data_store_path = local_paths['save_path']
    store_key_water_data = local_paths['wl_store_key']
    store_key_metadata = local_paths['akl_metadata_store_key']

    # Check if data needs to be recalculated or if the HDF files don't exist
    if not recalc and water_data_store_path.exists():
        combined_water_data = pd.read_hdf(water_data_store_path, store_key_water_data)
        combined_metadata = pd.read_hdf(water_data_store_path, store_key_metadata)
    else:
        needed_gw_columns_type = {'well_name': "str", 'depth_to_water': "float", 'gw_elevation': "float", 'dtw_flag': "int",
                                  'water_elev_flag': 'int',
                                  'data_source': 'str', 'elevation_datum': "str", 'other': "str"}
        akl_metadata = _get_akl_metadata(local_paths, meta_data_requirements)


        akl_hydrstra = _get_hydstra_akl_data(local_paths)
        assign_flags_based_on_null_values(akl_hydrstra, 'depth_to_water', 'dtw_flag', 1, 0)
        assign_flags_based_on_null_values(akl_hydrstra, 'gw_elevation', 'water_elev_flag', 1, 0)

        akl_wq = _get_wq_akl_data(local_paths)
        # dtw for wql sites looks to be ~1m accuracy....
        assign_flags_based_on_null_values(akl_wq, 'depth_to_water', 'dtw_flag', 6, 0)
        assign_flags_based_on_null_values(akl_wq, 'gw_elevation', 'water_elev_flag', 5, 0)
        akl_wq= akl_wq.drop(columns=['alt_well_name'])

        akl_gwl = _get_akl_gwl_data(local_paths, recalc=False)
        assign_flags_based_on_null_values(akl_gwl, 'depth_to_water', 'dtw_flag', 1, 0)
        assign_flags_based_on_null_values(akl_gwl, 'gw_elevation', 'water_elev_flag', 1, 0)


        combined_water_data = pd.concat([akl_wq, akl_hydrstra, akl_gwl], ignore_index=True)
        combined_water_data['data_source'] = 'GARC'

        combined_metadata = pd.concat([akl_metadata], ignore_index=True)
        elevation_data = combined_metadata[['well_name', 'rl_elevation', 'rl_datum']]
        combined_water_data = combined_water_data.merge(elevation_data, on='well_name', how='left')
        condition = pd.isnull(combined_water_data['depth_to_water']) & pd.notnull(combined_water_data['rl_elevation'])
        combined_water_data['depth_to_water'] = np.where(condition,
                                                         combined_water_data['rl_elevation'] - combined_water_data[
                                                             'gw_elevation'], combined_water_data['depth_to_water'])
        combined_water_data['dtw_flag'] = np.where(condition, 4, combined_water_data['dtw_flag'])
        combined_water_data['elevation_datum'] = combined_water_data['rl_datum']
        combined_water_data = combined_water_data.drop(columns=['rl_elevation', 'rl_datum'])
        combined_water_data = combined_water_data.sort_values(by=['well_name', 'depth_to_water'], ascending=[True, True])
        combined_water_data['well_name'] = combined_water_data['well_name'].astype(str)
        data_checks(combined_water_data)

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

        combined_metadata = append_to_other(df=combined_metadata, needed_columns=meta_data_requirements["needed_columns"])

        combined_metadata.drop(columns=[col for col in combined_metadata.columns if
                                        col not in meta_data_requirements["needed_columns"] and col != 'other'],
                               inplace=True)


        metadata_checks(combined_metadata)

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
                         store_key=local_paths['akl_metadata_store_key'])

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
        'auckland_local_save_path': local_base_path.joinpath("gwl_akl", "cleaned_data", "akl_gw_data.hdf"),
        'local_path': local_path_mapping
    }

    # Store keys are hardcoded as they are specific to this setup
    local_paths['wl_store_key'] = 'akl_gwl_data'
    local_paths['akl_metadata_store_key'] = 'akl_metadata'
    local_paths['save_path'] = groundwater_data.joinpath('gwl_akl', 'cleaned_data', 'combined_akl_data.hdf')

    return local_paths

def get_auk_data(recalc=False, redownload = False):
    local_paths = _get_folder_and_local_paths(source_dir=groundwater_data.joinpath('gwl_akl'),
                                              local_dir=unbacked_dir.joinpath('auckland_working/'), redownload=redownload)
    meta_data_requirements = needed_cols_and_types('akl')
    return output(local_paths, meta_data_requirements, recalc = recalc)

if __name__ == '__main__':
    data = get_auk_data(recalc=True)
    pass
