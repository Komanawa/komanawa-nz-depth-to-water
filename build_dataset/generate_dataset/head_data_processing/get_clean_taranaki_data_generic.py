"""
created Evelyn_Charlesworth 
on: 29/09/2023
"""

"""This script cleans and processes the Taranaki GWL data"""

import os
import pandas as pd
from build_dataset.generate_dataset.project_base import groundwater_data, unbacked_dir
from build_dataset.generate_dataset.head_data_processing.data_processing_functions import find_overlapping_files, \
    copy_with_prompt, \
    _get_summary_stats, append_to_other, needed_cols_and_types, data_checks, \
    metadata_checks, renew_hdf5_store, get_hdf5_store_keys, pull_tethys_data_store, aggregate_water_data, \
    assign_flags_based_on_null_values
import numpy as np
from pathlib import Path
from build_dataset.generate_dataset.head_data_processing.merge_rows import merge_rows_if_possible


def _get_taranaki_tethys_data(local_paths, meta_data_requirements):
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
                                         council="Taranaki")
    tethys_metadata = pull_tethys_data_store(
        unbacked_dir.joinpath('tetheys_2024_all', 'tethys_meta_fully_processed.hdf'),
        meta_keys, council="Taranaki")

    tethys_data_dtw_24h = tethys_data['/Taranaki Regional Council_groundwater_depth_24H'].copy()
    tethys_data_dtw_24h['depth_to_water'] = tethys_data_dtw_24h['groundwater_depth']
    tethys_data_dtw_24h = tethys_data_dtw_24h.rename(
        columns={'bore_depth': 'well_depth', 'bore_bottom_of_screen': 'bottom_bottomscreen',
                 'bore_top_of_screen': 'top_topscreen',
                 'altitude': 'tethys_elevation', 'water_level': 'gw_elevation'})

    tethys_data_dtw = tethys_data_dtw_24h[needed_gw_columns]
    tethys_data_dtw['data_source'] = "tethys"

    assign_flags_based_on_null_values(tethys_data_dtw, 'depth_to_water', 'dtw_flag', 1, 0)
    # Assign 'water_elev_flag' based on 'gw_elevation'
    assign_flags_based_on_null_values(tethys_data_dtw, 'gw_elevation', 'water_elev_flag', 1, 0)

    tethys_data_dtw['date'] = pd.to_datetime(tethys_data_dtw['date'])

    tethys_groundwater_data_metadata = tethys_data_dtw_24h[
        ['tethys_station_id', 'well_name', 'tethys_elevation', 'top_topscreen', 'bottom_bottomscreen']]
    tethys_groundwater_data_metadata = tethys_groundwater_data_metadata.drop_duplicates()

    tethys_metadata_dtw_24h = tethys_metadata['/Taranaki Regional Council_groundwater_depth_24H_metadata'].copy()
    tethys_metadata_dtw_24h = tethys_metadata_dtw_24h.rename(
        columns={'bore_depth': 'well_depth', 'bore_bottom_of_screen': 'bottom_bottomscreen',
                 'bore_top_of_screen': 'top_topscreen',
                 'altitude': 'tethys_elevation', 'groundwater_depth': 'depth_to_water', 'water_level': 'gw_elevation'})

    for col, dtype in meta_data_requirements['col_types'].items():
        if col in tethys_metadata_dtw_24h.columns:
            # If column exists, convert its data type
            tethys_metadata_dtw_24h[col] = tethys_metadata_dtw_24h[col].astype(dtype)
        else:
            tethys_metadata_dtw_24h[col] = meta_data_requirements['default_values'].get(col)

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


def process_file(file_path, rename_dicts):
    raw_df = pd.read_csv(file_path)
    site_name = os.path.basename(file_path).split('.')[0]
    processed_dfs = []
    dtw_flag = 4  # Default value if 'Index.1' is not present
    water_ele_flag = 1  # Default value if 'Index 2' is not present
    set = "set1"  # Default value if 'Index 2' is not present

    for rename_dict in rename_dicts:
        # Check if all original columns in rename_dict are present in raw_df
        if all(col in raw_df.columns for col in rename_dict.keys()):
            df = raw_df[list(rename_dict.keys())].rename(columns=rename_dict)
            df['site_name'] = site_name

            if 'Index.1' in rename_dict:
                dtw_flag = 1
                set = "set2"
            if 'Index 2' in rename_dict:
                water_ele_flag = 2
                set = "set3"

            df['dtw_flag'] = dtw_flag
            df['water_elev_flag'] = water_ele_flag
            df['set'] = set
            df['data_source'] = 'TRC'

            # Convert 'date' to datetime, assuming 'date' is a key in rename_dict
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], dayfirst=True)

            # Convert numeric columns to float
            numeric_cols = df.select_dtypes(include=['number']).columns.difference(['dtw_flag', 'water_ele_flag'])
            df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
            processed_dfs.append(df)

    return processed_dfs


def _get_bespoke_taranaki_data(local_paths, recalc=False):
    needed_gw_columns = ['well_name', 'date', 'depth_to_water', 'gw_elevation', 'dtw_flag', 'water_elev_flag',
                         'data_source', 'elevation_datum', 'other', 'set']

    needed_gw_columns_type = {'well_name': "str", 'depth_to_water': "float", 'gw_elevation': "float", 'dtw_flag': "int",
                              'water_elev_flag': 'int',
                              'data_source': 'str', 'elevation_datum': "str", 'other': "str", 'set': "str"}

    old_save_path = Path(local_paths['taranaki_local_save_path'])
    new_save_path = Path(local_paths['local_path']) / 'cleaned_data' / 'taranaki_sporadic_data.hdf'
    store_key = local_paths['water_level_data_store_key']

    if old_save_path.exists() and not recalc:
        return pd.read_hdf(old_save_path, store_key)

    folder_path = local_paths['water_level_data']
    all_dfs = []

    # Define your renaming dictionaries for each type of data
    rename_dicts = [
        {'Index': 'date', 'GW Level m AMSL (logger) [GW Level m AMSL (logger)]': 'gw_elevation'},
        {'Index.1': 'date', 'Groundwater Level m BMP [Groundwater Level MBMP]': 'depth_to_water'},
        {'Index 2': 'date', 'GW Level m AMSL (manual) [GW Level m AMSL (manual)]': 'gw_elevation'}
    ]

    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)
        processed_dfs = process_file(file_path, rename_dicts)
        all_dfs.extend(processed_dfs)  # Add the processed DataFrames to the list

    if all_dfs:  # Check if there are any DataFrames to concatenate
        combined_df = pd.concat(all_dfs, ignore_index=True)
        combined_df.dropna(subset=['date'], inplace=True)
        combined_df['well_name'] = combined_df['site_name'].str.extract(r'(GND\d+)')
        for column in needed_gw_columns:
            if column not in combined_df.columns:
                # Add the missing column and initialize with NaNs or another suitable default value
                combined_df[column] = np.nan
        for column, dtype in needed_gw_columns_type.items():
            combined_df[column] = combined_df[column].astype(dtype)
        combined_df = combined_df[needed_gw_columns]

        renew_hdf5_store(new_data=combined_df, old_path=old_save_path, new_path=new_save_path, store_key=store_key)

        return combined_df

    else:
        print("No valid data frames were processed.")
        return pd.DataFrame()


########################################################################################################################
def _get_discrete_taranaki_data(local_paths):
    """This function reads in the discrete data sent to us by Taranaki
               dtw_flag = 1= logger, 2= manual, 3= static_oneoff, 4= calculated frm gw_elevation, 5= aquifer test, 6= other
    water_ele_flag = 1= logger, 2= manual, 3= static_oneoff, 4= aquifer test, 5= other
    :return: dataframe
    """

    # keynote some of this is in depth to water and some is elevation
    # reading in the data
    needed_gw_columns = ['well_name', 'date', 'depth_to_water', 'gw_elevation', 'dtw_flag', 'water_elev_flag',
                         'data_source', 'elevation_datum', 'other']

    needed_gw_columns_type = {'well_name': "str", 'depth_to_water': "float", 'gw_elevation': "float", 'dtw_flag': "int",
                              'water_elev_flag': 'int',
                              'data_source': 'str', 'elevation_datum': "str", 'other': "str"}

    path = local_paths["local_path"] / 'groundwater discrete.csv'
    data = pd.read_csv(path, encoding='latin1')

    # filtering the data to only include water level and dtw
    discrete_water_level_data = data[data['trc_parameter_name'] == 'Water Level']
    discrete_water_depth_data = data[data['trc_parameter_name'] == 'Water Depth']

    # renaming the columns
    new_names = {'site_code': 'well_name', 'collected_date': 'date', 'value_reported': 'gw_elevation'}
    new_names1 = {'site_code': 'well_name', 'collected_date': 'date', 'value_reported': 'depth_to_water'}
    discrete_water_level_data.rename(columns=new_names, inplace=True)
    discrete_water_depth_data.rename(columns=new_names1, inplace=True)

    drop_columns = ['SiteName', 'collected_time', 'units', 'method_code', 'trc_parameter_name',
                    'non_trc_parameter_name']
    discrete_water_level_data.drop(columns=drop_columns, inplace=True)
    discrete_water_depth_data.drop(columns=drop_columns, inplace=True)

    # removing odd data
    # remove any data points that have strings or > or < in them
    # converting to numeric with errors coerced and then dropping anything that is not nan
    discrete_water_level_data['gw_elevation'] = pd.to_numeric(discrete_water_level_data['gw_elevation'],
                                                              errors='coerce')
    discrete_water_level_data.dropna(subset=['gw_elevation'], inplace=True)

    # combining the data
    combined_discrete_data = pd.merge(discrete_water_level_data, discrete_water_depth_data, on=["well_name", 'date'],
                                      how='outer')
    # handling date
    combined_discrete_data['date'] = pd.to_datetime(combined_discrete_data['date'], dayfirst=True)
    assign_flags_based_on_null_values(combined_discrete_data, 'depth_to_water', 'dtw_flag', 3, 0)
    # Assign 'water_elev_flag' based on 'gw_elevation'
    assign_flags_based_on_null_values(combined_discrete_data, 'gw_elevation', 'water_elev_flag', 3, 0)
    combined_discrete_data['data_source'] = 'TRC'

    for column in needed_gw_columns:
        if column not in combined_discrete_data.columns:
            # Add the missing column and initialize with NaNs or another suitable default value
            combined_discrete_data[column] = np.nan
    for column, dtype in needed_gw_columns_type.items():
        combined_discrete_data[column] = combined_discrete_data[column].astype(dtype)
    combined_df = combined_discrete_data[needed_gw_columns]

    return combined_discrete_data


def _get_taranaki_metadata(local_paths, meta_data_requirements):
    """This function processes the metadata provided by Taranaki
    :return: dataframe
    """

    path = local_paths['local_path'] / 'gw_meta_data.xlsx'
    metadata = pd.read_excel(path)

    # dropping unnecessary columns
    drop_columns = ['bio_category_id', 'bio_habitat_id', 'rec_climate_id', 'rec_flow_source_id', 'rec_geology_id',
                    'rec_land_cover_id', 'rec_network_position_id',
                    'rec_valley_landform_id', 'lawa_id_NOT_USED', 'well_bore_use_type', 'well_construction_type',
                    'well_pump_type', 'well_strata_id',
                    'well_strata_type_id', 'well_subtype', 'well_type', 'description', 'location', 'depth']
    metadata.drop(columns=drop_columns, inplace=True)

    new_names = {'site_code': 'well_name', 'easting': 'nztm_x', 'northing': 'nztm_y', 'well_depth (m)': 'well_depth',
                 'diameter (mm)': 'diameter', 'top_of_screen': 'top_topscreen',
                 'bottom_of_screen': 'bottom_bottomscreen', 'well_aquifer_type': 'aquifer',
                 'high_static_water_level (m)': 'max_dtw',
                 'low_static_water_level (m)': 'min_dtw'}
    metadata.rename(columns=new_names, inplace=True)

    # handling datatypes
    metadata = metadata.astype(
        {'well_name': 'str', 'nztm_x': 'float', 'nztm_y': 'float', 'well_depth': 'float', 'diameter': 'float',
         'top_topscreen': 'float', 'bottom_bottomscreen': 'float', 'aquifer': 'str', 'elevation': 'float',
         'altitude': 'float',
         'max_dtw': 'float', 'min_dtw': 'float', 'distance_from_coast': 'float',
         'well_elevation_accuracy': 'str',
         'static_water_level': 'float', 'strata_comment': 'str', 'well_strata_type': 'str'})

    # handling date
    metadata['drill_date'] = pd.to_datetime(metadata['drill_date'], dayfirst=False)

    ####################################################################################################################
    """" dtw_flag = 1= logger, 2= manual, 3= static_oneoff, 4= calculated frm gw_elevation, 5= aquifer test, 6= other
    water_elev_flag = 1= logger, 2= manual, 3= static_oneoff, 4= aquifer test, 5= other (and none)
    """

    needed_gw_columns = ['well_name', 'date', 'depth_to_water', 'gw_elevation', 'dtw_flag', 'water_elev_flag',
                         'data_source', 'elevation_datum', 'other']

    needed_gw_columns_type = {'well_name': "str", 'depth_to_water': "float", 'gw_elevation': "float", 'dtw_flag': "int",
                              'water_elev_flag': 'int',
                              'data_source': 'str', 'elevation_datum': "str", 'other': "str"}

    gw_depth_data = metadata.loc[:,
                    ['well_name', 'drill_date', 'static_water_level', 'well_elevation_accuracy',
                     ]]

    gw_depth_data = gw_depth_data.rename(columns={'static_water_level': 'depth_to_water', 'drill_date': 'date'})
    gw_depth_data = gw_depth_data.dropna(subset=['depth_to_water'])
    gw_depth_data = gw_depth_data.drop_duplicates(subset=['well_name', 'depth_to_water'])
    assign_flags_based_on_null_values(gw_depth_data, 'depth_to_water', 'dtw_flag', 3, 0)
    # Assign 'water_elev_flag' based on 'gw_elevation'
    assign_flags_based_on_null_values(gw_depth_data, 'gw_elevation', 'water_elev_flag', 3, 0)
    gw_depth_data['data_source'] = 'TRC'
    gw_depth_data = append_to_other(df=gw_depth_data, needed_columns=needed_gw_columns)

    for column in needed_gw_columns:
        if column not in gw_depth_data.columns:
            # Add the missing column and initialize with NaNs or another suitable default value
            gw_depth_data[column] = np.nan

    gw_depth_data.drop(columns=[col for col in gw_depth_data.columns if
                                col not in needed_gw_columns and col != 'other'],
                       inplace=True)

    for column, dtype in needed_gw_columns_type.items():
        gw_depth_data[column] = gw_depth_data[column].astype(dtype)

    gw_depth_data['date'] = pd.to_datetime(gw_depth_data['date'], format='mixed')
    ####################################################################################################################
    metadata = metadata.drop_duplicates(subset='well_name')
    for col in meta_data_requirements['needed_columns']:
        if col not in metadata.columns:
            metadata[col] = meta_data_requirements['default_values'].get(col)

    for col, dtype in meta_data_requirements['col_types'].items():
        metadata[col] = metadata[col].astype(dtype)

    return {'metadata': metadata, 'gw_depth_data': gw_depth_data}


def output(local_paths, meta_data_requirements, recalc=False):
    """This function combines the two sets of metadata and groundwater cleans it
    :return: dataframe and writes to hdf"""

    needed_gw_columns_type = {'well_name': "str", 'depth_to_water': "float", 'gw_elevation': "float", 'dtw_flag': "int",
                              'water_elev_flag': 'int',
                              'data_source': 'str', 'elevation_datum': "str", 'other': "str"}

    water_data_store_path = local_paths['save_path']
    store_key_water_data = local_paths['wl_store_key']
    store_key_metadata = local_paths['taranaki_metadata_store_key']

    # Check if data needs to be recalculated or if the HDF files don't exist
    if not recalc and water_data_store_path.exists():
        combined_water_data = pd.read_hdf(water_data_store_path, store_key_water_data)
        combined_metadata = pd.read_hdf(water_data_store_path, store_key_metadata)

    else:

        # need to extract the GND and numerics from tethys name to merge with TRC
        pattern = r'\s*(GND\d+)\s*'
        # pull the tehtys data
        tethys_data = _get_taranaki_tethys_data(local_paths, meta_data_requirements)
        tethys_gw_data = tethys_data['tethys_groundwater_data'].copy()
        tethys_metadata = tethys_data['tethys_metadata_combined'].copy()

        tethys_gw_data = tethys_gw_data.rename(columns={'well_name': 'old_name'})
        tethys_metadata = tethys_metadata.rename(columns={'well_name': 'old_name'})

        tethys_gw_data['well_name'] = tethys_gw_data['old_name'].str.extract(pattern)
        tethys_gw_data['well_name'] = tethys_gw_data['well_name'].fillna(tethys_gw_data['old_name'])
        tethys_gw_data = tethys_gw_data.drop(columns=['old_name'])

        tethys_gw_data.loc[tethys_gw_data['well_name'] == '10923 at Pukeone Rd bore', 'well_name'] = 'GNDxxx'
        tethys_gw_data.loc[tethys_gw_data['well_name'] == '10627 at Peat Rd bore', 'well_name'] = 'GNDxxx'

        # pull the council data
        trc_data = _get_taranaki_metadata(local_paths=local_paths,
                                          meta_data_requirements=meta_data_requirements)
        trc_metadata = trc_data['metadata'].copy()
        trc_gw_data = trc_data['gw_depth_data'].copy()

        trc_discrete_gw_levels = _get_discrete_taranaki_data(local_paths)

        trc_sporadic = _get_bespoke_taranaki_data(local_paths, recalc=False)
        trc_sporadic_set1 = trc_sporadic[trc_sporadic['set'] == 'set1']
        trc_sporadic_set2 = trc_sporadic[trc_sporadic['set'] == 'set2']
        trc_sporadic_set3 = trc_sporadic[trc_sporadic['set'] == 'set3']

        trc_sporadic_set1 = trc_sporadic_set1[['well_name', 'date', 'gw_elevation', 'water_elev_flag']]
        trc_sporadic_set2 = trc_sporadic_set2[['well_name', 'date', 'depth_to_water', 'dtw_flag']]
        trc_sporadic_set3 = trc_sporadic_set3[['well_name', 'date', 'gw_elevation', 'water_elev_flag']]

        concated_sporadic = pd.concat([trc_sporadic_set1, trc_sporadic_set3], ignore_index=True)
        merged_set_sporadic = pd.merge(concated_sporadic, trc_sporadic_set2, how='outer')
        merged_set_sporadic = merged_set_sporadic.sort_values(by=['well_name', 'date'])
        merged_set_sporadic['depth_to_water'] = abs(merged_set_sporadic['depth_to_water'])

        # Extract date parts (year, month, day) for grouping without creating additional dates
        merged_set_sporadic['year'] = merged_set_sporadic['date'].dt.year
        merged_set_sporadic['month'] = merged_set_sporadic['date'].dt.month
        merged_set_sporadic['day'] = merged_set_sporadic['date'].dt.day

        # Group by 'well_name' and the extracted date parts, then calculate mean for the specified columns
        daily_average_data = \
            merged_set_sporadic.groupby(['well_name', 'dtw_flag', 'water_elev_flag', 'year', 'month', 'day'])[
                ['gw_elevation', 'depth_to_water']].mean().reset_index()
        # If needed, reconstruct the 'date' from the grouped year, month, and day
        daily_average_data['date'] = pd.to_datetime(daily_average_data[['year', 'month', 'day']])
        # Drop the year, month, and day columns if they are no longer needed
        daily_average_data = daily_average_data.drop(columns=['year', 'month', 'day'])
        sporadic_data = daily_average_data

        # re force type, as keeps being lost
        for column, dtype in needed_gw_columns_type.items():
            tethys_gw_data[column] = tethys_gw_data[column].astype(dtype)

        for column, dtype in needed_gw_columns_type.items():
            trc_gw_data[column] = trc_gw_data[column].astype(dtype)

        for column, dtype in needed_gw_columns_type.items():
            trc_discrete_gw_levels[column] = trc_discrete_gw_levels[column].astype(dtype)

        for col, dtype in needed_gw_columns_type.items():
            if column in sporadic_data.columns:
                sporadic_data[col] = sporadic_data[col].astype(dtype)

        combined_water_data = pd.concat([tethys_gw_data, trc_gw_data, trc_discrete_gw_levels, sporadic_data],
                                        ignore_index=True)
        combined_water_data['date'] = pd.to_datetime(combined_water_data['date']).dt.date
        combined_water_data['date'] = pd.to_datetime(combined_water_data['date'])
        combined_water_data = aggregate_water_data(combined_water_data)

        combined_water_data['data_source'] = np.where(combined_water_data['data_source'].isna(), 'TRC',
                                                      combined_water_data['data_source'])

        # Ensure 'date' is in datetime format
        combined_water_data['date'] = pd.to_datetime(combined_water_data['date'])
        for column, dtype in needed_gw_columns_type.items():
            combined_water_data[column] = combined_water_data[column].astype(dtype)

        sites_with_data = combined_water_data['well_name'].drop_duplicates()

        # combining the two metadata sets
        combined_metadata = pd.concat([tethys_metadata, trc_metadata], ignore_index=True).sort_values(by='well_name')
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

        # do one bore numbers for tethys 10627, 10923 are known
        # combined_metadata = pd.merge(combined_metadata, sites_with_data, how='inner', on='well_name')

        stats = _get_summary_stats(combined_water_data)
        stats = stats.set_index('well_name')
        combined_metadata = combined_metadata.set_index('well_name')
        combined_metadata = combined_metadata.combine_first(stats)
        combined_metadata = combined_metadata.reset_index()

        combined_metadata = combined_metadata.sort_values(by=['nztm_y', 'nztm_x'], ascending=[True, True])
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
        combined_metadata['start_date'] = pd.to_datetime(combined_metadata['start_date'])
        combined_metadata['end_date'] = pd.to_datetime(combined_metadata['end_date'])

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

        renew_hdf5_store(new_data=combined_water_data, old_path=local_paths['save_path'],
                         store_key=local_paths['wl_store_key'])
        renew_hdf5_store(new_data=combined_metadata, old_path=local_paths['save_path'],
                         store_key=local_paths['taranaki_metadata_store_key'])

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
        'water_level_data': local_path_mapping.joinpath("taranaki_continuous_data"),
        'water_depth_data': local_path_mapping.joinpath("tethys_gw_depth_data"),
        'water_level_metadata': local_path_mapping.joinpath("water_level_all_stations.csv"),
        'water_depth_metadata': local_path_mapping.joinpath("groundwater_depth_all_stations.csv"),
        'thethys_local_save_path': local_base_path.joinpath("gwl_taranaki", "cleaned_data", "tethys_gw_data.hdf"),
        'taranaki_local_save_path': local_base_path.joinpath("gwl_taranaki", "cleaned_data", "taranaki_gw_data.hdf"),
        'local_path': local_path_mapping
    }

    # Store keys are hardcoded as they are specific to this setup
    local_paths['thethys_gw_depth_local_store_key'] = 'taranaki_depth_data'
    local_paths['water_level_data_store_key'] = 'water_level_data'
    local_paths['wl_store_key'] = 'taranaki_gwl_data'
    local_paths['taranaki_metadata_store_key'] = 'taranaki_metadata'
    local_paths['save_path'] = groundwater_data.joinpath('gwl_taranaki', 'cleaned_data', 'combined_taranaki_data.hdf')

    return local_paths


def get_trc_data(recalc=False, redownload=False):
    local_paths = _get_folder_and_local_paths(source_dir=groundwater_data.joinpath('gwl_taranaki'),
                                              local_dir=unbacked_dir.joinpath('taranaki_working/'),
                                              redownload=redownload)
    meta_data_requirements = needed_cols_and_types('TRC')
    return output(local_paths, meta_data_requirements, recalc=recalc)


if __name__ == '__main__':
    data = get_trc_data(recalc=False)
    pass
