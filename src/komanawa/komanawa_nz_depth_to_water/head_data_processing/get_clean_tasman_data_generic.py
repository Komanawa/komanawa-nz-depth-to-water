"""
created Evelyn_Charlesworth 
on: 2/10/2023
"""
""" This script cleans and processes the Tasman GWL data"""
import pandas as pd
from komanawa.komanawa_nz_depth_to_water.project_base import groundwater_data, unbacked_dir

from komanawa.komanawa_nz_depth_to_water.head_data_processing.data_processing_functions import (find_overlapping_files,
                                                                                                copy_with_prompt, \
                                                                                                _get_summary_stats,
                                                                                                append_to_other,
                                                                                                needed_cols_and_types,
                                                                                                data_checks, \
                                                                                                metadata_checks,
                                                                                                renew_hdf5_store,
                                                                                                pull_tethys_data_store,
                                                                                                get_hdf5_store_keys,
                                                                                                aggregate_water_data,
                                                                                                assign_flags_based_on_null_values)
import numpy as np
from komanawa.komanawa_nz_depth_to_water.head_data_processing.merge_rows import merge_rows_if_possible
import datetime


def _get_tasman_tethys_data(meta_data_requirements):
    """" This function reads in the gisborne data from Tethys
            dtw_flag = 1= logger, 2= manual, 3= static_oneoff, 4= calculated frm gw_elevation, 5= aquifer test, 6= other
    water_ele_flag = 1= logger, 2= manual, 3= static_oneoff, 4= aquifer test, 5= other
    """
    needed_gw_columns = ['well_name', 'date', 'depth_to_water', 'gw_elevation', 'dtw_flag', 'water_elev_flag',
                         'data_source', 'elevation_datum', 'other']

    needed_gw_columns_type = {'well_name': "str", 'depth_to_water': "float", 'gw_elevation': "float",
                              'dtw_flag': "Int64",
                              'water_elev_flag': 'Int64',
                              'data_source': 'str', 'elevation_datum': "str", 'other': "str"}

    data_keys = get_hdf5_store_keys(unbacked_dir.joinpath('tetheys_2024_all', 'tethys_fully_processed.hdf'))
    meta_keys = get_hdf5_store_keys(unbacked_dir.joinpath('tetheys_2024_all', 'tethys_meta_fully_processed.hdf'))

    tethys_data = pull_tethys_data_store(unbacked_dir.joinpath('tetheys_2024_all', 'tethys_fully_processed.hdf'),
                                         data_keys,
                                         council="Tasman")
    tethys_metadata = pull_tethys_data_store(
        unbacked_dir.joinpath('tetheys_2024_all', 'tethys_meta_fully_processed.hdf'),
        meta_keys, council="Tasman")

    tethys_metadata_dtw_24h = tethys_metadata['/Tasman District Council_groundwater_depth_24H_metadata']

    tethys_data_dtw_24h = tethys_data['/Tasman District Council_groundwater_depth_24H']
    # keynote cant be depth to water as the water level is deeper than borehole ??????? can't tell
    # keynote I think it is depth and the bore depth value is wrong
    # tethys_data_dtw_24h['gw_elevation'] = tethys_data_dtw_24h['groundwater_depth']
    tethys_data_dtw_24h['depth_to_water'] = tethys_data_dtw_24h['groundwater_depth']

    tethys_data_dtw = tethys_data_dtw_24h[needed_gw_columns]
    tethys_data_dtw['data_source'] = "tethys"

    assign_flags_based_on_null_values(tethys_data_dtw, 'depth_to_water', 'dtw_flag', 1, 0)
    assign_flags_based_on_null_values(tethys_data_dtw, 'gw_elevation', 'water_elev_flag', 1, 0)

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

    return {'tethys_groundwater_data': tethys_data_dtw,
            'tethys_metadata_combined': tethys_metadata_dtw_24h}


def _get_sporadic_tasman_data(local_paths):
    """This function reads in the sporadic gwl data sent by Tasman
    :returns: dataframe
    """
    needed_gw_columns = ['well_name', 'date', 'depth_to_water', 'gw_elevation', 'dtw_flag', 'water_elev_flag',
                         'data_source', 'elevation_datum', 'other']

    needed_gw_columns_type = {'well_name': "str", 'depth_to_water': "float", 'gw_elevation': "float", 'dtw_flag': "int",
                              'water_elev_flag': 'int',
                              'data_source': 'str', 'elevation_datum': "str", 'other': "str"}
    # reading in the data
    all_data = pd.read_excel(
        local_paths['local_path'] / 'gwl_sporadic_tasman' / '2023-04 BoresWLdataALL.xlsx')

    # choosing which columns to keep
    sporadic_gwl_data_tasman = all_data[
        ['BoreID', 'OldBore#', 'CollectedOn', 'RIM Level', 'RTS', 'RLWL', 'Ground Level']]
    # renaming the columns
    new_names = {'BoreID': 'well_name', 'OldBore#': 'alt_well_name', 'CollectedOn': 'date', 'RIM Level': 'rim_level',
                 'RTS': 'depth_to_water', 'RLWL': 'gw_elevation', 'Ground Level': 'ground_elevation'}

    sporadic_gwl_data_tasman.rename(columns=new_names, inplace=True)
    sporadic_gwl_data_tasman["other"] = "datum = NVD1955_or_TVD1982_if_in_Golden_Bay"
    sporadic_gwl_data_tasman['depth_to_water'] = sporadic_gwl_data_tasman['depth_to_water'] / 1000
    sporadic_gwl_data_tasman['gw_elevation'] = sporadic_gwl_data_tasman['gw_elevation'] / 1000
    sporadic_gwl_data_tasman['rim_level'] = sporadic_gwl_data_tasman['rim_level'] / 1000
    sporadic_gwl_data_tasman['ground_to_collar'] = sporadic_gwl_data_tasman['rim_level'] - sporadic_gwl_data_tasman[
        'ground_elevation']

    sporadic_gwl_data_tasman['depth_to_water'] = np.where(pd.notnull(sporadic_gwl_data_tasman['ground_to_collar']),
                                                          sporadic_gwl_data_tasman['depth_to_water'] -
                                                          sporadic_gwl_data_tasman['ground_to_collar'],
                                                          sporadic_gwl_data_tasman['depth_to_water'])

    for column in needed_gw_columns:
        if column not in sporadic_gwl_data_tasman.columns:
            # Add the missing column and initialize with NaNs or another suitable default value
            sporadic_gwl_data_tasman[column] = np.nan

    assign_flags_based_on_null_values(sporadic_gwl_data_tasman, 'depth_to_water', 'dtw_flag', 3, 0)
    assign_flags_based_on_null_values(sporadic_gwl_data_tasman, 'gw_elevation', 'water_elev_flag', 3, 0)

    sporadic_gwl_data_tasman['data_source'] = "TRC"
    sporadic_gwl_data_tasman['elevation_datum'] = None

    sporadic_gwl_data_tasman['well_name'] = np.where(pd.notnull(sporadic_gwl_data_tasman['well_name']),
                                                     sporadic_gwl_data_tasman['well_name'],
                                                     sporadic_gwl_data_tasman['alt_well_name'])

    sporadic_gwl_data_tasman = append_to_other(df=sporadic_gwl_data_tasman, needed_columns=needed_gw_columns)
    sporadic_gwl_data_tasman = sporadic_gwl_data_tasman[needed_gw_columns]
    sporadic_gwl_data_tasman['well_name'] = 'GW ' + sporadic_gwl_data_tasman["well_name"].astype(str)

    for col, dtype in needed_gw_columns_type.items():
        sporadic_gwl_data_tasman[col] = sporadic_gwl_data_tasman[col].astype(dtype)

    return sporadic_gwl_data_tasman


def _get_sporadic_tasman_metadata(local_paths, meta_data_requirements):
    """This function reads in the metadata for the sporadic gwl data sent by Tasman
    :returns: dataframe
    """

    metadata = pd.read_excel(
        local_paths['local_path'] / 'gwl_sporadic_tasman' / '2023-04 BoresWLdataALL.xlsx')

    metadata = metadata.drop_duplicates(subset=['BoreID'])

    new_names = {'BoreID': 'well_name', 'OldBore#': 'alt_well_name', 'CollectedOn': 'date', 'Easting(NZTM)': 'nztm_x',
                 'Northing(NZTM)': 'nztm_y',
                 'Bore Depth': 'well_depth', 'Ground Level': 'ground_elevation',
                 'Collar Set': 'collar_depth',
                 'Screen1 set': 'screen1_depth', 'Screen2 Set': 'screen2_depth',
                 'Screen3 Set': 'screen3_depth', 'Comments': 'comments'}
    metadata.rename(columns=new_names, inplace=True)
    metadata['dist_mp_to_ground_level'] = (metadata["RIM Level"] / 1000
                                           - metadata["ground_elevation"]) * -1
    metadata["ground_elevation"] = np.where(pd.notnull(metadata["ground_elevation"]),
                                            metadata["ground_elevation"], metadata["RIM Level"] / 1000)

    metadata.drop(columns=['RIM Level', 'RTS', 'RLWL'], inplace=True)

    # handling the collar range
    metadata['min_collar_set'], metadata['max_collar_set'] = zip(*metadata['collar_depth'].apply(split_range))

    # handling the screen ranges, subsetting the screen ranges
    screen_ranges = metadata[['screen1_depth', 'screen2_depth', 'screen3_depth']]
    metadata[['top_topscreen', 'bottom_bottomscreen']] = screen_ranges.apply(process_row, axis=1)

    # handling datatypes
    metadata = metadata.astype(
        {'well_name': 'str', 'alt_well_name': 'str', 'nztm_y': 'float', 'nztm_x': 'float',
         'well_depth': 'float', 'ground_elevation': 'float', 'collar_depth': 'str', 'screen1_depth': 'str',
         'screen2_depth': 'str', 'screen3_depth': 'str', 'comments': 'str', 'min_collar_set': 'float',
         'max_collar_set': 'float',
         'top_topscreen': 'float', 'bottom_bottomscreen': 'float'})

    # handling date column
    metadata['date'] = pd.to_datetime(metadata['date'], dayfirst=True)

    metadata['source'] = 'TDC'

    for col in meta_data_requirements['needed_columns']:
        if col not in metadata.columns:
            metadata[col] = meta_data_requirements['default_values'].get(col)

    for col, dtype in meta_data_requirements['col_types'].items():
        metadata[col] = metadata[col].astype(dtype)

    metadata['well_name'] = np.where(pd.notnull(metadata['well_name']),
                                     metadata['well_name'], metadata['alt_well_name'])

    metadata = append_to_other(df=metadata, needed_columns=meta_data_requirements["needed_columns"])
    metadata = metadata[meta_data_requirements['needed_columns']]
    metadata['well_name'] = 'GW ' + metadata["well_name"].astype(str)

    return metadata


def process_row(row):
    min_vals = []
    max_vals = []

    for col in row.index:
        value = row[col]
        if isinstance(value, str) and '-' in value:
            min_val, max_val = map(float, value.split('-'))
        elif isinstance(value, pd.Timestamp):  # Check if it's a timestamp
            min_val = max_val = value
        else:
            min_val = max_val = float(value)
        min_vals.append(min_val)
        max_vals.append(max_val)

    return pd.Series({'min_screen_set': min(min_vals), 'max_screen_set': max(max_vals)})


def split_range(value):
    """ A function used to split the ranges in the metadata"""

    if isinstance(value, str) and '-' in value:
        min_val, max_val = map(float, value.split('-'))
        return min_val, max_val
    elif isinstance(value, (int, float)):
        return float(value), float(value)
    else:
        return None, None


def output(local_paths, meta_data_requirements, recalc=False):
    """This function combines the two sets of metadata and cleans it
    :return: dataframe"""
    water_data_store_path = local_paths['save_path']
    store_key_water_data = local_paths['wl_store_key']
    store_key_metadata = local_paths['tasman_metadata_store_key']

    # Check if data needs to be recalculated or if the HDF files don't exist
    if not recalc and water_data_store_path.exists():
        combined_water_data = pd.read_hdf(water_data_store_path, store_key_water_data)
        combined_metadata = pd.read_hdf(water_data_store_path, store_key_metadata)

    else:
        needed_gw_columns_type = {'well_name': "str", 'depth_to_water': "float", 'gw_elevation': "float",
                                  'dtw_flag': "int",
                                  'water_elev_flag': 'int',
                                  'data_source': 'str', 'elevation_datum': "str", 'other': "str"}

        tethys_data = _get_tasman_tethys_data(meta_data_requirements)
        tethy_gw_data = tethys_data['tethys_groundwater_data']
        tethy_gw_data['well_name_x'] = tethy_gw_data["well_name"].astype(str).str.extract(r'([A-Za-z]+\s\d+)')
        tethy_gw_data['well_name'] = np.where(pd.notnull(tethy_gw_data['well_name_x']),
                                              tethy_gw_data['well_name_x'], tethy_gw_data['well_name'])
        tethy_gw_data['date'] = pd.to_datetime(tethy_gw_data['date'])
        tethy_gw_data = tethy_gw_data.drop(columns=['well_name_x'])

        tetheys_metadata = tethys_data['tethys_metadata_combined']
        tetheys_metadata['well_name_x'] = tetheys_metadata["well_name"].astype(str).str.extract(r'([A-Za-z]+\s\d+)')
        tetheys_metadata['well_name'] = np.where(pd.notnull(tetheys_metadata['well_name_x']),
                                                 tetheys_metadata['well_name_x'], tetheys_metadata['well_name'])
        tetheys_metadata = tetheys_metadata.drop(columns=['well_name_x'])

        tdc_metadata = _get_sporadic_tasman_metadata(local_paths=local_paths,
                                                     meta_data_requirements=meta_data_requirements)

        tdc_gw_data = _get_sporadic_tasman_data(local_paths=local_paths)
        tdc_gw_data['well_name'] = tdc_gw_data['well_name'].str.replace('\.0$', '', regex=True)

        combined_water_data = pd.concat([tethy_gw_data, tdc_gw_data], ignore_index=True)
        combined_water_data['date'] = pd.to_datetime(combined_water_data['date']).dt.date
        combined_water_data['date'] = pd.to_datetime(combined_water_data['date'])
        combined_water_data['date'] = np.where(
            pd.isnull(combined_water_data['date']),
            pd.to_datetime('1900-01-01 00:00:00'),
            combined_water_data['date'])

        combined_water_data['date'] = pd.to_datetime(combined_water_data['date'])
        combined_water_data['date'] = pd.to_datetime(combined_water_data['date'])
        combined_water_data = combined_water_data.reset_index(drop=True)

        combined_water_data = combined_water_data.sort_values(by=["well_name", 'date'], ascending=[True, True])

        combined_water_data['data_source'] = np.where(combined_water_data['data_source'].isna(), 'TDC',
                                                      combined_water_data['data_source'])

        for column, dtype in needed_gw_columns_type.items():
            combined_water_data[column] = combined_water_data[column].astype(dtype)

        combined_water_data['temp_name'] = combined_water_data['well_name'] + combined_water_data['date'].astype(str)
        dups = combined_water_data[combined_water_data.duplicated(subset=['temp_name'], keep=False)]
        dups = dups.drop(dups[dups['depth_to_water'] > 100].index)

        def handle_group(group):
            # Check if any row in the group has 'dtw_flag' equal to 1
            if any(group['dtw_flag'] == 1):
                # Select the first row where 'dtw_flag' is 1
                return group[group['dtw_flag'] == 1].head(1)
            else:
                # Calculate the mean of 'depth_to_water' for the group
                mean_dtw = group['depth_to_water'].mean()
                # Create a new row with the mean value and other necessary attributes
                # Here, we use the first row as a template and update 'depth_to_water'
                mean_row = group.head(1).copy()
                mean_row['depth_to_water'] = mean_dtw
                mean_row['dtw_flag'] = np.nan  # or any value you see fit
                return mean_row

        # Group by 'temp_name' and apply the 'handle_group' function to each group
        deduped = pd.concat([handle_group(group) for _, group in dups.groupby('temp_name')])
        deduped['dtw_flag'] = np.where(pd.isnull(deduped['dtw_flag']), 3, deduped['dtw_flag'])
        # Reset index if necessary
        deduped.reset_index(drop=True, inplace=True)
        combined_water_data = pd.concat(
            [combined_water_data.copy().drop_duplicates(subset=['temp_name'], keep=False), deduped])
        combined_water_data = combined_water_data.drop(columns=['temp_name'])

        tdc_metadata['start_date'] = pd.to_datetime(tdc_metadata['start_date'])
        tdc_metadata['end_date'] = pd.to_datetime(tdc_metadata['end_date'])
        # combining the two metadata sets
        tetheys_metadata['start_date'] = pd.to_datetime(tetheys_metadata['start_date'])
        tetheys_metadata['end_date'] = pd.to_datetime(tetheys_metadata['end_date'])
        tetheys_metadata['well_depth'] = tetheys_metadata['well_depth'].astype(float)

        combined_metadata = pd.merge(tetheys_metadata, tdc_metadata, how='outer')
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

        # combined_metadata = pd.concat([tetheys_metadata, tdc_metadata], ignore_index=True).sort_values(by='well_name')

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
        combined_metadata = combined_metadata.dropna(subset=['well_name'])

        renew_hdf5_store(new_data=combined_water_data, old_path=local_paths['save_path'],
                         store_key=local_paths['wl_store_key'])
        renew_hdf5_store(new_data=combined_metadata, old_path=local_paths['save_path'],
                         store_key=local_paths['tasman_metadata_store_key'])

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
        'water_level_data': local_path_mapping.joinpath("tasman_continuous_data"),
        'water_depth_data': local_path_mapping.joinpath("tethys_gw_depth_data"),
        'water_level_metadata': local_path_mapping.joinpath("water_level_all_stations.csv"),
        'water_depth_metadata': local_path_mapping.joinpath("groundwater_depth_all_stations.csv"),
        'thethys_local_save_path': local_base_path.joinpath("gwl_tasman", "cleaned_data", "tethys_gw_data.hdf"),
        'tasman_local_save_path': local_base_path.joinpath("gwl_tasman", "cleaned_data", "tasman_gw_data.hdf"),
        'local_path': local_path_mapping
    }

    # Store keys are hardcoded as they are specific to this setup
    local_paths['thethys_gw_depth_local_store_key'] = 'tasman_depth_data'
    local_paths['water_level_data_store_key'] = 'water_level_data'
    local_paths['wl_store_key'] = 'tasman_gwl_data'
    local_paths['tasman_metadata_store_key'] = 'tasman_metadata'
    local_paths['save_path'] = groundwater_data.joinpath('gwl_tasman', 'cleaned_data', 'combined_tasman_data.hdf')

    return local_paths


def get_tdc_data(recalc=False, redownload=False):
    local_paths = _get_folder_and_local_paths(source_dir=groundwater_data.joinpath('gwl_tasman'),
                                              local_dir=unbacked_dir.joinpath('tasman_working/'), redownload=redownload)
    meta_data_requirements = needed_cols_and_types('TDC')
    return output(local_paths, meta_data_requirements, recalc=recalc)


if __name__ == '__main__':
    data = get_tdc_data(recalc=True)
    pass
