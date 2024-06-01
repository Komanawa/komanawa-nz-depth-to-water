"""
This Python script : pulls the HBRC data
created by: Patrick_Durney
on: 20-2-2024
"""

import re

import numpy as np
import pandas as pd
from pyproj import Transformer

from komanawa.nz_depth_to_water.generate_dataset.head_data_processing.data_processing_functions import (find_overlapping_files, copy_with_prompt, \
                                                                                                        _get_summary_stats, append_to_other, needed_cols_and_types, data_checks, \
                                                                                                        metadata_checks, renew_hdf5_store, get_hdf5_store_keys, pull_tethys_data_store,
                                                                                                        assign_flags_based_on_null_values, aggregate_water_data)
from komanawa.nz_depth_to_water.generate_dataset.head_data_processing.merge_rows import merge_rows_if_possible
from komanawa.nz_depth_to_water.generate_dataset.project_base import groundwater_data, unbacked_dir


'''
this is a rework and fininalisation of evelyns code
'''


def _get_hbrc_tethys_data(local_paths, meta_data_requirements):
    """" This function reads in the hbrc data from Tethys
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
                                         council="Hawks Bay Regional Council")
    tethys_metadata = pull_tethys_data_store(
        unbacked_dir.joinpath('tetheys_2024_all', 'tethys_meta_fully_processed.hdf'),
        meta_keys, council="Hawks Bay Regional Council")

    tethys_gw_depth_none = tethys_data['/Hawks Bay Regional Council_groundwater_depth_None'].copy()
    tethys_water_level_none = tethys_data['/Hawks Bay Regional Council_water_level_None'].copy()

    tethys_gw_depth_none['depth_to_water'] = tethys_gw_depth_none['groundwater_depth']
    tethys_gw_depth_none = tethys_gw_depth_none.rename(
        columns={'bore_depth': 'well_depth', 'bore_bottom_of_screen': 'bottom_bottomscreen',
                 'bore_top_of_screen': 'top_topscreen',
                 'altitude': 'tethys_elevation', 'water_level': 'gw_elevation'})

    tethys_data_dtw = tethys_gw_depth_none[needed_gw_columns]
    tethys_data_dtw['data_source'] = "tethys"
    tethys_data_dtw['date'] = pd.to_datetime(tethys_data_dtw['date'], format='mixed')
    tethys_data_dtw.set_index(['well_name', 'date'], inplace=True)
    ##########
    # pull the gw elevation data
    tethys_water_level_none['gw_elevation'] = tethys_water_level_none['water_level']
    tethys_water_level_none = tethys_water_level_none.rename(
        columns={'bore_depth': 'well_depth', 'bore_bottom_of_screen': 'bottom_bottomscreen',
                 'bore_top_of_screen': 'top_topscreen',
                 'altitude': 'tethys_elevation', })

    tethys_data_gwl = tethys_water_level_none[needed_gw_columns]
    tethys_data_gwl['data_source'] = "tethys"
    tethys_data_gwl['date'] = pd.to_datetime(tethys_data_gwl['date'], format='mixed')
    tethys_data_gwl.set_index(['well_name', 'date'], inplace=True)
    ########
    # combine the two water data sets
    combined_water_data = tethys_data_dtw.combine_first(tethys_data_gwl)
    combined_water_data = combined_water_data.reset_index()
    combined_water_data = combined_water_data.sort_values(by=['well_name', 'date'], ascending=[True, True])
    assign_flags_based_on_null_values(combined_water_data, 'depth_to_water', 'dtw_flag', 1, 0)
    # Assign 'water_elev_flag' based on 'gw_elevation'
    assign_flags_based_on_null_values(combined_water_data, 'gw_elevation', 'water_elev_flag', 1, 0)

    tethys_metadata_gwl = tethys_metadata['/Hawks Bay Regional Council_water_level_None_metadata'].copy()
    tethys_metadata_dtw = tethys_metadata['/Hawks Bay Regional Council_groundwater_depth_None_metadata'].copy()

    tethys_groundwater_data_metadata = pd.concat([tethys_metadata_gwl, tethys_metadata_dtw],
                                                 ignore_index=True).sort_values(by='well_name')
    tethys_groundwater_data_metadata = tethys_groundwater_data_metadata.drop_duplicates(subset='tethys_station_id')

    for col, dtype in meta_data_requirements['col_types'].items():
        if col in tethys_groundwater_data_metadata.columns:
            # If column exists, convert its data type
            tethys_groundwater_data_metadata[col] = tethys_groundwater_data_metadata[col].astype(dtype)
        else:
            tethys_groundwater_data_metadata[col] = meta_data_requirements['default_values'].get(col)


    if 'other' not in tethys_groundwater_data_metadata.columns:
        tethys_groundwater_data_metadata['other'] = ''

    tethys_groundwater_data_metadata = append_to_other(df=tethys_groundwater_data_metadata,
                                                       needed_columns=meta_data_requirements["needed_columns"])
    tethys_groundwater_data_metadata['well_depth'] = np.nan
    tethys_groundwater_data_metadata = tethys_groundwater_data_metadata[meta_data_requirements['needed_columns']]
    tethys_groundwater_data_metadata['source'] = 'tethys'
    tethys_groundwater_data_metadata['start_date'] = pd.to_datetime(tethys_groundwater_data_metadata['start_date'],
                                                                    format='mixed')
    tethys_groundwater_data_metadata['end_date'] = pd.to_datetime(tethys_groundwater_data_metadata['end_date'],
                                                                  format='mixed')

    return {'tethys_groundwater_data': combined_water_data,
            'tethys_metadata_combined': tethys_groundwater_data_metadata}


def _extract_well_name(site_name):
    # Use re.search to find the first pattern where digits are immediately followed by non-space, non-underscore characters
    # The pattern \d+ captures one or more digits, and [^\s_]* captures zero or more characters that are neither spaces nor underscores
    match = re.search(r'(\d+[^\s_]*)', site_name)
    if match:
        # Extract the matched group if a match is found
        return match.group(1)
    else:
        # Return an empty string or some default value if no match is found
        return ''


def _get_missing_hawkes_bay_metadata(local_paths, meta_data_requirements):
    """This function reads in the missing hawkes bay metadata"""

    file_path = local_paths['local_path'] / 'HBRC_Wells_Metadata.xlsx'
    df = pd.read_excel(file_path, skiprows=0)
    new_names = {"Bore No": "well_no", 'Site Name': 'well_name', "Drill date": "start_date",
                 'Screen top 1 (m)': 'top_topscreen', 'Screen bottom 1 (m)': 'bottom_bottomscreen',
                 "Initial water level (m)": 'depth_to_water_static'
                 }
    df.rename(columns=new_names, inplace=True)
    df['end_date'] = df['start_date']

    transformer = Transformer.from_crs("EPSG:27200", "EPSG:2193")
    y, x = transformer.transform(pd.to_numeric(df.loc[:, 'Easting'], errors='coerce'),
                                 pd.to_numeric(df.loc[:, 'Northing'], errors='coerce'))
    df.loc[:, 'nztm_x'] = x.round(0)
    df.loc[:, 'nztm_y'] = y.round(0)

    df.drop(columns=['Northing', 'Easting'], inplace=True)
    df = df.astype({'well_name': 'str', 'nztm_x': 'float', 'nztm_y': 'float'})

    return df


def _get_extra_gwl_data(local_paths, meta_data_requirements):
    """This function reads in the extra hawkes back data sent through by HBRC"""
    timeseries_path = local_paths["local_path"] / 'GWL_LandSurface.xlsx'

    df = pd.read_excel(timeseries_path, skiprows=0)
    # extract name number
    df['well_name'] = df['Site Name']
    df['data_source'] = 'hbrc'
    # renaming the columns
    new_names = {'Time': 'date', 'Depth From Land Surface': 'depth_to_water'}
    df.drop(columns=['Site Name', "Easting", 'Northing'], inplace=True)
    df.rename(columns=new_names, inplace=True)

    return df


def output(local_paths, meta_data_requirements, recalc= False):
    """This function combines the two sets of metadata and cleans it
    :return: dataframe"""
    needed_gw_columns = ['well_name', 'date', 'depth_to_water', 'gw_elevation', 'dtw_flag', 'water_elev_flag',
                         'data_source', 'elevation_datum', 'other']

    needed_gw_columns_type = {'well_name': "str", 'depth_to_water': "float", 'gw_elevation': "float",
                              'dtw_flag': "Int64",
                              'water_elev_flag': 'Int64',
                              'data_source': 'str', 'elevation_datum': "str", 'other': "str"}

    water_data_store_path = local_paths['save_path']
    store_key_water_data = local_paths['wl_store_key']
    store_key_metadata = local_paths['hbrc_metadata_store_key']

    # Check if data needs to be recalculated or if the HDF files don't exist
    if not recalc and water_data_store_path.exists():
        combined_water_data = pd.read_hdf(water_data_store_path, store_key_water_data)
        combined_metadata = pd.read_hdf(water_data_store_path, store_key_metadata)

    else:

        tethys_data = _get_hbrc_tethys_data(local_paths, meta_data_requirements)
        tethys_gw_data = tethys_data['tethys_groundwater_data'].copy()
        tethys_gw_data['well_name'] = tethys_gw_data["well_name"].astype(str)
        tethys_gw_data['other'] = tethys_gw_data["other"].astype(str)

        tetheys_metadata = tethys_data['tethys_metadata_combined'].copy()
        tetheys_metadata['well_name'] = tetheys_metadata["well_name"].astype(str)

        hbrc_metadata = _get_missing_hawkes_bay_metadata(local_paths=local_paths,
                                                         meta_data_requirements=meta_data_requirements)

        hbrc_gwl_data = _get_extra_gwl_data(local_paths, meta_data_requirements)

        for column in needed_gw_columns:
            if column not in hbrc_gwl_data.columns:
                # Add the missing column and initialize with NaNs or another suitable default value
                hbrc_gwl_data[column] = np.nan
        for column, dtype in needed_gw_columns_type.items():
            hbrc_gwl_data[column] = hbrc_gwl_data[column].astype(dtype)

        assign_flags_based_on_null_values(hbrc_gwl_data, 'depth_to_water', 'dtw_flag', 1, 0)
        assign_flags_based_on_null_values(hbrc_gwl_data, 'gw_elevation', 'water_elev_flag', 1, 0)

        hbrc_additonal_gw_data = hbrc_metadata[['well_name', 'start_date', 'depth_to_water_static']]
        hbrc_additonal_gw_data['depth_to_water'] = np.where(hbrc_additonal_gw_data['depth_to_water_static'] == 0, np.nan,
                                                            hbrc_additonal_gw_data['depth_to_water_static'])
        hbrc_additonal_gw_data = hbrc_additonal_gw_data[['well_name', 'start_date', 'depth_to_water']]
        hbrc_additonal_gw_data = hbrc_additonal_gw_data.rename(columns={'start_date': 'date'})

        for column in needed_gw_columns:
            if column not in hbrc_additonal_gw_data.columns:
                # Add the missing column and initialize with NaNs or another suitable default value
                hbrc_additonal_gw_data[column] = np.nan
        for column, dtype in needed_gw_columns_type.items():
            hbrc_additonal_gw_data[column] = hbrc_additonal_gw_data[column].astype(dtype)

        assign_flags_based_on_null_values(hbrc_additonal_gw_data, 'depth_to_water', 'dtw_flag', 3, 0)
        assign_flags_based_on_null_values(hbrc_additonal_gw_data, 'gw_elevation', 'water_elev_flag', 1, 5)

        hbrc_gw_data = pd.concat([hbrc_gwl_data, hbrc_additonal_gw_data], ignore_index=True).sort_values(by='well_name')
        hbrc_gw_data = hbrc_gw_data.dropna(subset=['depth_to_water'])
        hbrc_gw_data['data_source'] = 'HBRC'
        hbrc_gw_data['elevation_datum'] = 'nzvd2016'
        # keynote hbrc depth to water is negative for below gl multiplying by -1
        hbrc_gw_data['depth_to_water'] = hbrc_gw_data['depth_to_water'] * -1

        combined_water_data = (pd.concat([tethys_gw_data, hbrc_gw_data], ignore_index=True))
        # clean up the well names
        pattern = r'[.]+'
        combined_water_data['well_name'] = combined_water_data['well_name'].str.replace(pattern, '_', regex=True)
        combined_water_data['date'] = pd.to_datetime(combined_water_data['date'], format='mixed', errors='coerce')
        combined_water_data = (combined_water_data.sort_values(['well_name', 'date'], ascending=[True, True]))
        for column, dtype in needed_gw_columns_type.items():
            combined_water_data[column] = combined_water_data[column].astype(dtype)
        combined_water_data['date'] = pd.to_datetime(combined_water_data['date']).dt.date
        combined_water_data['date'] = pd.to_datetime(combined_water_data['date'])

        combined_water_data = aggregate_water_data(combined_water_data)

        combined_water_data['well_name'] = combined_water_data['well_name'].astype(str)
        #### metadata processing and merge

        hbrc_metadata['start_date'] = pd.to_datetime(hbrc_metadata['start_date'], format='mixed', errors='coerce')
        hbrc_metadata['end_date'] = pd.to_datetime(hbrc_metadata['end_date'], format='mixed', errors='coerce')
        # combining the two metadata sets
        combined_metadata = pd.concat([tetheys_metadata, hbrc_metadata], ignore_index=True)
        combined_metadata['well_name'] = combined_metadata['well_name'].str.replace(pattern, '_', regex=True)
        combined_metadata = combined_metadata.sort_values(by='well_name')
        combined_metadata['start_date'] = pd.to_datetime(combined_metadata['start_date'])
        combined_metadata['end_date'] = pd.to_datetime(combined_metadata['end_date'])

        default_precision = 0.1  # for example, default precision is 2 decimal places

        # create dict of precisis ofr none str columns
        precisions = {col: default_precision for col in combined_metadata.columns
                      if combined_metadata[col].dtype != object and not pd.api.types.is_datetime64_any_dtype(
                combined_metadata[col])}
        precisions['X'] = 15
        precisions['Y'] = 15

        # Create a list of columns to skip, which are of string type
        skip_cols = [col for col in combined_metadata.columns
                     if
                     combined_metadata[
                         col].dtype == object]  # or pd.api.types.is_datetime64_any_dtype(combined_metadata[col])]

        aggregation_functions = {col: np.nanmean for col in precisions}
        aggregation_functions['start_date'] = np.min  # Keep the earliest date for 'start_date'
        aggregation_functions['end_date'] = np.max  # Keep the latest date for 'end_date'

        combined_metadata = merge_rows_if_possible(combined_metadata, on='well_name', precision=precisions,
                                                   skip_cols=skip_cols, actions=aggregation_functions)
        stats = _get_summary_stats(combined_water_data)
        stats = stats.set_index('well_name')
        combined_metadata = combined_metadata.set_index('well_name')
        combined_metadata = combined_metadata.combine_first(stats)
        combined_metadata = combined_metadata.reset_index()

        combined_metadata = combined_metadata.sort_values(by=['well_name', 'start_date'], ascending=[True, True])
        # code here to fix -ve depth to water when hbrc confirms

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
        combined_metadata['ground_level_source'] = None

        for column in cols_to_keep:
            # Check if the column is of pandas nullable Int64 type
            if pd.api.types.is_integer_dtype(combined_metadata[column]) and combined_metadata[
                column].isnull().any():
                # Convert to float64 if there are NaN values, as NaN cannot be represented in pandas' non-nullable integer types
                combined_metadata[column] = combined_metadata[column].astype('float64')
            elif pd.api.types.is_integer_dtype(combined_metadata[column]):
                # Convert to NumPy's int64 if there are no NaN values and it is a pandas Int64 type
                combined_metadata[column] = combined_metadata[column].astype('int64')
        valid_col_types = {col: dtype for col, dtype in meta_data_requirements['col_types'].items() if
                           col in combined_metadata.columns}
        # Use DataFrame.astype() to convert data types
        combined_metadata = combined_metadata.astype(valid_col_types)

        for column in combined_water_data:
            # Check if the column is of pandas nullable Int64 type
            if pd.api.types.is_integer_dtype(combined_water_data[column]) and combined_water_data[
                column].isnull().any():
                # Convert to float64 if there are NaN values, as NaN cannot be represented in pandas' non-nullable integer types
                combined_water_data[column] = combined_water_data[column].astype('float64')
            elif pd.api.types.is_integer_dtype(combined_water_data[column]):
                # Convert to NumPy's int64 if there are no NaN values and it is a pandas Int64 type
                combined_water_data[column] = combined_water_data[column].astype('int64')

        needed_gw_columns_type = {'well_name': "str", 'depth_to_water': "float", 'gw_elevation': "float",
                                  'dtw_flag': "int",
                                  'water_elev_flag': 'int',
                                  'data_source': 'str', 'elevation_datum': "str", 'other': "str"}
        combined_water_data = combined_water_data.astype(needed_gw_columns_type)

        renew_hdf5_store(new_data=combined_metadata, old_path=local_paths['save_path'],
                         store_key=local_paths['hbrc_metadata_store_key'])
        renew_hdf5_store(new_data=combined_water_data, old_path=local_paths['save_path'],
                         store_key=local_paths['wl_store_key'])

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
        # flag that water_level _metadata is horizons not hbrc
        'water_depth_metadata': local_path_mapping.joinpath('tethys_metadata', "groundwater_depth_all_stations.csv"),
        'tethys_local_save_path': local_base_path.joinpath("gwl_hbrc", "cleaned_data", "tethys_gw_data.hdf"),
        'hbrc_local_save_path': local_base_path.joinpath("gwl_hbrc", "cleaned_data", "hbrc_gw_data.hdf"),
        'local_path': local_path_mapping
    }

    # Store keys are hardcoded as they are specific to this setup
    local_paths['tethys_gw_depth_local_store_key'] = 'hbrc_depth_data'
    local_paths['tethys_water_level_data_store_key'] = 'water_level_data'
    local_paths['wl_store_key'] = 'hbrc_gwl_data'
    local_paths['hbrc_metadata_store_key'] = 'hbrc_metadata'
    local_paths['save_path'] = groundwater_data.joinpath('gwl_hawkes_bay', 'cleaned_data', 'combined_hbrc_data.hdf')

    return local_paths

def get_hbrc_data(recalc= False, redownload=False):
    """This function reads in the HBRC data"""
    local_paths = _get_folder_and_local_paths(source_dir=groundwater_data.joinpath('gwl_hawkes_bay'),
                                              local_dir=unbacked_dir.joinpath('hbrc_working/'), redownload=redownload)
    meta_data_requirements = needed_cols_and_types('hbrc')
    return output(local_paths, meta_data_requirements, recalc= recalc)



if __name__ == '__main__':
    data =get_hbrc_data(recalc= False)
    pass
