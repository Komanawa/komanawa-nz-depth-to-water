"""
created Evelyn_Charlesworth 
on: 20/06/2023
"""

""" This Python script cleans and processes the Northland data"""
import numpy as np
import pandas as pd

from komanawa.komanawa_nz_depth_to_water.head_data_processing.data_processing_functions import (find_overlapping_files,
                                                                                                copy_with_prompt,
                                                                                                _get_summary_stats,
                                                                                                append_to_other,
                                                                                                needed_cols_and_types,
                                                                                                data_checks,
                                                                                                metadata_checks,
                                                                                                renew_hdf5_store,
                                                                                                get_hdf5_store_keys,
                                                                                                pull_tethys_data_store,
                                                                                                assign_flags_based_on_null_values,
                                                                                                aggregate_water_data)
from komanawa.komanawa_nz_depth_to_water.head_data_processing.merge_rows import merge_rows_if_possible
from komanawa.komanawa_nz_depth_to_water.project_base import groundwater_data, unbacked_dir


def _get_northland_tethys_data(local_paths, meta_data_requirements, recalc=False):
    """" This function reads in the northland data from Tethys
            dtw_flag = 1= logger, 2= manual, 3= static_oneoff, 4= calculated frm gw_elevation, 5= aquifer test, 6= other
    water_ele_flag = 1= logger, 2= manual, 3= static_oneoff, 4= aquifer test, 5= other
    """

    water_data_store_path = local_paths['local_path'] / 'tethys_water_data.hdf'
    store_key_water_data = 'tethys_water_data'
    store_key_metadata = 'tethys_metadata_combined'

    # Check if data needs to be recalculated or if the HDF files don't exist
    if not recalc and water_data_store_path.exists():
        tethys_water_data = pd.read_hdf(water_data_store_path, store_key_water_data)
        tethys_metadata_all = pd.read_hdf(water_data_store_path, store_key_metadata)

    else:
        needed_gw_columns = ['well_name', 'date', 'depth_to_water', 'gw_elevation', 'dtw_flag', 'water_elev_flag',
                             'data_source', 'elevation_datum', 'other']

        needed_gw_columns_type = {'well_name': "str", 'depth_to_water': "float", 'gw_elevation': "float",
                                  'dtw_flag': "int",
                                  'water_elev_flag': 'int',
                                  'data_source': 'str', 'elevation_datum': "str", 'other': "str"}

        data_keys = get_hdf5_store_keys(unbacked_dir.joinpath('tetheys_2024_all', 'tethys_fully_processed.hdf'))
        meta_keys = get_hdf5_store_keys(unbacked_dir.joinpath('tetheys_2024_all', 'tethys_meta_fully_processed.hdf'))

        tethys_data = pull_tethys_data_store(unbacked_dir.joinpath('tetheys_2024_all', 'tethys_fully_processed.hdf'),
                                             data_keys,
                                             council="Northland")
        tethys_metadata = pull_tethys_data_store(
            unbacked_dir.joinpath('tetheys_2024_all', 'tethys_meta_fully_processed.hdf'),
            meta_keys, council="Northland")

        tethys_metadata_dtw_logger = tethys_metadata[
            '/Northland Regional Council_groundwater_depth_None_metadata'].copy()
        tethys_metadata_dtw_logger.set_index('tethys_station_id', inplace=True)

        tethys_metadata_wle_24h = tethys_metadata['/Northland Regional Council_water_level_24H_metadata'].copy()
        tethys_metadata_wle_24h.set_index('tethys_station_id', inplace=True)

        tethys_metadata_wle_logger = tethys_metadata['/Northland Regional Council_water_level_None_metadata'].copy()
        tethys_metadata_wle_logger.set_index('tethys_station_id', inplace=True)

        comb1 = tethys_metadata_wle_24h.combine_first(tethys_metadata_wle_logger)
        all_tethys_metadata = comb1.combine_first(tethys_metadata_dtw_logger)

        tethys_data_dtw_logger = tethys_data['/Northland Regional Council_groundwater_depth_None'].copy()
        tethys_data_wle_24h = tethys_data['/Northland Regional Council_water_level_24H'].copy()
        tethys_data_wle_logger = tethys_data['/Northland Regional Council_water_level_None'].copy()

        tethys_data_wle_24h['date'] = pd.to_datetime(tethys_data_wle_24h['date'],
                                                     format='%Y-%m-%d %H:%M:%S').dt.normalize()
        tethys_data_wle_logger['date'] = pd.to_datetime(tethys_data_wle_logger['date'], infer_datetime_format=True,
                                                        errors='coerce')
        tethys_data_dtw_logger['date'] = pd.to_datetime(tethys_data_dtw_logger['date'], infer_datetime_format=True,
                                                        errors='coerce')

        tethys_data_wle_24h = tethys_data_wle_24h.drop(columns=['depth_to_water'])
        tethys_data_wle_24h.set_index(['well_name', 'date'], inplace=True)

        tethys_data_dtw_logger['depth_to_water'] = tethys_data_dtw_logger['groundwater_depth']
        tethys_data_dtw_logger = tethys_data_dtw_logger.drop(columns=['groundwater_depth'])
        tethys_data_dtw_logger_additional = tethys_data_dtw_logger.drop_duplicates(subset=['well_name'])
        tethys_data_dtw_logger_additional = tethys_data_dtw_logger_additional.drop(columns=['depth_to_water', 'date'])

        tethys_data_wle_logger['gw_elevation'] = tethys_data_wle_logger['water_level']
        tethys_data_wle_logger = tethys_data_wle_logger.drop(columns=['water_level'])
        tethys_data_wle_logger['date'] = pd.to_datetime(tethys_data_wle_logger['date'], format='mixed')
        tethys_data_wle_logger_additional = tethys_data_wle_logger.drop_duplicates(subset=['well_name'])
        tethys_data_wle_logger_additional = tethys_data_wle_logger_additional.drop(columns=['gw_elevation', 'date'])

        tethys_data_dtw_logger['date'] = pd.to_datetime(tethys_data_dtw_logger['date'])
        tethys_data_dtw_logger['year'] = tethys_data_dtw_logger['date'].dt.year
        tethys_data_dtw_logger['month'] = tethys_data_dtw_logger['date'].dt.month
        tethys_data_dtw_logger['day'] = tethys_data_dtw_logger['date'].dt.day

        tethys_data_wle_logger['date'] = pd.to_datetime(tethys_data_wle_logger['date'])
        tethys_data_wle_logger['year'] = tethys_data_wle_logger['date'].dt.year
        tethys_data_wle_logger['month'] = tethys_data_wle_logger['date'].dt.month
        tethys_data_wle_logger['day'] = tethys_data_wle_logger['date'].dt.day

        # Group by 'well_name' and the extracted date parts, then calculate mean for the specified columns
        daily_average_data = \
            tethys_data_dtw_logger.groupby(['well_name', 'year', 'month', 'day'])[
                ['depth_to_water']].mean().reset_index()
        # If needed, reconstruct the 'date' from the grouped year, month, and day
        daily_average_data['date'] = pd.to_datetime(daily_average_data[['year', 'month', 'day']])
        # Drop the year, month, and day columns if they are no longer needed
        daily_average_data = daily_average_data.drop(columns=['year', 'month', 'day'])
        tethys_data_dtw_logger = daily_average_data
        tethys_data_dtw_logger = pd.merge(tethys_data_dtw_logger, tethys_data_dtw_logger_additional, on=['well_name'],
                                          how='left')
        tethys_data_dtw_logger.set_index(['well_name', 'date'], inplace=True)

        daily_average_data = \
            tethys_data_wle_logger.groupby(['well_name', 'year', 'month', 'day'])[
                ['gw_elevation']].mean().reset_index()
        # If needed, reconstruct the 'date' from the grouped year, month, and day
        daily_average_data['date'] = pd.to_datetime(daily_average_data[['year', 'month', 'day']])
        # Drop the year, month, and day columns if they are no longer needed
        daily_average_data = daily_average_data.drop(columns=['year', 'month', 'day'])
        tethys_data_wle_logger = daily_average_data

        # remove dodgy sites
        bad_sites = [
            'Mangonui at Wallace Bore',  # missing lots of data, just feels suspect
        ]
        tethys_data_wle_logger = tethys_data_wle_logger[~np.in1d(tethys_data_wle_logger['well_name'], bad_sites)]
        tethys_data_wle_logger = pd.merge(tethys_data_wle_logger, tethys_data_wle_logger_additional, on=['well_name'],
                                          how='left')
        tethys_data_wle_logger.set_index(['well_name', 'date'], inplace=True)
        loggers_combine = tethys_data_wle_logger.combine_first(tethys_data_dtw_logger)

        full_combine = loggers_combine.combine_first(tethys_data_wle_24h)
        full_combine = full_combine.reset_index()
        full_combine = full_combine.sort_values(by=['well_name', 'date'], ascending=[True, True])

        tethys_water_data = full_combine[needed_gw_columns]
        tethys_water_data['data_source'] = "tethys"
        tethys_water_data['elevation_datum'] = "NZVD2016"
        # keynote assuming dtw is positive below gl
        tethys_water_data['depth_to_water'] = tethys_water_data['depth_to_water'] * -1

        assign_flags_based_on_null_values(tethys_water_data, 'depth_to_water', 'dtw_flag', 1, 0)
        # Assign 'water_elev_flag' based on 'gw_elevation'
        assign_flags_based_on_null_values(tethys_water_data, 'gw_elevation', 'water_elev_flag', 1, 0)

        tethys_metadata_all = all_tethys_metadata.reset_index().copy()

        for col in meta_data_requirements['needed_columns']:
            if col not in tethys_metadata_all.columns:
                tethys_metadata_all[col] = meta_data_requirements['default_values'].get(col)

        for col, dtype in meta_data_requirements['col_types'].items():
            tethys_metadata_all[col] = tethys_metadata_all[col].astype(dtype)
        if 'other' not in tethys_metadata_all.columns:
            tethys_metadata_all['other'] = ''

        # append unneeded columns to other, incase latter needed
        tethys_metadata_all = append_to_other(df=tethys_metadata_all,
                                              needed_columns=meta_data_requirements["needed_columns"])
        tethys_metadata_all = tethys_metadata_all[meta_data_requirements['needed_columns']]
        tethys_metadata_all['source'] = 'tethys'
        tethys_metadata_all['start_date'] = pd.to_datetime(tethys_metadata_all['start_date'], format='mixed').dt.round(
            'H')
        tethys_metadata_all['end_date'] = pd.to_datetime(tethys_metadata_all['end_date'], format='mixed').dt.round('H')

        for column in tethys_metadata_all:
            # Check if the column is of pandas nullable Int64 type
            if pd.api.types.is_integer_dtype(tethys_metadata_all[column]) and tethys_metadata_all[
                column].isnull().any():
                # Convert to float64 if there are NaN values, as NaN cannot be represented in pandas' non-nullable integer types
                tethys_metadata_all[column] = tethys_metadata_all[column].astype('float64')
            elif pd.api.types.is_integer_dtype(tethys_metadata_all[column]):
                # Convert to NumPy's int64 if there are no NaN values and it is a pandas Int64 type
                tethys_metadata_all[column] = tethys_metadata_all[column].astype('int64')

        # Convert boolean columns to int
        for col in tethys_metadata_all.columns:
            if tethys_metadata_all[col].dtype == 'boolean':
                tethys_metadata_all[col] = tethys_metadata_all[col].astype('int64')

        renew_hdf5_store(new_data=tethys_water_data, old_path=water_data_store_path,
                         store_key=store_key_water_data)
        renew_hdf5_store(new_data=tethys_metadata_all, old_path=water_data_store_path,
                         store_key=store_key_metadata)

    return {'tethys_groundwater_data_final': tethys_water_data,
            'tethys_metadata_combined': tethys_metadata_all}


def _get_all_bores_northland_metadata(local_paths, meta_data_requirements):
    """
    This function reads in the metadata for all the registered bores in the NRC database,
    as provided by NRC
    :return: dataframe, raw data
    """
    needed_gw_columns = ['well_name', 'date', 'depth_to_water', 'gw_elevation', 'dtw_flag', 'water_elev_flag',
                         'data_source', 'elevation_datum', 'other']

    needed_gw_columns_type = {'well_name': "str", 'depth_to_water': "float", 'gw_elevation': "float", 'dtw_flag': "int",
                              'water_elev_flag': 'int',
                              'data_source': 'str', 'elevation_datum': "str", 'other': "str"}

    # defining the path
    all_bores_northland_metadata = pd.read_excel(
        local_paths['local_path'] / 'Metadata_from_NRC' / 'AllBores200523SWL.xlsx', skiprows=1)

    gwl_sites_northland_metadata = pd.read_excel(local_paths[
                                                     'local_path'] / 'Metadata_from_NRC' / 'HydroSites23_92_22spatialjointoBoreLogs30m.xlsx')

    concatenated = pd.concat([all_bores_northland_metadata, gwl_sites_northland_metadata], ignore_index=True)

    for col in concatenated.columns:
        # Replace specific non-numeric placeholders with NaN
        concatenated[col] = concatenated[col].replace(['<Null>', 'nan', 'NaN', 'N/A', 'n/a'], np.nan)

    concatenated['DateOfCompletion'] = pd.to_datetime(concatenated['DateOfCompletion'], format='mixed')
    concatenated['DateCreated'] = pd.to_datetime(concatenated['DateCreated'], format='mixed')

    for col in concatenated.columns:
        if not pd.api.types.is_datetime64_any_dtype(concatenated[col]):
            concatenated[col] = pd.to_numeric(concatenated[col], errors='ignore')

    default_precision = 0.1  # for example, default precision is 2 decimal places

    # create dict of precisis ofr none str columns
    precisions = {col: default_precision for col in concatenated.columns
                  if concatenated[col].dtype != object and not pd.api.types.is_datetime64_any_dtype(concatenated[col])}
    precisions['X'] = 50
    precisions['Y'] = 50

    # Create a list of columns to skip, which are of string type
    skip_cols = [col for col in concatenated.columns
                 if concatenated[col].dtype == object or pd.api.types.is_datetime64_any_dtype(concatenated[col])]

    aggregation_functions = {col: np.nanmean for col in precisions}

    concatenated2 = merge_rows_if_possible(concatenated, on='IRISID', precision=precisions,
                                           skip_cols=skip_cols, actions=aggregation_functions)
    concatenated2 = concatenated2.sort_values(by=['IRISID'], ascending=[True])

    new_names = {'IRISID': 'alt_well_name', "ReducedLevel": "elevation", 'DateCreated': 'start_date',
                 'DateOfCompletion': 'end_date',
                 'StaticWaterLevel': 'depth_to_water', 'X': 'nztm_x', 'Y': 'nztm_y', 'DepthOfBore': 'well_depth',
                 'ScreenIntervalFrom': 'top_topscreen',
                 'ScreenIntervalTo': 'bottom_bottomscreen'}

    concatenated = concatenated2.copy().rename(columns=new_names)
    # concatenated = concatenated.rename(columns=new_names)
    concatenated['well_name'] = np.where(pd.notnull(concatenated['WSNumber']), concatenated['WSNumber'],
                                         concatenated['alt_well_name'])

    nrc_gw_depth_data = concatenated[['well_name', 'start_date', 'end_date', 'elevation', 'depth_to_water'
                                      ]]

    nrc_gw_depth_data = nrc_gw_depth_data.dropna(subset=['well_name'])
    nrc_gw_depth_data = nrc_gw_depth_data.dropna(subset=['depth_to_water'])
    nrc_gw_depth_data = nrc_gw_depth_data.drop_duplicates(subset=['well_name', 'end_date'])
    nrc_gw_depth_data = nrc_gw_depth_data.sort_values(by=['well_name', 'start_date'])
    nrc_gw_depth_data['depth_to_water'] = nrc_gw_depth_data['depth_to_water'] * -1
    nrc_gw_depth_data['gw_elevation'] = np.where(
        (~pd.isnull(nrc_gw_depth_data['elevation'])) | (nrc_gw_depth_data['elevation'] == 0),
        nrc_gw_depth_data['elevation'] - nrc_gw_depth_data['depth_to_water'],
        np.nan
    )

    assign_flags_based_on_null_values(nrc_gw_depth_data, 'depth_to_water', 'dtw_flag', 1, 0)
    # Assign 'water_elev_flag' based on 'gw_elevation'
    assign_flags_based_on_null_values(nrc_gw_depth_data, 'gw_elevation', 'water_elev_flag', 1, 0)

    for column in needed_gw_columns:
        if column not in nrc_gw_depth_data.columns:
            # Add the missing column and initialize with NaNs or another suitable default value
            nrc_gw_depth_data[column] = np.nan

    nrc_gw_depth_data = append_to_other(nrc_gw_depth_data, needed_gw_columns)

    # as we want a single date here I assume the end date is the date if present else the start date
    nrc_gw_depth_data['date'] = np.where(pd.notnull(nrc_gw_depth_data['end_date']), nrc_gw_depth_data['end_date'],
                                         nrc_gw_depth_data['start_date'])

    # Ensure the columns are in the same order as needed_gw_columns
    nrc_gw_depth_data = nrc_gw_depth_data[needed_gw_columns]

    for col in meta_data_requirements['needed_columns']:
        if col not in concatenated.columns:
            concatenated[col] = meta_data_requirements['default_values'].get(col)

    for col, dtype in meta_data_requirements['col_types'].items():
        if column in concatenated.columns:
            concatenated[col] = concatenated[col].astype(dtype)

    concatenated = append_to_other(concatenated, meta_data_requirements['needed_columns'])
    concatenated = concatenated[meta_data_requirements['needed_columns']]
    concatenated['start_date'] = pd.to_datetime(concatenated['start_date'])
    concatenated['end_date'] = pd.to_datetime(concatenated['end_date'])

    return {'all_bores_northland_metadata': concatenated, 'nrc_gw_depth_data': nrc_gw_depth_data}


def output(local_paths, meta_data_requirements, recalc=False):  #
    """This function combines the two sets of metadata and cleans it
    :return: dataframe"""

    needed_gw_columns_type = {'well_name': "str", 'depth_to_water': "float", 'gw_elevation': "float", 'dtw_flag': "int",
                              'water_elev_flag': 'int',
                              'data_source': 'str', 'elevation_datum': "str", 'other': "str"}

    water_data_store_path = local_paths['save_path']
    store_key_water_data = local_paths['wl_store_key']
    store_key_metadata = local_paths['northland_metadata_store_key']

    # Check if data needs to be recalculated or if the HDF files don't exist
    if not recalc and water_data_store_path.exists():
        combined_water_data = pd.read_hdf(water_data_store_path, store_key_water_data)
        combined_metadata = pd.read_hdf(water_data_store_path, store_key_metadata)

    else:

        tethys_data = _get_northland_tethys_data(local_paths, meta_data_requirements, recalc=False)
        tethys_gw_data = tethys_data['tethys_groundwater_data_final']
        tethys_gw_data['well_name'] = tethys_gw_data["well_name"].astype(str)
        tethys_gw_data['other'] = tethys_gw_data["other"].astype(str)

        tetheys_metadata = tethys_data['tethys_metadata_combined']
        tetheys_metadata['well_name'] = tetheys_metadata["well_name"].astype(str)

        nrc_data = _get_all_bores_northland_metadata(local_paths=local_paths,
                                                     meta_data_requirements=meta_data_requirements)

        nrc_metadata = nrc_data['all_bores_northland_metadata']
        nrc_gw_data = nrc_data['nrc_gw_depth_data']
        nrc_gw_data['data_source'] = 'nrc'
        nrc_gw_data['elevation_datum'] = nrc_gw_data['elevation_datum'].astype(str)

        combined_water_data = pd.concat([tethys_gw_data, nrc_gw_data], ignore_index=True)
        combined_water_data['date'] = pd.to_datetime(combined_water_data['date']).dt.date
        combined_water_data['date'] = pd.to_datetime(combined_water_data['date'])
        for column, dtype in needed_gw_columns_type.items():
            combined_water_data[column] = combined_water_data[column].astype(dtype)

        combined_water_data = aggregate_water_data(combined_water_data)

        nrc_metadata['start_date'] = pd.to_datetime(nrc_metadata['start_date'])
        nrc_metadata['end_date'] = pd.to_datetime(nrc_metadata['end_date'])
        # combining the two metadata sets

        combined_metadata = pd.concat([tetheys_metadata, nrc_metadata], ignore_index=True).sort_values(by='well_name')
        combined_metadata.reset_index(inplace=True, drop=True)

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
        # check wl site has an entry in metadata and retun list otherwise
        external_column = pd.Series(combined_water_data['well_name'].unique())
        metadata_checks(data=combined_metadata, external_column=external_column)

        # drop extra sites in metadata not in water level data
        combined_metadata = combined_metadata[combined_metadata['well_name'].isin(external_column)]

        cols_to_keep = [
            'well_name', 'rl_elevation', 'rl_datum', 'rl_source',
            'ground_level_datum', 'ground_level_source', 'well_depth', 'top_topscreen',
            'bottom_bottomscreen', 'nztm_x', 'nztm_y', 'other', 'dist_mp_to_ground_level'
        ]

        combined_metadata = append_to_other(df=combined_metadata, needed_columns=cols_to_keep)
        combined_metadata.drop(columns=[col for col in combined_metadata.columns if
                                        col not in cols_to_keep and col != 'other'],
                               inplace=True)

        for column in combined_metadata:
            # Check if the column is of pandas nullable Int64 type
            if pd.api.types.is_integer_dtype(combined_metadata[column]) and combined_metadata[
                column].isnull().any():
                # Convert to float64 if there are NaN values, as NaN cannot be represented in pandas' non-nullable integer types
                combined_metadata[column] = combined_metadata[column].astype('float64')
            elif pd.api.types.is_integer_dtype(combined_metadata[column]):
                # Convert to NumPy's int64 if there are no NaN values and it is a pandas Int64 type
                combined_metadata[column] = combined_metadata[column].astype('int64')

        combined_metadata['well_depth'] = combined_metadata['well_depth'].astype('float64')

        renew_hdf5_store(new_data=combined_water_data, old_path=local_paths['save_path'],
                         store_key=local_paths['wl_store_key'])
        renew_hdf5_store(new_data=combined_metadata, old_path=local_paths['save_path'],
                         store_key=local_paths['northland_metadata_store_key'])

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
        # tthys now sourced from corrected central repository
        # 'water_level_data': local_path_mapping.joinpath("tethys_water_level_data"),
        # 'water_depth_data': local_path_mapping.joinpath("tethys_gw_depth_data"),
        # 'water_level_metadata': local_path_mapping.joinpath('tethys_metadata', "water_level_all_stations.csv"),
        # flag that water_level _metadata is horizons not Northland
        'water_depth_metadata': local_path_mapping.joinpath('tethys_metadata', "groundwater_depth_all_stations.csv"),
        'tethys_local_save_path': local_base_path.joinpath("gwl_northland", "cleaned_data", "tethys_gw_data.hdf"),
        'northland_local_save_path': local_base_path.joinpath("gwl_northland", "cleaned_data", "northland_gw_data.hdf"),
        'local_path': local_path_mapping
    }

    # Store keys are hardcoded as they are specific to this setup
    local_paths['tethys_gw_depth_local_store_key'] = 'northland_depth_data'
    local_paths['tethys_water_level_data_store_key'] = 'water_level_data'
    local_paths['wl_store_key'] = 'northland_gwl_data'
    local_paths['northland_metadata_store_key'] = 'northland_metadata'
    local_paths['save_path'] = groundwater_data.joinpath('gwl_northland', 'cleaned_data', 'combined_northland_data.hdf')

    return local_paths


def get_nrc_data(recalc=False, redownload=False):
    local_paths = _get_folder_and_local_paths(source_dir=groundwater_data.joinpath('gwl_northland'),
                                              local_dir=unbacked_dir.joinpath('northland_working/'),
                                              redownload=redownload)
    meta_data_requirements = needed_cols_and_types('NRC')
    return output(local_paths, meta_data_requirements, recalc=recalc)


if __name__ == '__main__':
    data = get_nrc_data(recalc=True)
    pass
