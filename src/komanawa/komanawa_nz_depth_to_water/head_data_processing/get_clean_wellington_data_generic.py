"""
created Patrick Durney and Evelyn_Charlesworth
on: 8-2-2024
"""

"""This script cleans and processes the Wellington GWL data"""

import numpy as np
import pandas as pd

from data_processing_functions import find_overlapping_files, copy_with_prompt, \
    _get_summary_stats, needed_cols_and_types, metadata_checks, \
    data_checks, get_hdf5_store_keys, pull_tethys_data_store, append_to_other, renew_hdf5_store, parse_and_identify, \
    assign_flags_based_on_null_values, aggregate_water_data
from project_base import groundwater_data, unbacked_dir
from merge_rows import merge_rows_if_possible


def _get_wellington_tethys_data(local_paths, meta_data_requirements):
    """" This function reads in the gisborne data from Tethys
            dtw_flag = 1= logger, 2= manual, 3= static_oneoff, 4= calculated frm gw_elevation, 5= aquifer test, 6= other
    water_ele_flag = 1= logger, 2= manual, 3= static_oneoff, 4= aquifer test, 5= other
    """
    needed_gw_columns = ['well_name', 'date', 'depth_to_water', 'gw_elevation', 'dtw_flag', 'water_elev_flag',
                         'data_source', 'elevation_datum', 'other']

    needed_gw_columns_type = {'well_name': "str", 'depth_to_water': "float", 'gw_elevation': "float", 'dtw_flag': "int",
                              'water_elev_flag': 'int',
                              'data_source': 'str', 'elevation_datum': "str", 'other': "str"}

    data_keys = get_hdf5_store_keys(unbacked_dir.joinpath('tetheys_2024_all', 'tethys_fully_processed.hdf'))
    meta_keys = get_hdf5_store_keys(unbacked_dir.joinpath('tetheys_2024_all', 'tethys_meta_fully_processed.hdf'))

    tethys_data = pull_tethys_data_store(unbacked_dir.joinpath('tetheys_2024_all', 'tethys_fully_processed.hdf'),
                                         data_keys,
                                         council="Wellington")
    tethys_metadata = pull_tethys_data_store(
        unbacked_dir.joinpath('tetheys_2024_all', 'tethys_meta_fully_processed.hdf'),
        meta_keys, council="Wellington")

    tethys_metadata_dtw_24h = tethys_metadata['/Greater Wellington Regional Council_groundwater_depth_24H_metadata']

    tethys_data_dtw_24h = tethys_data['/Greater Wellington Regional Council_groundwater_depth_24H']
    tethys_data_dtw_24h['depth_to_water'] = tethys_data_dtw_24h['groundwater_depth']
    tethys_data_dtw_24h['well_name'] = tethys_data_dtw_24h['ref']

    tethys_data_dtw = tethys_data_dtw_24h[needed_gw_columns]
    tethys_data_dtw['data_source'] = "tethys"

    assign_flags_based_on_null_values(tethys_data_dtw, 'depth_to_water', 'dtw_flag', 1, 0)
    assign_flags_based_on_null_values(tethys_data_dtw, 'gw_elevation', 'water_elev_flag', 1, 0)

    for col in meta_data_requirements['needed_columns']:
        if col not in tethys_metadata_dtw_24h.columns:
            tethys_metadata_dtw_24h[col] = meta_data_requirements['default_values'].get(col)

    for col, dtype in meta_data_requirements['col_types'].items():
        tethys_metadata_dtw_24h[col] = tethys_metadata_dtw_24h[col].astype(dtype)
    # review figure out what to do with those that don't have coordinates etc
    if 'other' not in tethys_metadata_dtw_24h.columns:
        tethys_metadata_dtw_24h['other'] = ''

    tethys_metadata_dtw_24h = append_to_other(df=tethys_metadata_dtw_24h,
                                              needed_columns=meta_data_requirements["needed_columns"])
    tethys_metadata_dtw_24h = tethys_metadata_dtw_24h[meta_data_requirements['needed_columns']]
    tethys_metadata_dtw_24h['source'] = 'tethys'
    tethys_metadata_dtw_24h['start_date'] = pd.to_datetime(tethys_metadata_dtw_24h['start_date'])
    tethys_metadata_dtw_24h['end_date'] = pd.to_datetime(tethys_metadata_dtw_24h['end_date'])

    return {'tethys_groundwater_data': tethys_data_dtw,
            'tethys_metadata_combined': tethys_metadata_dtw_24h}


def _get_bespoke_wellington_data(path_lists, meta_data_requirements):
    """This function reads in the sporadic wellington data
    :returns: dataframe
    """
    needed_gw_columns = ['well_name', 'date', 'depth_to_water', 'gw_elevation', 'dtw_flag', 'water_elev_flag',
                         'data_source', 'elevation_datum', 'other']

    needed_gw_columns_type = {'well_name': "str", 'depth_to_water': "float", 'gw_elevation': "float", 'dtw_flag': "int",
                              'water_elev_flag': 'int',
                              'data_source': 'str', 'elevation_datum': "str", 'other': "str"}

    wrc_data_path = local_paths['water_sporadic_data'] / 'Wells_and_Bores.csv'
    # reading in the data
    wrc_data = pd.read_csv(wrc_data_path)

    # renaming columns
    new_names = {'WELL_NO': 'well_name', 'X': 'nztm_x', 'Y': 'nztm_y', 'DATE_DRILLED': 'date',
                 'REFERENCE_RL': 'rl_elevation', 'REFERENCE_DESCRIPTION': 'reference_description',
                 'GROUND_RL': 'ground_elevation', 'DEPTH': 'well_depth', 'DIAMETER': 'diameter',
                 'TOP_SCREEN_1': 'top_topscreen', 'BOTTOM_SCREEN_1': 'bottom_topscreen',
                 'TOP_SCREEN_2': 'top_bottomscreen', 'INITIAL_SWL': 'depth_to_water',
                 'BOTTOM_SCREEN_2': 'bottom_bottomscreen', 'AQUIFER_TYPE': 'aquifer', 'WRC_GROUNDWATER_ZONE': 'gw_zone'}

    keep_names = ['well_name', 'nztm_x', 'nztm_y', 'date',
                  'rl_elevation', 'reference_description',
                  'ground_elevation', 'well_depth', 'diameter',
                  'top_topscreen', 'bottom_topscreen',
                  'top_bottomscreen', 'depth_to_water',
                  'bottom_bottomscreen', 'aquifer', 'gw_zone']

    wrc_data.rename(columns=new_names, inplace=True)
    wrc_data = wrc_data[keep_names]

    # Check if 'Date' or 'date' is in the DataFrame columns
    if 'Date' in wrc_data.columns:
        date_column = 'Date'

    elif 'date' in wrc_data.columns:
        date_column = 'date'
    else:
        date_column = None

    if date_column:
        # Apply the function to the date column and create a new DataFrame with the results
        wrc_data[date_column] = wrc_data[date_column].astype(str)
        date_info = wrc_data[date_column].apply(parse_and_identify)
        temp_df = pd.DataFrame(date_info.tolist(), columns=['date', 'type'], index=wrc_data.index)

        # Update the original DataFrame
        wrc_data['date'] = temp_df['date']
        # Optionally drop the 'type' column and the original date column if it was 'Date'
        if date_column and date_column != 'date':
            df = wrc_data.drop(columns=date_column)
    else:
        # If no date column exists, create one with NaT values
        wrc_data['date'] = pd.NaT

    wrc_data['date'] = pd.to_datetime(wrc_data['date'])

    for col in meta_data_requirements['needed_columns']:
        if col not in wrc_data.columns:
            wrc_data[col] = meta_data_requirements['default_values'].get(col)

    for col, dtype in meta_data_requirements['col_types'].items():
        wrc_data[col] = wrc_data[col].astype(dtype)

    wrc_data = wrc_data.dropna(subset=['well_name'])

    metadata = wrc_data

    # choosing which columns to keep
    gw_data = wrc_data[['well_name', 'date', 'depth_to_water', 'aquifer']]
    gw_data['data_source'] = 'wrc'
    for column in needed_gw_columns:
        if column not in gw_data.columns:
            # Add the missing column and initialize with NaNs or another suitable default value
            gw_data[column] = np.nan

    gw_data = gw_data.dropna(subset=['depth_to_water'])
    # Make 'depth_to_water' negative where 'aquifer' contains 'Flowing Artesian', and positive (absolute) otherwise
    gw_data['depth_to_water'] = np.where(
        gw_data['aquifer'].str.contains('Flowing Artesian', case=False, na=False),
        -gw_data['depth_to_water'].abs(),  # Negate the absolute value for 'Flowing Artesian'
        gw_data['depth_to_water'].abs()  # Ensure all other values are positive (absolute)
    )

    gw_data = gw_data.dropna(subset=['depth_to_water'])
    assign_flags_based_on_null_values(gw_data, 'depth_to_water', 'dtw_flag', 3, 0)
    assign_flags_based_on_null_values(gw_data, 'gw_elevation', 'water_elev_flag', 3, 0)
    for column, dtype in needed_gw_columns_type.items():
        gw_data[column] = gw_data[column].astype(dtype)

    return {'sporadic_wellington_data': gw_data,
            'metadata': metadata}


def output(local_paths, meta_data_requirements, recalc=False):
    """This function combines the two sets of metadata and cleans it
    :return: dataframe"""
    needed_gw_columns = ['well_name', 'date', 'depth_to_water', 'gw_elevation', 'dtw_flag', 'water_elev_flag',
                         'data_source', 'elevation_datum', 'other']

    needed_gw_columns_type = {'well_name': "str", 'depth_to_water': "float", 'gw_elevation': "float", 'dtw_flag': "int",
                              'water_elev_flag': 'int',
                              'data_source': 'str', 'elevation_datum': "str", 'other': "str"}
    water_data_store_path = local_paths['save_path']
    store_key_water_data = local_paths['wl_store_key']
    store_key_metadata = local_paths['wellington_metadata_store_key']

    # Check if data needs to be recalculated or if the HDF files don't exist
    if not recalc and water_data_store_path.exists():
        combined_water_data = pd.read_hdf(water_data_store_path, store_key_water_data)
        combined_metadata = pd.read_hdf(water_data_store_path, store_key_metadata)

    else:
        tethys_data = _get_wellington_tethys_data(local_paths, meta_data_requirements)
        tethy_gw_data = tethys_data['tethys_groundwater_data']
        tethy_gw_data['date'] = pd.to_datetime(tethy_gw_data['date'])
        tetheys_metadata = tethys_data['tethys_metadata_combined']
        wrc_data = _get_bespoke_wellington_data(path_lists=local_paths,
                                                meta_data_requirements=meta_data_requirements)
        wrc_metadata = wrc_data['metadata']
        wrc_gw_data = wrc_data['sporadic_wellington_data']
        wrc_gw_data['date'] = pd.to_datetime(wrc_gw_data['date'])

        combined_water_data = pd.concat([tethy_gw_data, wrc_gw_data], ignore_index=True)
        # Ensure 'date' is in date datetime format
        combined_water_data['date'] = pd.to_datetime(combined_water_data['date']).dt.date
        combined_water_data['date'] = pd.to_datetime(combined_water_data['date'])
        combined_water_data = aggregate_water_data(combined_water_data)
        combined_water_data = append_to_other(df=combined_water_data, needed_columns=needed_gw_columns)

        for column in combined_water_data:
            if column not in combined_water_data.columns:
                # Add the missing column and initialize with NaNs or another suitable default value
                combined_water_data[column] = np.nan

        combined_water_data.drop(columns=[col for col in combined_water_data.columns if
                                          col not in needed_gw_columns and col != 'other'],
                                 inplace=True)

        for column, dtype in needed_gw_columns_type.items():
            combined_water_data[column] = combined_water_data[column].astype(dtype)

        # combining the two metadata sets
        combined_metadata = pd.concat([tetheys_metadata, wrc_metadata], ignore_index=True)
        combined_metadata = combined_metadata[combined_metadata['well_name'].isin(combined_water_data['well_name'])]

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

        cols_to_keep = [
            'well_name', 'rl_elevation', 'rl_datum', 'rl_source',
            'ground_level_datum', 'ground_level_source', 'well_depth', 'top_topscreen',
            'bottom_bottomscreen', 'nztm_x', 'nztm_y', 'other', 'dist_mp_to_ground_level'
        ]

        combined_metadata = append_to_other(df=combined_metadata, needed_columns=cols_to_keep)
        combined_metadata.drop(columns=[col for col in combined_metadata.columns if
                                        col not in cols_to_keep and col != 'other'],
                               inplace=True)
        combined_metadata['well_name'] = combined_metadata['well_name'].astype(str)
        # combined_metadata['data_source'] = combined_metadata['data_source'].astype(float)
        # combined_metadata['elevation_datum'] = combined_metadata['elevation_datum'].astype(str)
        combined_metadata['other'] = combined_metadata['other'].astype(str)

        renew_hdf5_store(new_data=combined_water_data, old_path=local_paths['save_path'],
                         store_key=local_paths['wl_store_key'])
        renew_hdf5_store(new_data=combined_metadata, old_path=local_paths['save_path'],
                         store_key=local_paths['wellington_metadata_store_key'])

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
        'water_level_data': local_path_mapping.joinpath("tethys_water_level_data"),
        'water_depth_data': local_path_mapping.joinpath("tethys_gw_depth_data"),
        'water_sporadic_data': local_path_mapping.joinpath('gwl_sporadic_wellington'),
        'water_depth_metadata': local_path_mapping.joinpath("groundwater_depth_all_stations.csv"),
        'thethys_local_save_path': local_base_path.joinpath("gwl_wellington", "cleaned_data", "tethys_gw_data.hdf"),
        'local_path': local_path_mapping
    }

    # Store keys are hardcoded as they are specific to this setup
    local_paths['thethys_gw_depth_local_store_key'] = 'wellington_depth_data'
    local_paths['thethys_gw_level_local_store_key'] = 'wellington_gw_level_data'
    local_paths['wl_store_key'] = 'wellington_gwl_data'
    local_paths['wellington_metadata_store_key'] = 'wellington_metadata'
    local_paths['save_path'] = groundwater_data.joinpath('gwl_wellington', 'cleaned_data',
                                                         'combined_wellington_data.hdf')

    return local_paths


def get_gwrc_data(recalc=False, redownload=False):
    local_paths = _get_folder_and_local_paths(source_dir=groundwater_data.joinpath('gwl_west_coast'),
                                              local_dir=unbacked_dir.joinpath('west_coast_working/'),
                                              redownload=redownload)
    meta_data_requirements = needed_cols_and_types('WCRC')
    return output(local_paths, meta_data_requirements, recalc=recalc)


if __name__ == '__main__':
    data = get_gwrc_data(recalc=False)
