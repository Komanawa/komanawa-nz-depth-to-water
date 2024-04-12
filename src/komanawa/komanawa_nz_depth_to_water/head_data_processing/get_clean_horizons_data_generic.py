"""
created Patrick Durney and Evelyn Charlesworth
on: 16/2/2024
"""

""" This script cleans and processes the horizons data"""

import os

import numpy as np
import pandas as pd
import pyproj

import komanawa.komanawa_nz_depth_to_water.head_data_processing.merge_rows as merge_rows
from komanawa.komanawa_nz_depth_to_water.head_data_processing.data_processing_functions import \
    (find_overlapping_files, copy_with_prompt, \
     _get_summary_stats, append_to_other, needed_cols_and_types, data_checks, \
     metadata_checks, renew_hdf5_store, get_hdf5_store_keys, pull_tethys_data_store, assign_flags_based_on_null_values,
     aggregate_water_data )
from komanawa.komanawa_nz_depth_to_water.project_base import groundwater_data, unbacked_dir, project_dir


# keynote not gw_elevation, all depth_to_water -confirmed with horizons

def _get_horizons_tethys_data(local_paths, meta_data_requirements):
    """" This function reads in the horizons data from Tethys
            dtw_flag = 1= logger, 2= manual, 3= static_oneoff, 4= calculated frm gw_elevation, 5= aquifer test, 6= other
    water_ele_flag = 1= logger, 2= manual, 3= static_oneoff, 4= aquifer test, 5= other
    """

    data_keys = get_hdf5_store_keys(unbacked_dir.joinpath('tetheys_2024_all', 'tethys_processed.hdf'))
    meta_keys = get_hdf5_store_keys(unbacked_dir.joinpath('tetheys_2024_all', 'tethys_meta_processed.hdf'))

    needed_gw_columns = ['well_name', 'date', 'depth_to_water', 'gw_elevation', 'dtw_flag', 'water_elev_flag',
                         'data_source', 'elevation_datum', 'other']

    needed_gw_columns_type = {'well_name': "str", 'depth_to_water': "float", 'gw_elevation': "float",
                              'dtw_flag': "Int64",
                              'water_elev_flag': 'Int64',
                              'data_source': 'str', 'elevation_datum': "str", 'other': "str"}

    tethys_data = pull_tethys_data_store(unbacked_dir.joinpath('tetheys_2024_all', 'tethys_processed.hdf'), data_keys,
                                         council="Horizons")
    tethys_metadata = pull_tethys_data_store(unbacked_dir.joinpath('tetheys_2024_all', 'tethys_meta_processed.hdf'),
                                             meta_keys, council="Horizons")
    # keynote, there is no way this is wl elevtion, -163 m below sea level!??! Assuming dtw
    tethys_metadata_wl_24h = tethys_metadata['/Horizons Regional Council_water_level_24H_metadata'].copy()
    tethys_metadata_wl_spot = tethys_metadata['/Horizons Regional Council_water_level_None_metadata'].copy()

    tethys_data_wl_24h = tethys_data['/Horizons Regional Council_water_level_24H'].copy()
    tethys_data_wl_spot = tethys_data['/Horizons Regional Council_water_level_None'].copy()

    tethys_metadata_wl_24h = pd.merge(tethys_metadata_wl_24h,
                                      (tethys_data_wl_24h.drop_duplicates(subset=['tethys_station_id'])),
                                      on='tethys_station_id', how='outer')

    tethys_metadata_wl_spot = pd.merge(tethys_metadata_wl_spot,
                                       (tethys_data_wl_spot.drop_duplicates(subset=['tethys_station_id'])),
                                       on='tethys_station_id', how='outer')

    tethys_metadata_processed = pd.concat([tethys_metadata_wl_24h, tethys_metadata_wl_spot],
                                          ignore_index=True).drop_duplicates(
        subset=['tethys_station_id'])
    ##########
    # process wl_data
    tethys_data_wl_24h['depth_to_water'] = tethys_data_wl_24h['water_level']
    tethys_data_wl_spot['depth_to_water'] = tethys_data_wl_spot['water_level']

    assign_flags_based_on_null_values(tethys_data_wl_24h, 'depth_to_water', 'dtw_flag', 1, 0)
    assign_flags_based_on_null_values(tethys_data_wl_24h, 'gw_elevation', 'water_elev_flag', 1, 0)

    assign_flags_based_on_null_values(tethys_data_wl_spot, 'depth_to_water', 'dtw_flag', 2, 0)
    assign_flags_based_on_null_values(tethys_data_wl_spot, 'gw_elevation', 'water_elev_flag', 2, 0)

    tethys_water_level = pd.concat([tethys_data_wl_24h, tethys_data_wl_spot], ignore_index=True)
    tethys_water_level = tethys_water_level.rename(
        columns={'site_name': 'well_name', 'altitude': 'tethys_elevation'})
    tethys_water_level['data_source'] = "tethys"

    for column in needed_gw_columns:
        if column not in tethys_water_level.columns:
            # Add the missing column and initialize with NaNs or another suitable default value
            tethys_water_level[column] = np.nan

    # Ensure the columns are in the same order as needed_gw_columns
    tethys_water_level = tethys_water_level[needed_gw_columns]
    tethys_water_level['elevation_datum'] = 'NZVD2016'

    tethys_metadata_processed = tethys_metadata_processed.rename(
        columns={"site_name_y": "well_name", "altitude_x": "tethys_elevation", 'from_date': 'start_date',
                 'to_date': 'end_date', 'bore_depth': 'well_depth', 'bore_bottom_of_screen': 'bottom_bottomscreen',
                 'bore_top_of_screen': 'top_topscreen', 'num_samp': 'reading_count'})

    tethys_metadata_processed = tethys_metadata_processed[['well_name', 'tethys_elevation', 'start_date', 'end_date',
                                                           'well_depth', 'reading_count', 'bottom_bottomscreen',
                                                           'top_topscreen']]

    for col in meta_data_requirements['needed_columns']:
        if col not in tethys_metadata_processed.columns:
            tethys_metadata_processed[col] = meta_data_requirements['default_values'].get(col)

    for col, dtype in meta_data_requirements['col_types'].items():
        tethys_metadata_processed[col] = tethys_metadata_processed[col].astype(dtype)

    tethys_metadata_processed['start_date'] = pd.to_datetime(tethys_metadata_processed['start_date'])
    tethys_metadata_processed['end_date'] = pd.to_datetime(tethys_metadata_processed['end_date'])

    for column in needed_gw_columns:
        if column not in tethys_water_level.columns:
            # Add the missing column and initialize with NaNs or another suitable default value
            tethys_water_level[column] = np.nan

    for column, dtype in needed_gw_columns_type.items():
        tethys_water_level[column] = tethys_water_level[column].astype(dtype)

    for col in meta_data_requirements['needed_columns']:
        if col not in tethys_metadata_processed.columns:
            tethys_metadata_processed[col] = meta_data_requirements['default_values'].get(col)

    for col, dtype in meta_data_requirements['col_types'].items():
        tethys_metadata_processed[col] = tethys_metadata_processed[col].astype(dtype)

    return {'tethys_water_level': tethys_water_level,
            'tethys_metadata_combined': tethys_metadata_processed}


def _get_manual_horizons_gwl_data(local_paths, meta_data_requirements, recalc=False):
    """ This function reads in the gw data sent to us by Horizons
    :return: dataframe"""

    # reading in the data, using a recalc method
    save_path = unbacked_dir.joinpath('horizons_working', 'gwl_horizons', 'cleaned_data',
                                      'clean_manual_horizons_gwl_data.hdf')
    store_key = 'clean_manual_horizons_gwl_data'
    if save_path.exists() and not recalc:
        combined_manual_horizons_gwl_data = pd.read_hdf(save_path, store_key)
    else:
        folder_path = local_paths['manual_horizons_gwl_data']
        lists_dfs = []
        for file in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file)
            rows_to_skip = [1, 2]
            raw_df = pd.read_csv(file_path, skiprows=rows_to_skip)
            # melting the df
            melted_df = pd.melt(raw_df, id_vars=['Unnamed: 0'], var_name='well_name', value_name='gwl_data')
            lists_dfs.append(melted_df)
        combined_manual_horizons_gwl_data = pd.concat(lists_dfs, ignore_index=True)
        # renaming the columns
        new_names = {'Unnamed: 0': 'date'}
        combined_manual_horizons_gwl_data.rename(columns=new_names, inplace=True)
        # reading in the date correctly
        combined_manual_horizons_gwl_data['date'] = pd.to_datetime(combined_manual_horizons_gwl_data['date'],
                                                                   dayfirst=True,
                                                                   errors='coerce')

        combined_manual_horizons_gwl_data = combined_manual_horizons_gwl_data.dropna(subset=['gwl_data'])
        combined_manual_horizons_gwl_data['date'] = pd.to_datetime(combined_manual_horizons_gwl_data['date']).dt.date
        combined_manual_horizons_gwl_data = combined_manual_horizons_gwl_data.groupby(
            ['well_name', 'date']).mean().reset_index()

        # handling datatypes
        combined_manual_horizons_gwl_data = combined_manual_horizons_gwl_data.astype(
            {'well_name': 'str', 'gwl_data': 'float'})

        # turning the water_level into m from mm
        combined_manual_horizons_gwl_data['gwl_data'] = combined_manual_horizons_gwl_data['gwl_data'] / 1000

        # dropping any nans
        combined_manual_horizons_gwl_data.dropna(inplace=True)

    # saving to save path
    combined_manual_horizons_gwl_data.to_hdf(save_path, store_key)

    return combined_manual_horizons_gwl_data


def _get_manual_horizons_metadata(local_paths, meta_data_requirements):
    """This function reads in the metadata for the manual horizons data
    :return: dataframe"""

    manual_horizons_metadata = pd.read_csv(
        local_paths['manual_horizons_metadata'], encoding='latin1')
    # renaming the columns
    new_names = {'BoreID': 'well_name', 'HRCTMEasting': 'nztm_x', 'HRCTMNorthing': 'nztm_y', 'Status': 'status'}
    manual_horizons_metadata.rename(columns=new_names, inplace=True)

    # dropping unnecessary columns
    drop_columns = ['HRCLat', 'HRCLong', 'Easting', 'Northing', 'HRCSiteGeometry']
    manual_horizons_metadata.drop(columns=drop_columns, inplace=True)
    manual_horizons_metadata['well_name'].astype('Int64')  # Convert to int where not NaN

    manual_horizons_metadata = manual_horizons_metadata.astype(
        {'nztm_x': 'float', 'nztm_y': 'float', 'status': 'str'})
    manual_horizons_metadata['well_name'] = np.where(
        pd.notnull(manual_horizons_metadata['well_name']),  # Condition: 'depth_to_water' is not NaN
        manual_horizons_metadata['well_name'],  # Value to assign if condition is True
        manual_horizons_metadata['SiteName']  # Value to assign if condition is False
    )

    for col in meta_data_requirements['needed_columns']:
        if col not in manual_horizons_metadata.columns:
            manual_horizons_metadata[col] = meta_data_requirements['default_values'].get(col)

    for col, dtype in meta_data_requirements['col_types'].items():
        manual_horizons_metadata[col] = manual_horizons_metadata[col].astype(dtype)

    return manual_horizons_metadata


def _get_extra_horizons_metadata(local_paths, meta_data_requirements):
    """This functions reads and tidies some of the extra metadata provided by Horizons - e.g.
    hydrogeological parameters, casing etc
    :return: dataframe"""
    nzmg = pyproj.Proj('epsg:27200')
    # Define the NZTM projection (EPSG:2193)
    nztm = pyproj.Proj('epsg:2193')

    fill_data = pd.read_excel(local_paths['extra_manual_horizons_metadata'])

    # renaming columns
    new_names = {'station': 'well_name', 'from_': 'from_depth', 'to_': 'to_depth', 'descr': 'description'}
    fill_data.rename(columns=new_names, inplace=True)
    grouped = fill_data.groupby('well_name')
    # Find the index of the max 'to_depth' for each group
    idx = grouped['to_depth'].idxmax()
    # Step 3: Filter the original DataFrame to keep only the rows with the max 'to_depth' for each 'well_name'
    fill_data = fill_data.loc[idx]

    casing_data = pd.read_excel(
        local_paths['local_path'] / '20230512_Future Coasts Aotearoa Endeavour' / 'casing_tb.xlsx')
    # renaming columns
    new_names1 = {'station': 'well_name', 'from_': 'from_depth', 'to_': 'to_depth', 'diam_': 'diameter'}
    casing_data.rename(columns=new_names1, inplace=True)
    grouped = casing_data.groupby('well_name')
    # Find the index of the max 'to_depth' for each group
    idx = grouped['to_depth'].idxmax()
    # Step 3: Filter the original DataFrame to keep only the rows with the max 'to_depth' for each 'well_name'
    casing_data = casing_data.loc[idx]

    # hydrogeo_data = pd.read_excel(local_paths['local_path']/'20230512_Future Coasts Aotearoa Endeavour'/'Hydrogeological_parameters_tb.xlsx')
    # new_names2 = {'station': 'well_name'}
    # hydrogeo_data.rename(columns=new_names2, inplace=True)

    gw_metadata = pd.read_csv(
        (local_paths['local_path'] / '20230512_Future Coasts Aotearoa Endeavour' / '20230414_PID99962_GW_Metadata.csv'),
        encoding='latin1')
    gw_metadata = gw_metadata.rename(columns={"Easting": "nztm_x", "Northing": "nztm_y"})
    gw_metadata['well_name'] = np.where(pd.notnull(gw_metadata['BoreID']), gw_metadata['BoreID'],
                                        gw_metadata['SiteName'])
    gw_metadata = gw_metadata[['well_name', 'nztm_x', 'nztm_y']]
    gw_metadata['nztm_y'], gw_metadata['nztm_x'] = (
        pyproj.transform(nzmg, nztm, gw_metadata['nztm_x'], gw_metadata['nztm_y']))
    gw_metadata = gw_metadata.round({'nztm_x': 0, 'nztm_y': 0})

    static_water_level_metadata = pd.read_csv(
        (local_paths['local_path'] / '20230512_Future Coasts Aotearoa Endeavour' / 'LandView_Lithology_Data_tb.csv'),
        encoding='latin1')
    new_names3 = {'HOLEID': 'well_name', 'L_FROM': 'top_topscreen',
                  'L_TO': 'bottom_bottomscreen', 'DESCR': 'lithology_description'}
    static_water_level_metadata.rename(columns=new_names3, inplace=True)
    # convert from mapgrid to nztm
    nzmg = pyproj.Proj('epsg:27200')
    # Define the NZTM projection (EPSG:2193)
    nztm = pyproj.Proj('epsg:2193')
    static_water_level_metadata['nztm_y'], static_water_level_metadata['nztm_x'] = (
        pyproj.transform(nzmg, nztm, static_water_level_metadata['EAST'], static_water_level_metadata['NORTH']))
    # dropping unnecessary columns
    drop_columns = ['SURNAME', 'EAST', "NORTH"]
    static_water_level_metadata.drop(columns=drop_columns, inplace=True)
    grouped = static_water_level_metadata.groupby('well_name')
    # Find the index of the max 'to_depth' for each group
    idx = grouped['bottom_bottomscreen'].idxmax()
    idm = grouped['top_topscreen'].idxmin()
    # Step 3: Filter the original DataFrame to keep only the rows with the max 'to_depth' for each 'well_name'
    bot_screen = static_water_level_metadata.loc[idx]
    top_screen = static_water_level_metadata.loc[idm]
    top_screen = top_screen[['well_name', 'top_topscreen']]
    bot_screen = bot_screen.drop(columns=['top_topscreen'])
    static_water_level_metadata = pd.merge(top_screen, bot_screen, on='well_name', how='outer')

    def round_and_convert(value):
        # Check if the value is an instance of float
        if isinstance(value, float):
            # Round the float to remove the decimal part and convert to int for cleaner appearance
            value = int(round(value, 0))
        # Convert the value to string
        return str(value)

    # combine the data
    extra_metadata = pd.merge(fill_data, casing_data, on='well_name', how='outer')
    extra_metadata = pd.merge(extra_metadata, static_water_level_metadata, on='well_name', how='outer')
    extra_metadata['well_name'] = extra_metadata['well_name'].astype(str)
    extra_metadata = pd.concat([extra_metadata, gw_metadata], ignore_index=True)
    extra_metadata['well_depth'] = extra_metadata[['to_depth_x', 'to_depth_y', 'bottom_bottomscreen']].max(axis=1)
    # Apply the function to each entry in the 'well_name' column
    extra_metadata['well_name'] = extra_metadata['well_name'].apply(round_and_convert)
    extra_metadata = extra_metadata.sort_values(by='well_name')
    duplicates = extra_metadata[extra_metadata.duplicated(subset='well_name', keep=False)]

    #  handling datatypes
    extra_metadata = extra_metadata.astype(
        {'well_name': 'str', 'nztm_x': 'float', 'nztm_y': 'float', 'top_topscreen': 'float',
         'bottom_bottomscreen': 'float', 'well_depth': 'float',
         'diameter': 'float', 'description': 'str', 'lithology_description': 'str'})
    for col in meta_data_requirements['needed_columns']:
        if col not in extra_metadata.columns:
            extra_metadata[col] = meta_data_requirements['default_values'].get(col)

    for col, dtype in meta_data_requirements['col_types'].items():
        extra_metadata[col] = extra_metadata[col].astype(dtype)
    if 'other' not in extra_metadata.columns:
        extra_metadata['other'] = ''

    extra_metadata = append_to_other(df=extra_metadata, needed_columns=meta_data_requirements["needed_columns"])

    extra_metadata.drop(columns=[col for col in extra_metadata.columns if
                                 col not in meta_data_requirements["needed_columns"] and col != 'other'],
                        inplace=True)

    return extra_metadata


def _get_horizons_static_gwl(local_paths):
    """This function reads in the static water level provided by Horizons
    :return: dataframe
     This function reads in the horizons data from Tethys
                dtw_flag = 1= logger, 2= manual, 3= static_oneoff, 4= calculated frm gw_elevation, 5= aquifer test, 6= other
        water_ele_flag = 1= logger, 2= manual, 3= static_oneoff, 4= aquifer test, 5= other
     """

    needed_gw_columns = ['well_name', 'date', 'depth_to_water', 'gw_elevation', 'dtw_flag', 'water_elev_flag',
                         'data_source', 'elevation_datum', 'other']

    needed_gw_columns_type = {'well_name': "str", 'depth_to_water': "float", 'gw_elevation': "float",
                              'dtw_flag': "Int64",
                              'water_elev_flag': 'Int64',
                              'data_source': 'str', 'elevation_datum': "str", 'other': "str"}
    needed_gw_columns = ['well_name', 'date', 'depth_to_water', 'gw_elevation', 'dtw_flag', 'water_elev_flag',
                         'data_source', 'elevation_datum', 'other']

    needed_gw_columns_type = {'well_name': "str", 'depth_to_water': "float", 'gw_elevation': "float",
                              'dtw_flag': "Int64",
                              'water_elev_flag': 'Int64',
                              'data_source': 'str', 'elevation_datum': "str", 'other': "str"}

    static_gwl_1 = pd.read_csv(
        local_paths['local_path'] / '20230512_Future Coasts Aotearoa Endeavour' / 'LandView_Borehole_Data_tb.csv')

    # renaming columns
    new_names = {'BoreID': 'well_name', 'Easting': 'nztm_x', 'Northing': 'nztm_y', 'Drill Date': 'date',
                 'Depth': 'well_depth', 'Elevation': 'elevation', 'SWL': 'depth_to_water', 'Aquifer': 'aquifer'}
    static_gwl_1.rename(columns=new_names, inplace=True)
    static_gwl_1.drop(columns=['Link'], inplace=True)
    # handling the date
    static_gwl_1['date'] = pd.to_datetime(static_gwl_1['date'], format='%d/%m/%Y %H:%M')

    static_gwl_2 = pd.read_excel(
        local_paths['local_path'] / '20230512_Future Coasts Aotearoa Endeavour' / 'initial_swl_tb.xlsx')
    # renaming columns
    new_names1 = {'station': 'well_name', 'depth_to_wl': 'depth_to_water'}
    static_gwl_2.rename(columns=new_names1, inplace=True)
    static_gwl_2.drop(columns=['SWL_serial_number'], inplace=True)
    # handling date
    static_gwl_2['date'] = pd.to_datetime(static_gwl_2['date'], format='%d/%m/%Y')

    # combine the two static gwl dataframes
    static_gwl = pd.concat([static_gwl_1, static_gwl_2], axis=0, ignore_index=True)
    # handling datatypes
    static_gwl = static_gwl.astype({'well_name': 'str', 'nztm_x': 'float', 'nztm_y': 'float', 'well_depth': 'float',
                                    'elevation': 'float', 'depth_to_water': 'float', 'aquifer': 'str'})
    # need to transform from nz map grid to nztm
    nzmg = pyproj.Proj('epsg:27200')
    # Define the NZTM projection (EPSG:2193)
    nztm = pyproj.Proj('epsg:2193')
    static_gwl['nztm_y'], static_gwl['nztm_x'] = (
        pyproj.transform(nzmg, nztm, static_gwl['nztm_x'], static_gwl['nztm_y']))
    static_gwl = static_gwl.round({'nztm_x': 0, 'nztm_y': 0})


    # depth to water by the very name should be positive
    static_gwl['depth_to_water'] = static_gwl['depth_to_water'] * -1

    for column in needed_gw_columns:
        if column not in static_gwl.columns:
            # Add the missing column and initialize with NaNs or another suitable default value
            static_gwl[column] = np.nan

    for column, dtype in needed_gw_columns_type.items():
        static_gwl[column] = static_gwl[column].astype(dtype)

    static_gwl = static_gwl.drop_duplicates(subset=['well_name', 'date'])
    static_gwl = static_gwl.dropna(subset=['depth_to_water'])
    static_gwl['data_source'] = 'HRC'
    static_gwl['elevation_datum'] = 'NZVD2016'
    static_gwl['other'] = ''

    assign_flags_based_on_null_values(static_gwl, 'depth_to_water', 'dtw_flag', 3, 0)
    assign_flags_based_on_null_values(static_gwl, 'gw_elevation', 'water_elev_flag', 3, 0)

    # intherory this is good in practice bad for hrc
    # static_gwl = append_to_other(df=static_gwl, needed_columns=needed_gw_columns)
    # static_gwl = static_gwl[needed_gw_columns]

    return static_gwl


def output(local_paths, meta_data_requirements, recalc=False):
    """This function combines the two sets of metadata and cleans it
    :return: dataframe"""

    water_data_store_path = local_paths['save_path']
    store_key_water_data = local_paths['wl_store_key']
    store_key_metadata = local_paths['horizons_metadata_store_key']

    # Check if data needs to be recalculated or if the HDF files don't exist
    if not recalc and water_data_store_path.exists():
        combined_water_data = pd.read_hdf(water_data_store_path, store_key_water_data)
        combined_metadata = pd.read_hdf(water_data_store_path, store_key_metadata)

    else:
        needed_gw_columns = ['well_name', 'date', 'depth_to_water', 'gw_elevation', 'dtw_flag', 'water_elev_flag',
                             'data_source', 'elevation_datum', 'other']

        needed_gw_columns_type = {'well_name': "str", 'depth_to_water': "float", 'gw_elevation': "float",
                                  'dtw_flag': "Int64",
                                  'water_elev_flag': 'Int64',
                                  'data_source': 'str', 'elevation_datum': "str", 'other': "str"}

        tethys_data = _get_horizons_tethys_data(local_paths, meta_data_requirements)
        tethy_gw_data = tethys_data['tethys_water_level']
        tethy_gw_data['well_name'] = tethy_gw_data["well_name"].astype(str)
        tethy_gw_data['date'] = pd.to_datetime(tethy_gw_data['date'])
        tethy_gw_data['depth_to_water'] = tethy_gw_data['depth_to_water'] * -1

        tetheys_metadata = tethys_data['tethys_metadata_combined']
        tetheys_metadata['well_name'] = tetheys_metadata["well_name"].astype(str)

        hrc_metadata = _get_manual_horizons_metadata(local_paths=local_paths,
                                                     meta_data_requirements=meta_data_requirements)
        hrc_metadata = hrc_metadata.sort_values(by='well_name')

        hrc_extra_metadata = _get_extra_horizons_metadata(local_paths=local_paths,
                                                          meta_data_requirements=meta_data_requirements)

        hrc_gw_data = _get_horizons_static_gwl(local_paths=local_paths)
        hrc_gw_data_metadata = hrc_gw_data[['well_name', 'nztm_x', 'nztm_y', 'well_depth', 'elevation']]
        hrc_gw_data_metadata = hrc_gw_data_metadata.drop_duplicates(subset=['well_name'])

        hrc_gw_data_manual_data = _get_manual_horizons_gwl_data(local_paths=local_paths,
                                                                meta_data_requirements=meta_data_requirements,
                                                                recalc=False)
        hrc_gw_data_manual_data['depth_to_water'] = hrc_gw_data_manual_data['gwl_data'] * -1

        for column in needed_gw_columns:
            if column not in tethy_gw_data.columns:
                # Add the missing column and initialize with NaNs or another suitable default value
                tethy_gw_data[column] = np.nan

        for column, dtype in needed_gw_columns_type.items():
            tethy_gw_data[column] = tethy_gw_data[column].astype(dtype)

        for column, dtype in needed_gw_columns_type.items():
            hrc_gw_data[column] = hrc_gw_data[column].astype(dtype)

        combined_water_data = pd.concat([tethy_gw_data, hrc_gw_data], ignore_index=True)
        combined_water_data['data_source'] = np.where(combined_water_data['data_source'].isna(), 'HRC',
                                                      combined_water_data['data_source'])

        # Ensure 'date' is in datetime format
        combined_water_data['date'] = pd.to_datetime(combined_water_data['date']).dt.date
        combined_water_data['date'] = pd.to_datetime(combined_water_data['date'])

        combined_water_data = aggregate_water_data(combined_water_data)

        for column, dtype in needed_gw_columns_type.items():
            combined_water_data[column] = combined_water_data[column].astype(dtype)

        # combining the metadata sets
        combined_metadata = pd.concat([tetheys_metadata, hrc_metadata, hrc_extra_metadata, hrc_gw_data_metadata],
                                      ignore_index=True).sort_values(
            by='well_name')
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

        combined_metadata = merge_rows.merge_rows_if_possible(combined_metadata, on='well_name', precision=precisions,
                                                              skip_cols=skip_cols, actions=aggregation_functions)
        combined_metadata = combined_metadata.sort_values(by='well_name')
        combined_metadata = combined_metadata.reset_index(drop=True)
        combined_metadata['rl_elevation'] = combined_metadata['elevation']
        combined_metadata['rl_source'] = np.where(pd.notnull(combined_metadata['rl_elevation']), 'HRC', np.nan)
        combined_metadata['rl_elevation'] = np.where(pd.isnull(combined_metadata['rl_elevation']),
                                                     combined_metadata['tethys_elevation'],
                                                     combined_metadata['rl_elevation'])
        combined_metadata['rl_source'] = np.where(pd.isnull(combined_metadata['rl_source']), 'tethys',
                                                  combined_metadata['rl_source'])

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
        combined_metadata['well_depth'] = combined_metadata['well_depth'].astype('float')

        for col, dtype in meta_data_requirements['col_types'].items():
            if col in combined_metadata.columns:
                # Change the data type of the column to the specified dtype
                combined_metadata[col] = combined_metadata[col].astype(dtype)

        combined_metadata.to_csv(project_dir.joinpath('Data/gwl_data/horizons_metadata_db.csv'))

        for column in needed_gw_columns:
            # Check if the column is of pandas nullable Int64 type
            if pd.api.types.is_integer_dtype(combined_water_data[column]) and combined_water_data[
                column].isnull().any():
                # Convert to float64 if there are NaN values, as NaN cannot be represented in pandas' non-nullable integer types
                combined_water_data[column] = combined_water_data[column].astype('float64')
            elif pd.api.types.is_integer_dtype(combined_water_data[column]):
                # Convert to NumPy's int64 if there are no NaN values and it is a pandas Int64 type
                combined_water_data[column] = combined_water_data[column].astype('int64')

        renew_hdf5_store(new_data=combined_water_data, old_path=local_paths['save_path'],
                         store_key=local_paths['wl_store_key'])
        renew_hdf5_store(new_data=combined_metadata, old_path=local_paths['save_path'],
                         store_key=local_paths['horizons_metadata_store_key'])

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
        # original tethys data not used to to suspected erros
        # 'water_level_data': local_path_mapping.joinpath("tethys_water_level_data"),
        # 'water_depth_data': local_path_mapping.joinpath("tethys_gw_depth_data"),
        # 'water_level_metadata': local_path_mapping.joinpath("water_level_all_stations.csv"),
        # 'water_depth_metadata': local_path_mapping.joinpath("groundwater_depth_all_stations.csv"),
        'manual_horizons_gwl_data': local_path_mapping.joinpath('20230512_Future Coasts Aotearoa Endeavour', "gw_data"),
        'manual_horizons_metadata': local_path_mapping.joinpath('20230512_Future Coasts Aotearoa Endeavour',
                                                                '20230414_PID99962_GW_Metadata.csv'),
        'extra_manual_horizons_metadata': local_path_mapping.joinpath('20230512_Future Coasts Aotearoa Endeavour',
                                                                      'annular_fill_tb.xlsx'),

        'horizons_local_save_path': local_base_path.joinpath("gwl_horizons", "cleaned_data", "horizons_gw_data.hdf"),
        'local_path': local_path_mapping
    }

    # Store keys are hardcoded as they are specific to this setup
    local_paths['tethys_gw_depth_local_store_key'] = 'horizons_depth_data'
    local_paths['tethys_gw_level_local_store_key'] = 'water_level_data'
    local_paths['wl_store_key'] = 'horizons_gwl_data'
    local_paths['horizons_metadata_store_key'] = 'horizons_metadata'
    local_paths['save_path'] = groundwater_data.joinpath('gwl_horizons', 'cleaned_data', 'combined_horizons_data.hdf')

    return local_paths


def get_hrc_data(recalc=False, redownload=False):
    local_paths = _get_folder_and_local_paths(source_dir=groundwater_data.joinpath('gwl_horizons'),
                                              local_dir=unbacked_dir.joinpath('horizons_working/'),
                                              redownload=redownload)
    meta_data_requirements = needed_cols_and_types('HRC')
    return output(local_paths, meta_data_requirements, recalc=recalc)


if __name__ == '__main__':
    data = get_hrc_data(recalc=True)
    pass
