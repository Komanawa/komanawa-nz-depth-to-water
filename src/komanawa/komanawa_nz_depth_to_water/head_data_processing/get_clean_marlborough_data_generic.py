"""
created Patrick Durney & Evelyn_Charlesworth
on: 29/09/2023
This script cleans and processes the Marlborough GWL data

"""

# keynote there is no way to match mdc and tethys sites

import numpy as np
import pandas as pd

from komanawa.komanawa_nz_depth_to_water.head_data_processing.data_processing_functions import (find_overlapping_files,
                                                                                                copy_with_prompt, \
                                                                                                _get_summary_stats,
                                                                                                append_to_other,
                                                                                                needed_cols_and_types,
                                                                                                data_checks, \
                                                                                                metadata_checks,
                                                                                                parse_and_identify,
                                                                                                get_hdf5_store_keys,
                                                                                                pull_tethys_data_store,
                                                                                                assign_flags_based_on_null_values,
                                                                                                renew_hdf5_store)
from komanawa.komanawa_nz_depth_to_water.head_data_processing.merge_rows import merge_rows_if_possible
from komanawa.komanawa_nz_depth_to_water.project_base import groundwater_data, unbacked_dir


########################################################################################################################
def _get_marlborough_tethys_data(meta_data_requirements):
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
                                         council="Marlborough")
    tethys_metadata = pull_tethys_data_store(
        unbacked_dir.joinpath('tetheys_2024_all', 'tethys_meta_fully_processed.hdf'),
        meta_keys, council="Marlborough")

    tethys_metadata_dtw_24h = tethys_metadata['/Marlborough District Council_groundwater_depth_24H_metadata']

    tethys_data_dtw_24h = tethys_data['/Marlborough District Council_groundwater_depth_24H']
    tethys_data_dtw_24h['depth_to_water'] = tethys_data_dtw_24h['groundwater_depth']

    tethys_data_dtw = tethys_data_dtw_24h[needed_gw_columns]
    tethys_data_dtw['data_source'] = "tethys"

    assign_flags_based_on_null_values(tethys_data_dtw, 'depth_to_water', 'dtw_flag', 1, 0)
    assign_flags_based_on_null_values(tethys_data_dtw, 'gw_elevation', 'water_elev_flag', 1, 0)

    for col in meta_data_requirements['needed_columns']:
        if col not in tethys_metadata_dtw_24h.columns:
            tethys_metadata_dtw_24h[col] = meta_data_requirements['default_values'].get(col)

    for col, dtype in meta_data_requirements['col_types'].items():
        tethys_metadata_dtw_24h[col] = tethys_metadata_dtw_24h[col].astype(dtype)
    if 'other' not in tethys_metadata_dtw_24h.columns:
        tethys_metadata_dtw_24h['other'] = ''

    tethys_metadata_dtw_24h = append_to_other(df=tethys_metadata_dtw_24h,
                                              needed_columns=meta_data_requirements["needed_columns"])
    tethys_metadata_dtw_24h = tethys_metadata_dtw_24h[meta_data_requirements['needed_columns']]
    tethys_metadata_dtw_24h['source'] = 'tethys'
    tethys_metadata_dtw_24h['start_date'] = pd.to_datetime(tethys_metadata_dtw_24h['start_date'])
    tethys_metadata_dtw_24h['end_date'] = pd.to_datetime(tethys_metadata_dtw_24h['end_date'])

    return {'tethys_groundwater_data_final': tethys_data_dtw,
            'tethys_metadata_combined': tethys_metadata_dtw_24h}


def _get_marlborough_bespoke_metadata(local_paths, meta_data_requirements):
    """This function reads in the metadata sent through by Marlborough District Council
    dtw_flag = 1= logger, 2= manual, 3= static_oneoff, 4= calculated frm gw_elevation, 5= aquifer test, 6= other
    water_ele_flag = 1= logger, 2= manual, 3= static_oneoff, 4= aquifer test, 5= other
    """

    needed_gw_columns = ['well_name', 'date', 'depth_to_water', 'gw_elevation', 'dtw_flag', 'water_elev_flag',
                         'data_source', 'elevation_datum', 'other']

    needed_gw_columns_type = {'well_name': "str", 'depth_to_water': "float", 'gw_elevation': "float", 'dtw_flag': "int",
                              'water_elev_flag': 'int',
                              'data_source': 'str', 'elevation_datum': "str", 'other': "str"}

    mdc_metadata = local_paths['local_path'] / 'downloaded_mdc_well_data.csv'
    mdc_metadata = pd.read_csv(mdc_metadata)

    # renaming columns
    new_names = {'X': 'nztm_x', 'Y': 'nztm_y', 'WellNumber': 'well_name', 'AdjFinishedWellDepth': 'well_depth',
                 'AdjFinishedStaticWaterLevel': 'depth_to_water', 'WellDiameter': 'diameter',
                 'DrillingDate': 'date'}
    mdc_metadata.rename(columns=new_names, inplace=True)

    drop_columns = ['OBJECTID', 'WellType', 'WellSubType', 'WellStatus', 'DrillingCompany',
                    'ApplicantOwner', 'Productivity', 'IsPublished',
                    'PhotoURL', 'LogURL', 'ID', 'ChemistryReportURL', 'AquiferTestURL', 'OtherURL', 'ISODataQuality']

    mdc_metadata.drop(columns=drop_columns, inplace=True)

    # handling datatypes
    mdc_metadata = mdc_metadata.astype(
        {'well_name': 'str', 'nztm_x': 'float', 'nztm_y': 'float', 'well_depth': 'float',
         'depth_to_water': 'float', 'diameter': 'float'})

    # Check if 'Date' or 'date' is in the DataFrame columns
    if 'Date' in mdc_metadata.columns:
        date_column = 'Date'

    elif 'date' in mdc_metadata.columns:
        date_column = 'date'
    else:
        date_column = None

    if date_column:
        # Apply the function to the date column and create a new DataFrame with the results
        mdc_metadata[date_column] = mdc_metadata[date_column].astype(str)
        date_info = mdc_metadata[date_column].apply(parse_and_identify)
        temp_df = pd.DataFrame(date_info.tolist(), columns=['date', 'type'], index=mdc_metadata.index)

        # Update the original DataFrame
        mdc_metadata['date'] = temp_df['date']
        # Optionally drop the 'type' column and the original date column if it was 'Date'
        if date_column and date_column != 'date':
            df = mdc_metadata.drop(columns=date_column)
    else:
        # If no date column exists, create one with NaT values
        mdc_metadata['date'] = pd.NaT

    mdc_metadata['date'] = pd.to_datetime(mdc_metadata['date'])

    mdc_gw_data = mdc_metadata[['well_name', 'date', 'depth_to_water']].dropna()
    mdc_gw_data['data_source'] = "MDC"
    mdc_gw_data['dtw_flag'] = 3
    mdc_gw_data['water_elev_flag'] = 0
    # I hate depth to water as negatives!
    mdc_gw_data['depth_to_water'] = mdc_gw_data['depth_to_water'] * -1

    for column in needed_gw_columns:
        if column not in mdc_gw_data.columns:
            # Add the missing column and initialize with NaNs or another suitable default value
            mdc_gw_data[column] = np.nan

    for column, dtype in needed_gw_columns_type.items():
        mdc_gw_data[column] = mdc_gw_data[column].astype(dtype)

    for col in meta_data_requirements['needed_columns']:
        if col not in mdc_metadata.columns:
            mdc_metadata[col] = meta_data_requirements['default_values'].get(col)

    for col, dtype in meta_data_requirements['col_types'].items():
        mdc_metadata[col] = mdc_metadata[col].astype(dtype)

    mdc_metadata['start_date'] = pd.to_datetime(mdc_metadata['start_date'])
    mdc_metadata['end_date'] = pd.to_datetime(mdc_metadata['end_date'])

    return {'mdc_metadata': mdc_metadata, 'mdc_gw_data': mdc_gw_data}


def output(local_paths, meta_data_requirements, recalc=False):
    """This function combines the two sets of metadata and cleans it
    :return: dataframe"""
    needed_gw_columns_type = {'well_name': "str", 'depth_to_water': "float", 'gw_elevation': "float", 'dtw_flag': "int",
                              'water_elev_flag': 'int',
                              'data_source': 'str', 'elevation_datum': "str", 'other': "str"}

    water_data_store_path = local_paths['save_path']
    store_key_water_data = local_paths['wl_store_key']
    store_key_metadata = local_paths['marlborough_metadata_store_key']

    # Check if data needs to be recalculated or if the HDF files don't exist
    if not recalc and water_data_store_path.exists():
        combined_water_data = pd.read_hdf(water_data_store_path, store_key_water_data)
        combined_metadata = pd.read_hdf(water_data_store_path, store_key_metadata)

    else:
        tethys_data = _get_marlborough_tethys_data(meta_data_requirements)
        tethy_gw_data = tethys_data['tethys_groundwater_data_final']
        tethy_gw_data['date'] = pd.to_datetime(tethy_gw_data['date'])

        tetheys_metadata = tethys_data['tethys_metadata_combined']
        mdc_data = _get_marlborough_bespoke_metadata(local_paths=local_paths,
                                                     meta_data_requirements=meta_data_requirements)
        mdc_metadata = mdc_data['mdc_metadata']
        mdc_gw_data = mdc_data['mdc_gw_data']
        mdc_gw_data['date'] = pd.to_datetime(mdc_gw_data['date'])

        combined_metadata = pd.concat([tetheys_metadata, mdc_metadata], ignore_index=True)
        # combining the two metadata sets

        combined_metadata = combined_metadata.round({'nztm_x': 0, 'nztm_y': 0})

        combined_water_data = pd.concat([tethy_gw_data, mdc_gw_data], ignore_index=True)
        combined_water_data['date'] = pd.to_datetime(combined_water_data['date']).dt.date
        combined_water_data['date'] = pd.to_datetime(combined_water_data['date'])
        #    combined_water_data = aggregate_water_data(combined_water_data)

        stats = _get_summary_stats(combined_water_data)
        stats = stats.set_index('well_name')
        combined_metadata = combined_metadata.set_index('well_name')
        combined_metadata = combined_metadata.combine_first(stats)
        combined_metadata = combined_metadata.reset_index()
        combined_metadata = combined_metadata.dropna(subset=['min_dtw'])

        combined_metadata = combined_metadata.sort_values(by=['well_name', 'start_date'], ascending=[True, True])
        combined_metadata["artesian"] = np.where(
            combined_metadata['min_dtw'] < 0,  # Else, if 'min_gwl' < 0 (regardless of 'depth_to_water_static')
            True,  # Then also set to True
            False  # Else, set to False
        )

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

        renew_hdf5_store(old_path=local_paths['save_path'], store_key=local_paths['wl_store_key'],
                         new_data=combined_water_data)

        renew_hdf5_store(old_path=local_paths['save_path'], store_key=local_paths['marlborough_metadata_store_key'],
                         new_data=combined_metadata)

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
        # thethys no longer pulled from coucil directory - instead from corrected central file
        # 'water_level_data': local_path_mapping.joinpath("tethys_water_level_data"),
        # 'water_depth_data': local_path_mapping.joinpath("tethys_gw_depth_data"),
        # 'water_level_metadata': local_path_mapping.joinpath("water_level_all_stations.csv"),
        # 'water_depth_metadata': local_path_mapping.joinpath("groundwater_depth_all_stations.csv"),
        'thethys_local_save_path': local_base_path.joinpath("gwl_marlborough", "cleaned_data", "tethys_gw_data.hdf"),
        'local_path': local_path_mapping
    }

    # Store keys are hardcoded as they are specific to this setup
    local_paths['thethys_gw_depth_local_store_key'] = 'marlborough_depth_data'
    local_paths['thethys_gw_level_local_store_key'] = 'marlborough_gw_level_data'
    local_paths['wl_store_key'] = 'marlborough_gwl_data'
    local_paths['marlborough_metadata_store_key'] = 'marlborough_metadata'
    local_paths['save_path'] = groundwater_data.joinpath('gwl_marlborough', 'cleaned_data',
                                                         'combined_marlborough_data.hdf')

    return local_paths


def get_mdc_data(recalc=False, redownload=False):
    local_paths = _get_folder_and_local_paths(source_dir=groundwater_data.joinpath('gwl_marlborough'),
                                              local_dir=unbacked_dir.joinpath('marborough_working/'),
                                              redownload=redownload)
    meta_data_requirements = needed_cols_and_types('MDC')
    return output(local_paths, meta_data_requirements, recalc=recalc)


if __name__ == '__main__':
    data = get_mdc_data(recalc=False)
