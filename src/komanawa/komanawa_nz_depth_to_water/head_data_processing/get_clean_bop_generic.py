"""
This Python script : does xxx
created by: Patrick_Durney
on: 26/02/24
"""

import logging
import os
import numpy as np
import pandas as pd

from komanawa.komanawa_nz_depth_to_water.project_base import groundwater_data, unbacked_dir
from komanawa.komanawa_nz_depth_to_water.head_data_processing.data_processing_functions import (find_overlapping_files,
                                                                                                copy_with_prompt, \
                                                                                                _get_summary_stats,
                                                                                                needed_cols_and_types,
                                                                                                metadata_checks, \
                                                                                                data_checks,
                                                                                                append_to_other,
                                                                                                assign_flags_based_on_null_values,
                                                                                                renew_hdf5_store,
                                                                                                aggregate_water_data)
from komanawa.komanawa_nz_depth_to_water.head_data_processing.merge_rows import merge_rows_if_possible


def _get_metadata(local_paths, file_name, skiprows=0):
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
    st_wl.loc[:, 'data_source'] = "BOPRC"
    st_wl.loc[:, 'elevation_datum'] = "NZVD2016"
    st_wl.loc[:, 'other'] = "static_wl"
    st_wl.loc[:, 'date'] = pd.to_datetime(None)
    st_wl['date'] = pd.to_datetime(st_wl['date'])
    st_wl = st_wl.drop(columns=['rl'])
    return st_wl


def determine_prefix(location):
    location = location.lower()
    if 'piezo' in location or 'bore' in location:
        return 'BN-'
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


def _get_wl_bop_data(local_paths, folder_path, metadata):
    """This reads in the continuous timeseries data"""

    site_data = pd.read_excel(local_paths['local_path'] / 'Groundwater Level Site List.xlsx', skiprows=1)

    # Apply the function to create a new column for the prefix
    site_data['prefix'] = site_data['Location'].apply(determine_prefix)

    # Extract the number from the Location
    site_data['extracted_number'] = site_data['Location'].str.extract(r'(\d+(?:-\d+)?)(?=\s+at|\s+\d+|\))')

    # Apply the function to create the well_name column
    site_data['well_name'] = site_data.apply(create_well_name, axis=1)

    # Proceed with the rest of your operations
    site_data = site_data.drop_duplicates(subset=['well_name'])
    site_lookup = dict(zip(site_data['Data Set Id'], site_data['well_name']))
    site_lookup1 = dict(zip(site_data['Data Set Id'], site_data['Location']))
    site_lookup = {k.strip().upper(): v for k, v in site_lookup.items()}
    site_lookup1 = {k.strip().upper(): v for k, v in site_lookup1.items()}

    data = []
    for filename in os.listdir(folder_path):
        file_path = folder_path / filename
        try:
            df = pd.read_excel(file_path, skiprows=2)
        except Exception as e:
            print(f"Error reading file {filename}: {e}")
            continue

        key = filename.replace("DataSetExport-", "").replace(".xlsx", "")
        df['key'] = key
        df['key'] = df['key'].str.split("-Aggregate-").str[0]
        df['key'] = df['key'].str.strip().str.upper()
        df['site_name'] = df['key'].map(site_lookup).fillna(np.nan)
        df['other'] = df['key'].map(site_lookup1).fillna(np.nan)
        data.append(df)

    if data:
        combined_bop_gwl_df = pd.concat(data, ignore_index=True).dropna(subset=['Value (m)'])
    else:
        print("No data files were processed.")

    df = combined_bop_gwl_df.copy()
    df.drop(columns=['key'], inplace=True)
    df.rename(columns={'Value (m)': 'gw_elevation'}, inplace=True)
    df['data_source'] = "BOPRC"
    df['elevation_datum'] = "moturiki"
    df['other'] = df['other'].astype(str) + " time_series"
    df['date'] = pd.to_datetime(df['Start of Interval (UTC+12:00)'])
    # to account for the fact the data is average for period between midnight to midnight
    df = df.sort_values(['site_name', 'date'])
    df = df.drop(columns=['Start of Interval (UTC+12:00)', 'End of Interval (UTC+12:00)'])
    df = df.rename(columns={'site_name': 'well_name'})

    rl_data = metadata[
        ['well_name', 'rl_elevation', 'well_depth_elevation_NZVD', 'well_depth', 'diff_moturiki_nzdv2016']]

    rl_key, rl_key1 = process_reference_levels(rl_data)
    ts_wl = process_ts_wl(df, rl_key, rl_key1)
    assign_flags_based_on_null_values(ts_wl, 'depth_to_water', 'dtw_flag', 1, 0)
    # Assign 'water_elev_flag' based on 'gw_elevation'
    assign_flags_based_on_null_values(ts_wl, 'gw_elevation', 'water_elev_flag', 1, 0)
    ts_wl = ts_wl.loc[:,
            ['well_name', 'date', 'depth_to_water', 'gw_elevation', 'dtw_flag', 'water_elev_flag', 'data_source',
             'elevation_datum', 'other']]

    # create static wl data
    st_wl = metadata.loc[:, ['well_name', 'depth_to_water_static']]
    st_wl = process_st_wl(st_wl, rl_key)
    assign_flags_based_on_null_values(st_wl, 'depth_to_water', 'dtw_flag', 2, 0)
    # Assign 'water_elev_flag' based on 'gw_elevation'
    assign_flags_based_on_null_values(st_wl, 'gw_elevation', 'water_elev_flag', 2, 0)
    st_wl = st_wl.loc[:,
            ['well_name', 'date', 'depth_to_water', 'gw_elevation', 'dtw_flag', 'water_elev_flag', 'data_source',
             'elevation_datum', 'other']]

    # merge ts and static wl data
    wl_output = pd.concat([ts_wl, st_wl[~st_wl['well_name'].isin(ts_wl['well_name'])]])
    wl_output.dropna(subset=['gw_elevation'], inplace=True)

    return wl_output


def output(local_paths, meta_data_requirements, recalc=False):  #
    """This function pulls all the data and metadata together and outputs it to a hdf5 file
    :return: dataframe"""
    water_data_store_path = local_paths['save_path']
    store_key_water_data = local_paths['wl_store_key']
    store_key_metadata = local_paths['bop_metadata_store_key']

    # Check if data needs to be recalculated or if the HDF files don't exist
    if not recalc and water_data_store_path.exists():
        combined_water_data = pd.read_hdf(water_data_store_path, store_key_water_data, )
        combined_metadata = pd.read_hdf(water_data_store_path, store_key_metadata)

    else:
        needed_gw_columns_type = {'well_name': "str", 'depth_to_water': "float", 'gw_elevation': "float",
                                  'dtw_flag': "int",
                                  'water_elev_flag': 'int', 'data_source': 'str', 'elevation_datum': "str",
                                  'other': "str"}

        bop_metadata = _get_metadata(local_paths=local_paths, file_name='Bore data for Komanawa.xlsx')
        bop_metadata = bop_metadata.drop(
            columns=['WMA', 'SiteName_Address', 'AquariusID', 'NERMN_Code', 'LAWA_ID', 'Groundwater_Zone',
                     'Current', 'Telemetred', 'Bore_use', 'Logger', 'Temp', 'Casing Dia', 'Unnamed: 25'])
        bop_metadata = bop_metadata.rename(
            columns={'Bore_number': 'well_name', 'Aquifer': 'aquifer_type', 'HGU': 'hgu', 'HSU': 'hsu',
                     'Easting': 'nztm_x', 'Northing': 'nztm_y', 'Monitoring_Frequency': 'monitoring_freq',
                     'Monitoring_Type': 'monitoring_type', 'Comment': 'comment',
                     'Bore_depth_(m)': 'well_depth',
                     'Static_WL': 'depth_to_water_static', 'Casing_depth': 'casing_depth',
                     'RL_collar': 'rl_elevation'})

        extra_bop_metadata_path = _get_metadata(local_paths=local_paths,
                                                file_name='Static water level for Komanawa.xlsx')

        extra_bop_metadata_path = extra_bop_metadata_path.drop(
            columns=['Bore Status', 'Site Address', 'Bore Use', 'Bore Type', 'Aquarius Site #',
                     'Screen Type',
                     'Geothermal Field', 'Allocation Zone', 'Water Management Area',
                     'Bore Temperature (Celsius)', 'Casing Diameter mm ', 'Screen Diameter mm ',
                     'Water Level Before \nPumping (mRL_NZVD)'])

        extra_bop_metadata_path = extra_bop_metadata_path.rename(
            columns={'Record ID': 'well_name', 'NZTM Easting': 'nztm_x', 'NZTM Northing': 'nztm_y',
                     'Data Quality': 'qa_comment', 'Data Source': 'data_source',
                     'Hydrogeological Unit': 'hgu',
                     'Water Level Before \nPumping (m)': 'depth_to_water_static',
                     'Bore Depth m ': 'well_depth', 'Bore Depth mRL_NZVD': 'well_depth_elevation_NZVD',
                     'Casing Depth m ': 'casing_depth', 'Screen Set from m ': 'top_topscreen',
                     'Screen Set to m ': 'bottom_bottomscreen',
                     'Reduced Level of measuring point m ': 'rl_elevation',
                     'Geological Unit Screened': 'hgu_screened',
                     'Bore is Flowing Artesian ': 'temp_artesian',
                     'DEM_2011_NZVD2016': 'diff_moturiki_nzdv2016'
                     })

        rl_bop_metadata = _get_metadata(local_paths=local_paths, file_name='NERMN Bore Elevations.xlsx')
        rl_bop_metadata = rl_bop_metadata.drop(columns=['WMA', 'SiteName_Address', 'AquariusID', 'Temp', 'BM measure',
                                                        'Groundelevation_Moturiki', 'RL_collar_Moturiki',
                                                        'Monitoring_Type',
                                                        'Unnamed: 16', 'Unnamed: 17', 'Unnamed: 18', 'Unnamed: 19',
                                                        'Unnamed: 20',
                                                        'Groundelevation_NZVD2016', 'RL_collar_ NZVD2016'])

        rl_bop_metadata = rl_bop_metadata.rename(
            columns={'Bore_number': 'well_name', 'Easting': 'nztm_x', 'Northing': 'nztm_y',
                     'Bore_depth_m ': 'well_depth',
                     'Casing_depth': 'casing_depth', 'Bore_depth_(m)': 'well_depth',
                     'Static_WL': 'depth_to_water_static'})

        ts_metadata = _get_metadata(local_paths=local_paths, file_name='Groundwater Level Site List.xlsx', skiprows=1)
        ts_metadata = ts_metadata.drop(columns=['Location', 'Data Set Id', 'Location Folder', 'Value', 'Status'])
        ts_metadata = ts_metadata.rename(columns={'Start of Record': 'start_date', 'End of Record': 'end_date'})

        combined_metadata = pd.concat([bop_metadata, extra_bop_metadata_path, rl_bop_metadata, ts_metadata],
                                      ignore_index=True)
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

        combined_water_data = _get_wl_bop_data(local_paths=local_paths,
                                               folder_path=local_paths['local_path'] / 'EDS-686541',
                                               metadata=combined_metadata)

        combined_water_data['date'] = pd.to_datetime(combined_water_data['date']).dt.date
        combined_water_data['date'] = pd.to_datetime(combined_water_data['date'])
        combined_water_data = aggregate_water_data(combined_water_data)
        combined_water_data = combined_water_data.sort_values(by=['depth_to_water', "well_name"],
                                                              ascending=[True, True])

        stats = _get_summary_stats(combined_water_data)
        stats = stats.set_index('well_name')
        combined_metadata = combined_metadata.set_index('well_name')
        combined_metadata = combined_metadata.combine_first(stats)
        combined_metadata = combined_metadata.reset_index()

        combined_metadata = merge_rows_if_possible(combined_metadata, on='well_name', precision=precisions,
                                                   skip_cols=skip_cols, actions=aggregation_functions)
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

        renew_hdf5_store(new_data=combined_water_data, old_path=local_paths['save_path'],
                         store_key=local_paths['wl_store_key'])
        renew_hdf5_store(new_data=combined_metadata, old_path=local_paths['save_path'],
                         store_key=local_paths['bop_metadata_store_key'])
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
        'thethys_local_save_path': local_base_path.joinpath("gwl_bop", "cleaned_data", "tethys_gw_data.hdf"),
        'local_path': local_path_mapping
    }

    # Store keys are hardcoded as they are specific to this setup
    local_paths['wl_store_key'] = 'bop_gwl_data'
    local_paths['bop_metadata_store_key'] = 'bop_metadata'
    local_paths['save_path'] = groundwater_data.joinpath('gwl_bop', 'cleaned_data', 'combined_bop_data.hdf')

    return local_paths


def get_bop_data(recalc=False, redownload=False):
    local_paths = _get_folder_and_local_paths(source_dir=groundwater_data.joinpath('gwl_bop'),
                                              local_dir=unbacked_dir.joinpath('bop_working/'), redownload=redownload)
    meta_data_requirements = needed_cols_and_types("BOPRC")
    return output(local_paths, meta_data_requirements, recalc=recalc)


########################################################################################################################


save_path = groundwater_data.joinpath('gwl_bop', 'cleaned_data', 'combined_bop_data.hdf')
wl_store_key = 'bop_gwl_data'
gisborne_metadata_store_key = 'bop_metadata'

if __name__ == '__main__':
    data = get_bop_data(recalc=False, redownload=False)
