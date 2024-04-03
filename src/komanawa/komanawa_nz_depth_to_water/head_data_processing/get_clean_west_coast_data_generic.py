"""
This Python script : processes the West Coast Regional Council groundwater data
created by: Patrick_Durney
on: 26/02/24
"""

import numpy as np
import pandas as pd
import warnings
from data_processing_functions import find_overlapping_files, copy_with_prompt, \
    _get_summary_stats, append_to_other, needed_cols_and_types, data_checks, \
    metadata_checks, renew_hdf5_store, assign_flags_based_on_null_values, aggregate_water_data
from merge_rows import merge_rows_if_possible
from project_base import groundwater_data, unbacked_dir


# keynote - sure as to this is depth to water (confirmed by council)

def output(local_paths, meta_data_requirements, recalc=False):  #
    """This function pulls all the data and metadata together and outputs it to a hdf5 file
    :return: dataframe"""
    water_data_store_path = local_paths['save_path']
    store_key_water_data = local_paths['wl_store_key']
    store_key_metadata = local_paths['wcrc_metadata_store_key']

    # Check if data needs to be recalculated or if the HDF files don't exist
    if not recalc and water_data_store_path.exists():
        combined_water_data = pd.read_hdf(water_data_store_path, store_key_water_data)
        combined_metadata = pd.read_hdf(water_data_store_path, store_key_metadata)

    else:
        needed_gw_columns = ['well_name', 'date', 'depth_to_water', 'gw_elevation', 'dtw_flag', 'water_elev_flag',
                             'data_source', 'elevation_datum', 'other']

        needed_gw_columns_type = {'well_name': "str", 'depth_to_water': float, 'gw_elevation': float, 'dtw_flag': int,
                                  'water_elev_flag': int, 'nztm_x': float, 'nztm_y': float,
                                  'data_source': 'str', 'elevation_datum': "str", 'other': "str"}

        wcrc_gwl_data = pd.read_excel(local_paths['local_path'] / 'West Coast bore DB latest.xlsx',
                                      sheet_name='Level and NGMP', skiprows=1)
        wcrc_gwl_data = wcrc_gwl_data.rename(
            columns={'Site Name': 'well_name', 'Date': 'date', 'Ground Water Level': 'depth_to_water',
                     'Easting': 'nztm_x', 'Northing': 'nztm_y'})

        assign_flags_based_on_null_values(wcrc_gwl_data, 'depth_to_water', 'dtw_flag', 2, 0)
        # Assign 'water_elev_flag' based on 'gw_elevation'
        assign_flags_based_on_null_values(wcrc_gwl_data, 'gw_elevation', 'water_elev_flag', 2, 0)

        wcrc_metadata = pd.read_excel(local_paths['local_path'] / 'West Coast bore DB latest.xlsx',
                                      sheet_name='Current Iris Data')
        wcrc_metadata = wcrc_metadata.rename(columns={'SiteName': 'site_name', 'BoreDepth': 'well_depth',
                                                      'BoreTopOfScreen': 'top_topscreen',
                                                      'BoreBottomOfScreen': 'bottom_bottomscreen',
                                                      'Easting': 'nztm_x', 'Northing': 'nztm_y', 'Other': 'other',
                                                      'StaticWaterLevel': 'depth_to_water',
                                                      'StaticWaterLevelDate': 'date',
                                                      'TopOfCollar': 'mp_to_ground_level',
                                                      'HilltopSiteName': 'well_name'})

        wcrc_gwl_spot_data = wcrc_metadata[['site_name', 'well_name', 'depth_to_water', 'date', 'nztm_x', 'nztm_y']]
        wcrc_gwl_spot_data = wcrc_gwl_spot_data.dropna(subset=['depth_to_water', 'date'])

        combined_water_data = pd.concat([wcrc_gwl_data, wcrc_gwl_spot_data], ignore_index=True)
        combined_water_data['well_name'] = combined_water_data['well_name'].str.lower()
        combined_water_data['well_name'] = combined_water_data['well_name'].str.replace(' gw ', '',
                                                                                        regex=False)
        combined_water_data['date'] = pd.to_datetime(combined_water_data['date']).dt.date
        combined_water_data['date'] = pd.to_datetime(combined_water_data['date'])

        combined_water_data = combined_water_data.sort_values(by=['depth_to_water', "well_name"],
                                                              ascending=[True, True])
        combined_water_data['nztm_x'] = combined_water_data['nztm_x'].astype('Int64')
        combined_water_data['nztm_y'] = combined_water_data['nztm_y'].astype('Int64')

        wcrc_metadata = pd.read_excel(local_paths['local_path'] / 'West Coast bore DB latest.xlsx',
                                      sheet_name='Current Iris Data')
        wcrc_metadata = wcrc_metadata.rename(columns={'SiteName': 'site_name', 'BoreDepth': 'well_depth',
                                                      'BoreTopOfScreen': 'top_topscreen',
                                                      'BoreBottomOfScreen': 'bottom_bottomscreen',
                                                      'Easting': 'nztm_x', 'Northing': 'nztm_y', 'Other': 'other',
                                                      'StaticWaterLevel': 'depth_to_water',
                                                      'StaticWaterLevelDate': 'date',
                                                      'TopOfCollar': 'mp_to_ground_level',
                                                      'HilltopSiteName': 'well_name'})
        wcrc_metadata = wcrc_metadata[
            ['well_name', 'site_name', 'well_depth', 'top_topscreen', 'bottom_bottomscreen', 'nztm_x', 'nztm_y',
             'depth_to_water', 'date', 'mp_to_ground_level']]

        combined_metadata = wcrc_metadata
        combined_metadata['well_name'] = combined_metadata['well_name'].str.lower()
        combined_metadata['well_name'] = combined_metadata['well_name'].str.replace(' gw ', '', regex=False)
        # combined_metadata['well_name'] = combined_metadata['well_name'].str.replace(' ', '_', regex=False)

        combined_water_data_names = wcrc_gwl_data.drop_duplicates(subset=['well_name']).reset_index(drop=True)

        combined_water_data_names = combined_water_data_names.dropna(subset=['well_name'])
        # combined_water_data_names['well_name'] = combined_water_data_names['well_name'].str.replace(' ', '_',
        #                                                                                             regex=False)

        # keynote - this should return an empty list but does not, there is no way of knowing from the data what the level monitoing bore numbers are!
        check = [name for name in combined_water_data_names['well_name'] if
                 name not in combined_metadata['well_name'].unique()]
        combined_water_data['well_name'] = np.where(pd.isnull(combined_water_data['well_name']),
                                                    combined_water_data['site_name'], combined_water_data['well_name'])
        combined_water_data.set_index('well_name', inplace=True)
        combined_metadata['well_name'] = np.where(pd.isnull(combined_metadata['well_name']),
                                                  combined_metadata['site_name'], combined_metadata['well_name'])
        combined_metadata = combined_metadata.dropna(subset=['well_name'])
        combined_metadata.set_index('well_name', inplace=True)

        combined_water_data = combined_water_data.combine_first(combined_metadata)
        combined_water_data = combined_water_data.reset_index()
        combined_metadata.reset_index()
        combined_water_data = combined_water_data.dropna(subset=['depth_to_water'])
        combined_water_data = combined_water_data.drop_duplicates(subset=['well_name', 'date'])
        combined_water_data = combined_water_data.sort_values(by=['well_name', 'date'], ascending=[True, True])
        combined_water_data['dtw_flag'] = combined_water_data['dtw_flag'].astype(float)
        combined_water_data['dtw_flag'] = np.where(pd.isnull(combined_water_data['dtw_flag']), 3,
                                                   combined_water_data['dtw_flag'])
        combined_water_data['water_elev_flag'] = 0

        combined_metadata = combined_metadata.sort_values(by='well_name')
        combined_water_data_sites = combined_water_data.drop_duplicates(subset=['well_name'])
        combined_metadata = pd.concat([combined_metadata, combined_water_data_sites], ignore_index=True)

        default_precision = 0.1  # for example, default precision is 2 decimal places
        # create dict of precisis ofr none str columns
        precisions = {col: default_precision for col in combined_metadata.columns
                      if combined_metadata[col].dtype != object and not pd.api.types.is_datetime64_any_dtype(
                combined_metadata[col])}
        precisions['nztm_x'] = 5
        precisions['nztm_y'] = 5

        # Create a list of columns to skip, which are of string type
        skip_cols = [col for col in combined_metadata.columns
                     if
                     combined_metadata[col].dtype == object or pd.api.types.is_datetime64_any_dtype(
                         combined_metadata[col])]

        aggregation_functions = {col: np.nanmean for col in precisions}

        combined_metadata = merge_rows_if_possible(combined_metadata, on='well_name', precision=precisions,
                                                   skip_cols=skip_cols, actions=aggregation_functions)
        combined_metadata = combined_metadata.sort_values(by='well_name').dropna(subset=['well_name'])
        combined_metadata = combined_metadata.drop(columns=['site_name'])

        # check names in metadata
        combined_metadata_names = combined_metadata['well_name'].unique()
        combined_water_data_names = combined_water_data['well_name'].unique()
        test = [name for name in combined_water_data_names if name not in combined_metadata_names]
        if len(test) > 0: warnings.warn(
            f"The following well names are in the water data but not in the metadata: {test}")

        combined_water_data['date'] = pd.to_datetime(combined_water_data['date'])
        stats = _get_summary_stats(combined_water_data)
        stats = stats.set_index('well_name')
        combined_metadata = combined_metadata.set_index('well_name')
        combined_metadata = combined_metadata.combine_first(stats)
        combined_metadata = combined_metadata.reset_index()

        for col, dtype in meta_data_requirements['col_types'].items():
            if col in combined_metadata.columns:
                # If column exists, convert its data type
                combined_metadata[col] = combined_metadata[col].astype(dtype)
            else:
                combined_metadata[col] = meta_data_requirements['default_values'].get(col)

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

        for col in needed_gw_columns:
            if col not in combined_water_data.columns:
                combined_water_data[col] = np.nan

        for col, dtype in needed_gw_columns_type.items():
            if col not in combined_water_data.columns:
                # If the column does not exist, create it and fill with NaN values
                combined_water_data[col] = np.nan
            # Convert the column to the specified data type
            combined_water_data[col] = combined_water_data[col].astype(dtype)

        combined_water_data = combined_water_data[needed_gw_columns]
        combined_water_data = combined_water_data[combined_water_data['well_name'] != 'Bertacco Farm No.1 GW @ Ahaura']

        combined_metadata = append_to_other(df=combined_metadata, needed_columns=cols_to_keep)
        combined_metadata.drop(columns=[col for col in combined_metadata.columns if
                                        col not in cols_to_keep and col != 'other'],
                               inplace=True)

        combined_metadata = combined_metadata[combined_metadata['well_name'] != 'Bertacco Farm No.1 GW @ Ahaura']
        combined_metadata['nztm_x'] = combined_metadata['nztm_x'].astype('float')
        combined_metadata['nztm_y'] = combined_metadata['nztm_y'].astype('float')

        renew_hdf5_store(new_data=combined_water_data, old_path=local_paths['save_path'],
                         store_key=local_paths['wl_store_key'])
        renew_hdf5_store(new_data=combined_metadata, old_path=local_paths['save_path'],
                         store_key=local_paths['wcrc_metadata_store_key'])
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
        'wcrc_local_save_path': local_base_path.joinpath("gwl_west_coast", "cleaned_data", "wcrc_gw_data.hdf"),
        'local_path': local_path_mapping
    }

    # Store keys are hardcoded as they are specific to this setup
    local_paths['wl_store_key'] = 'wcrc_gwl_data'
    local_paths['wcrc_metadata_store_key'] = 'wcrc_metadata'
    local_paths['save_path'] = groundwater_data.joinpath('gwl_west_coast', 'cleaned_data', 'combined_wcrc_data.hdf')

    return local_paths


def get_wcrc_data(recalc=False, redownload=False):
    local_paths = _get_folder_and_local_paths(source_dir=groundwater_data.joinpath('gwl_west_coast'),
                                              local_dir=unbacked_dir.joinpath('wcrc_working/'), redownload=redownload)
    meta_data_requirements = needed_cols_and_types('wcrc')
    return output(local_paths, meta_data_requirements, recalc=recalc)


if __name__ == '__main__':
    data = get_wcrc_data(recalc=True)
    pass
