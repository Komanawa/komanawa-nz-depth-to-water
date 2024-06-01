"""
created Evelyn_Charlesworth 
on: 6/07/2023
"""
""" This script cleans and processes the gisborne data"""

import numpy as np
import pandas as pd
import pyproj

from komanawa.nz_depth_to_water.generate_dataset.head_data_processing.data_processing_functions import (find_overlapping_files,
                                                                                                        copy_with_prompt, \
                                                                                                        _get_summary_stats,
                                                                                                        needed_cols_and_types,
                                                                                                        metadata_checks, \
                                                                                                        data_checks,
                                                                                                        get_hdf5_store_keys,
                                                                                                        pull_tethys_data_store,
                                                                                                        append_to_other,
                                                                                                        renew_hdf5_store,
                                                                                                        assign_flags_based_on_null_values,
                                                                                                        aggregate_water_data)
from komanawa.nz_depth_to_water.generate_dataset.head_data_processing.merge_rows import merge_rows_if_possible
from komanawa.nz_depth_to_water.generate_dataset.project_base import groundwater_data, unbacked_dir


########################################################################################################################
def _get_gisborne_tethys_data(local_paths, meta_data_requirements):
    """" This function reads in the gisborne data from Tethys
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
                                         council="Gisborne")
    tethys_gw_metadata = pull_tethys_data_store(unbacked_dir.joinpath('tetheys_2024_all', 'tethys_meta_processed.hdf'),
                                                meta_keys, council="Gisborne")

    tethys_gw_depth_none = tethys_data['/Gisborne District Council_groundwater_depth_None']
    tethys_gw_depth_none = tethys_gw_depth_none.set_index(['tethys_station_id', 'date'])

    tethys_water_level_none = tethys_data['/Gisborne District Council_water_level_None']
    tethys_water_level_none = tethys_water_level_none.set_index(['tethys_station_id', 'date'])

    tethys_data_water_level_24 = tethys_data['/Gisborne District Council_water_level_24H']

    # this section does a safe merge without loss of data or duplication
    unique_df2_mask = ~tethys_water_level_none.index.isin(
        tethys_gw_depth_none.index)

    unique_tethys_water_level_none = tethys_water_level_none[unique_df2_mask]

    tethys_none_data = pd.merge(tethys_gw_depth_none, tethys_water_level_none, on=['tethys_station_id', 'date'],
                                how='outer', suffixes=('', '_df2'))
    # For each column in df1, if there's a corresponding '_df2' column in combined_df, fill NaNs from df1 column with values from '_df2' column
    for col in tethys_gw_depth_none.columns:
        if col + '_df2' in tethys_none_data.columns:
            tethys_none_data[col] = tethys_none_data[col].fillna(tethys_none_data[col + '_df2'])
            tethys_none_data.drop(col + '_df2', axis=1, inplace=True)

    tethys_none_data = tethys_none_data.reset_index()
    tethys_none_data = pd.concat([tethys_none_data, unique_tethys_water_level_none], ignore_index=True)

    tethys_none_data['well_name'] = tethys_none_data['site_name'].str.split(' ').str[-1]

    tethys_none_data = tethys_none_data.drop(columns=['site_name', "alt_name"])
    tethys_none_data['data_source'] = "tethys"
    tethys_none_data['gw_elevation'] = tethys_none_data['water_level']
    tethys_none_data['depth_to_water'] = tethys_none_data['groundwater_depth']
    tethys_none_data = tethys_none_data.drop(columns=['water_level', 'groundwater_depth'])
    for column in needed_gw_columns:
        if column not in tethys_none_data.columns:
            # Add the missing column and initialize with NaNs or another suitable default value
            tethys_none_data[column] = np.nan
    for column, dtype in needed_gw_columns_type.items():
        tethys_none_data[column] = tethys_none_data[column].astype(dtype)

    assign_flags_based_on_null_values(tethys_none_data, 'depth_to_water', 'dtw_flag', 2, 0)
    # Assign 'water_elev_flag' based on 'gw_elevation'
    assign_flags_based_on_null_values(tethys_none_data, 'gw_elevation', 'water_elev_flag', 2, 0)

    tethys_data_water_level_24['well_name'] = tethys_data_water_level_24['site_name'].str.split(' ').str[-1]
    tethys_data_water_level_24 = tethys_data_water_level_24.drop(columns=['site_name', "alt_name"])
    tethys_data_water_level_24['data_source'] = "tethys"
    tethys_data_water_level_24['gw_elevation'] = tethys_data_water_level_24['water_level']
    tethys_data_water_level_24 = tethys_data_water_level_24.drop(columns=['water_level'])

    for column in needed_gw_columns:
        if column not in tethys_data_water_level_24.columns:
            # Add the missing column and initialize with NaNs or another suitable default value
            tethys_data_water_level_24[column] = np.nan
    for column, dtype in needed_gw_columns_type.items():
        tethys_data_water_level_24[column] = tethys_data_water_level_24[column].astype(dtype)

    assign_flags_based_on_null_values(tethys_data_water_level_24, 'depth_to_water', 'dtw_flag', 1, 0)
    # Assign 'water_elev_flag' based on 'gw_elevation'
    assign_flags_based_on_null_values(tethys_data_water_level_24, 'gw_elevation', 'water_elev_flag', 1, 0)

    tethys_groundwater_data = pd.concat([tethys_none_data, tethys_data_water_level_24], ignore_index=True)
    # Extract text within parentheses and store it in a temporary Series
    extracted_names = tethys_groundwater_data['well_name'].str.extract(r'\((.*?)\)')[0]

    # Fill non-matches with original names from 'well_name'
    tethys_groundwater_data['well_name'] = extracted_names.fillna(tethys_groundwater_data['well_name'])
    tethys_groundwater_data_names = tethys_groundwater_data[['well_name', 'tethys_station_id']].drop_duplicates()
    tethys_groundwater_data_names = tethys_groundwater_data_names.rename(
        columns={'well_name': 'data_well_name'})
    tethys_groundwater_data_names.set_index('tethys_station_id', inplace=True)

    tethys_groundwater_data = tethys_groundwater_data.rename(
        columns={'bore_depth': 'well_depth', 'bore_bottom_of_screen': 'bottom_bottomscreen',
                 'bore_top_of_screen': 'top_topscreen',
                 'altitude': 'tethys_elevation'})
    tethys_groundwater_data_metadata = tethys_groundwater_data[
        ['well_name', 'tethys_elevation', 'top_topscreen', 'bottom_bottomscreen']]
    tethys_groundwater_data_metadata = tethys_groundwater_data_metadata.drop_duplicates()
    tethys_groundwater_data = tethys_groundwater_data.drop(
        columns=['tethys_elevation', 'well_depth', 'top_topscreen', 'bottom_bottomscreen']).drop_duplicates()

    tethys_groundwater_data = append_to_other(df=tethys_groundwater_data, needed_columns=needed_gw_columns)
    for column in needed_gw_columns:
        if column not in tethys_groundwater_data.columns:
            # Add the missing column and initialize with NaNs or another suitable default value
            tethys_groundwater_data[column] = np.nan

    for column, dtype in needed_gw_columns_type.items():
        tethys_groundwater_data[column] = tethys_groundwater_data[column].astype(dtype)

    # Ensure the columns are in the same order as needed_gw_columns
    tethys_groundwater_data = tethys_groundwater_data[needed_gw_columns]
    tethys_groundwater_data['elevation_datum'] = 'msl'
    tethys_groundwater_data = tethys_groundwater_data.sort_values(by=['well_name', 'date'],
                                                                  ascending=[True, True])

    tethys_groundwater_data['diff'] = tethys_groundwater_data['depth_to_water'] + tethys_groundwater_data[
        'gw_elevation']

    tethys_groundwater_data_grp = tethys_groundwater_data.groupby(['well_name'])
    mean_diff_per_group = tethys_groundwater_data_grp['diff'].mean()
    tethys_groundwater_data = pd.merge(tethys_groundwater_data, mean_diff_per_group, on='well_name')
    tethys_groundwater_data['depth_to_water'] = np.where(pd.isnull(tethys_groundwater_data['depth_to_water']),
                                                         tethys_groundwater_data['diff_y'] - tethys_groundwater_data[
                                                             'gw_elevation'], tethys_groundwater_data['depth_to_water'])
    tethys_groundwater_data = tethys_groundwater_data.drop(columns=['diff_y', 'diff_x'])

    tethys_gw_metadata = pd.concat([tethys_gw_metadata['/Gisborne District Council_groundwater_depth_None_metadata'],
                                    tethys_gw_metadata['/Gisborne District Council_water_level_None_metadata'],
                                    tethys_gw_metadata['/Gisborne District Council_water_level_24H_metadata']],
                                   ignore_index=True)

    tethys_gw_metadata = tethys_gw_metadata.drop_duplicates()
    tethys_gw_metadata['well_name'] = tethys_gw_metadata['site_name'].str.split(' ').str[-1]
    extracted_names = tethys_gw_metadata['well_name'].str.extract(r'\((.*?)\)')[0]
    # Fill non-matches with original names from 'well_name'
    tethys_gw_metadata['well_name'] = extracted_names.fillna(tethys_gw_metadata['well_name'])
    tethys_gw_metadata.set_index('tethys_station_id', inplace=True)

    tethys_gw_metadata = tethys_gw_metadata.combine_first(tethys_groundwater_data_names)
    tethys_gw_metadata['well_name'] = tethys_gw_metadata['data_well_name']
    tethys_gw_metadata = tethys_gw_metadata.drop_duplicates(subset=['well_name'])
    # merge bore_depth etc with the metadata
    tethys_metadata_combined = pd.merge(tethys_gw_metadata, tethys_groundwater_data_metadata, on='well_name',
                                        how='outer')

    for col in meta_data_requirements['needed_columns']:
        if col not in tethys_metadata_combined.columns:
            tethys_metadata_combined[col] = meta_data_requirements['default_values'].get(col)

    for col, dtype in meta_data_requirements['col_types'].items():
        tethys_metadata_combined[col] = tethys_metadata_combined[col].astype(dtype)

    tethys_metadata_combined = append_to_other(df=tethys_metadata_combined,
                                               needed_columns=meta_data_requirements["needed_columns"])

    lat_long = pyproj.Proj('epsg:4326')
    nztm = pyproj.Proj('epsg:2193')

    tethys_metadata_combined['nztm_y'], tethys_metadata_combined['nztm_x'] = (
        pyproj.transform(lat_long, nztm, tethys_metadata_combined['lat'],
                         tethys_metadata_combined['lon']))
    tethys_metadata_combined = tethys_metadata_combined.round({'nztm_x': 0, 'nztm_y': 0})

    tethys_metadata_combined.drop(columns=[col for col in tethys_metadata_combined.columns if
                                           col not in meta_data_requirements["needed_columns"] and col != 'other'],
                                  inplace=True)

    tethys_metadata_combined['start_date'] = pd.to_datetime(tethys_metadata_combined['start_date'])
    tethys_metadata_combined['end_date'] = pd.to_datetime(tethys_metadata_combined['end_date'])

    return {'tethys_groundwater_data': tethys_groundwater_data,
            'tethys_metadata_combined': tethys_metadata_combined}


########################################################################################################################

def _get_extra_swl_data(local_paths):
    """This reads in the extra gisborne static GWL data
    this is elevation data
    all coordinates are NZTM
    """
    data_path = local_paths['local_path'] / '20231003_Evelyn_Charlesworth_SWL_JK.xlsx'
    extra_swl_data = pd.read_excel(data_path, sheet_name='SWL Data', skiprows=2)
    extra_swl_data = extra_swl_data.rename(
        columns={'BoreID': 'well_name', 'Static Water Level (masl/RL)*': 'gw_elevation', 'Easting': 'nztm_x',
                 'Northing': 'nztm_y'})
    extra_swl_data['Date'] = pd.to_datetime(extra_swl_data['Date'])

    # Combine 'Date' and 'Time' into a single 'datetime' column
    def _combine_date_time(row):
        if pd.notnull(row['Date']):
            return pd.Timestamp.combine(row['Date'], row['Time'])
        else:
            return pd.NaT

    # Use the 'apply' method with the custom function
    extra_swl_data['date'] = extra_swl_data.apply(_combine_date_time, axis=1)
    extra_swl_data = extra_swl_data.drop(columns=['Date', 'Time'])

    return extra_swl_data


def _get_extra_loger_data(local_paths):
    """This reads in the extra gisborne logger data
    this is elevation data
    all coordinates are NZTM
    """
    data_path = local_paths['local_path'] / '20231003_Evelyn_Charlesworth_SWL_JK.xlsx'
    extra_loger_data = pd.read_excel(data_path, sheet_name='Logger Data', skiprows=2)
    extra_loger_data = extra_loger_data.rename(
        columns={'BoreID': 'well_name', 'Static Water Level (masl/RL)*': 'gw_elevation', 'Easting': 'nztm_x',
                 'Northing': 'nztm_y', 'Date': 'date'})

    return extra_loger_data


def _get_poor_quality_data(local_paths):
    """This reads in the extra gisborne data
    # this is elevation data
    # all coordinates are NZTM
    """

    data_path = local_paths['local_path'] / '20231003_Evelyn_Charlesworth_SWL_JK.xlsx'
    poor_quality_data = pd.read_excel(data_path, sheet_name='Poor quality data', skiprows=2)
    poor_quality_data = poor_quality_data.rename(
        columns={'BoreID': 'well_name', 'Static Water Level (masl/RL)*': 'gw_elevation', 'Easting': 'nztm_x',
                 'Northing': 'nztm_y'})
    poor_quality_data['Date'] = pd.to_datetime(poor_quality_data['Date'])

    # Combine 'Date' and 'Time' into a single 'datetime' column
    def _combine_date_time(row):
        if pd.notnull(row['Date']):
            return pd.Timestamp.combine(row['Date'], row['Time'])
        else:
            return pd.NaT

    poor_quality_data['date'] = poor_quality_data.apply(_combine_date_time, axis=1)
    poor_quality_data = poor_quality_data.drop(columns=['Date', 'Time'])

    return poor_quality_data


def _get_standalone_gwl(local_paths):
    """This function reads in the separate logger site from gisborne"""
    # " The data for GPE065 is affected by the aquifer recharge - upspikes (not typically observed in
    # confined aquifers) are due to injection water going into the aquifer and downspikes are due to pumping  "
    # all coordinates are NZTM

    data_path = local_paths['local_path'] / '20231003_Evelyn_Charlesworth_SWL_JK.xlsx'
    standalone_gwl = pd.read_excel(data_path, sheet_name='GPE065', skiprows=2)
    standalone_gwl = standalone_gwl.rename(
        columns={'BoreID': 'well_name', 'Static Water Level (masl/RL)*': 'gw_elevation', 'Easting': 'nztm_x',
                 'Northing': 'nztm_y', 'Date': 'date'})

    return standalone_gwl


def _get_bespoke_data(local_paths):
    """This function reads in the bespoke data from the gisborne data
        dtw_flag = 0 = no data, 1= logger, 2= manual, 3= static_oneoff, 4= calculated frm gw_elevation, 5= aquifer test, 6= other
    water_ele_flag = 1= logger, 2= manual, 3= static_oneoff, 4= aquifer test, 5= other
    :return dataframe, the combined Hawkes Bay dtw and gw elevation data"""

    needed_columns = ['well_name', 'date', 'depth_to_water', 'gw_elevation', 'dtw_flag', 'water_elev_flag',
                      'data_source', 'elevation_datum', 'other']

    extra_swl_data = _get_extra_swl_data(local_paths)
    extra_swl_data['data_source'] = 'GDC'
    assign_flags_based_on_null_values(extra_swl_data, 'depth_to_water', 'dtw_flag', 4, 0)
    # Assign 'water_elev_flag' based on 'gw_elevation'
    assign_flags_based_on_null_values(extra_swl_data, 'gw_elevation', 'water_elev_flag', 2, 0)

    extra_loger_data = _get_extra_loger_data(local_paths)
    extra_loger_data['data_source'] = 'GDC'
    assign_flags_based_on_null_values(extra_loger_data, 'depth_to_water', 'dtw_flag', 4, 0)
    # Assign 'water_elev_flag' based on 'gw_elevation'
    assign_flags_based_on_null_values(extra_loger_data, 'gw_elevation', 'water_elev_flag', 1, 0)

    poor_quality_data = _get_poor_quality_data(local_paths)
    poor_quality_data['data_source'] = 'GDC'
    assign_flags_based_on_null_values(poor_quality_data, 'depth_to_water', 'dtw_flag', 6, 0)
    # Assign 'water_elev_flag' based on 'gw_elevation'
    assign_flags_based_on_null_values(poor_quality_data, 'gw_elevation', 'water_elev_flag', 5, 0)

    standalone_gwl = _get_standalone_gwl(local_paths)
    standalone_gwl['data_source'] = 'GDC'
    standalone_gwl = standalone_gwl[standalone_gwl['well_name'] == 'GPE065']
    assign_flags_based_on_null_values(standalone_gwl, 'depth_to_water', 'dtw_flag', 6, 0)
    # Assign 'water_elev_flag' based on 'gw_elevation'
    assign_flags_based_on_null_values(standalone_gwl, 'gw_elevation', 'water_elev_flag', 5, 0)

    combined_bespoke_data = pd.concat([extra_swl_data, extra_loger_data, poor_quality_data, standalone_gwl],
                                      ignore_index=True)

    # Check for and add any missing columns from needed_columns
    for column in needed_columns:
        if column not in combined_bespoke_data.columns:
            # Add the missing column and initialize with NaNs or another suitable default value
            combined_bespoke_data[column] = np.nan

    # Ensure the columns are in the same order as needed_columns
    combined_bespoke_data = combined_bespoke_data[needed_columns]
    combined_bespoke_data['elevation_datum'] = 'msl'

    return combined_bespoke_data


########################################################################################################################
def _get_extra_gisborne_metadata(local_paths, meta_data_requirements):
    """Reading in the extra gisborne metadata
    all coordinates are NZTM
    """

    metadata_path = local_paths['local_path'] / '20231003_Evelyn_Charlesworth_SWL_JK.xlsx'
    extra_metadata = pd.read_excel(metadata_path, sheet_name='Bore Data', skiprows=2)
    extra_metadata = extra_metadata.rename(
        columns={'BoreID': 'well_name', 'Easting': 'nztm_x', 'Northing': 'nztm_y', "BoreDepth (m)": "well_depth",
                 'ScreenDepthToTop (m)': 'top_topscreen', "TopOfCollar(m)": 'dist_mp_to_ground_level'})
    extra_metadata['bottom_bottomscreen'] = extra_metadata['top_topscreen'] + extra_metadata['ScreenLength (m)']

    for col in meta_data_requirements['needed_columns']:
        if col not in extra_metadata.columns:
            extra_metadata[col] = meta_data_requirements['default_values'].get(col)

    for col, dtype in meta_data_requirements['col_types'].items():
        extra_metadata[col] = extra_metadata[col].astype(dtype)

    extra_metadata['start_date'] = pd.to_datetime(extra_metadata['start_date'])
    extra_metadata['end_date'] = pd.to_datetime(extra_metadata['end_date'])
    extra_metadata['DrillDate'] = pd.to_datetime(extra_metadata['DrillDate'])

    for col in meta_data_requirements['needed_columns']:
        if col not in extra_metadata.columns:
            extra_metadata[col] = meta_data_requirements['default_values'].get(col)

    for col, dtype in meta_data_requirements['col_types'].items():
        extra_metadata[col] = extra_metadata[col].astype(dtype)

    extra_metadata = append_to_other(df=extra_metadata, needed_columns=meta_data_requirements["needed_columns"])
    extra_metadata = extra_metadata[meta_data_requirements["needed_columns"]]

    return extra_metadata


def output(local_paths, meta_data_requirements, recalc=False):
    needed_gw_columns = ['well_name', 'date', 'depth_to_water', 'gw_elevation', 'dtw_flag', 'water_elev_flag',
                         'data_source', 'elevation_datum', 'other']

    water_data_store_path = local_paths['save_path']
    store_key_water_data = local_paths['wl_store_key']
    store_key_metadata = local_paths['gisborne_metadata_store_key']

    # Check if data needs to be recalculated or if the HDF files don't exist
    if not recalc and water_data_store_path.exists():
        combined_water_data = pd.read_hdf(water_data_store_path, store_key_water_data)
        combined_metadata = pd.read_hdf(water_data_store_path, store_key_metadata)

    else:

        GDC_metadata = _get_extra_gisborne_metadata(local_paths, meta_data_requirements)
        tethys_data = _get_gisborne_tethys_data(local_paths, meta_data_requirements)
        tethys_water_data = tethys_data['tethys_groundwater_data']
        tethys_water_data['date'] = pd.to_datetime(tethys_water_data['date'])

        tethys_metadata = tethys_data['tethys_metadata_combined']
        tethys_metadata['well_depth'] = tethys_metadata['well_depth'].astype('float')

        gdc_water_data = _get_bespoke_data(local_paths)
        gdc_water_data['date'] = pd.to_datetime(gdc_water_data['date'])
        gdc_water_data['other'] = gdc_water_data['other'].astype(str)

        combined_water_data = pd.concat([tethys_water_data, gdc_water_data], ignore_index=True)
        combined_water_data['date'] = pd.to_datetime(combined_water_data['date']).dt.date
        combined_water_data['date'] = pd.to_datetime(combined_water_data['date'])

        # aggregate the water data
        combined_water_data = aggregate_water_data(combined_water_data)

        combined_metadata = pd.concat([GDC_metadata, tethys_metadata], ignore_index=True)
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
        combined_metadata["artesian"] = np.where(
            combined_metadata['min_dtw'] < 0,  # Else, if 'min_gwl' < 0 (regardless of 'depth_to_water_static')
            True,  # Then also set to True
            False  # Else, set to False
        )

        combined_metadata = combined_metadata[combined_metadata['well_name'].isin(combined_water_data['well_name'])]

        if 'other' not in combined_metadata.columns:
            combined_metadata['other'] = ''

        combined_metadata = append_to_other(df=combined_metadata,
                                            needed_columns=meta_data_requirements["needed_columns"])

        combined_metadata.drop(columns=[col for col in combined_metadata.columns if
                                        col not in meta_data_requirements["needed_columns"] and col != 'other'],
                               inplace=True)
        combined_metadata['start_date'] = pd.to_datetime(combined_metadata['start_date'])
        combined_metadata['end_date'] = pd.to_datetime(combined_metadata['end_date'])
        combined_water_data['well_name'] = combined_water_data['well_name'].astype(str)
        data_checks(combined_water_data)
        metadata_checks(combined_metadata)

        # check well in medata
        # Step 1: Get unique well names from combined_water_data
        unique_well_names = combined_water_data['well_name'].unique()
        # Step 2: Check if these unique well names are present in the 'well_name' column of combined_metadata
        # Make sure to compare against the unique values in combined_metadata['well_name']
        check_data_in_metadata = pd.Series(unique_well_names).isin(combined_metadata['well_name'].unique())
        if not check_data_in_metadata.all():
            # If there are any False values in check_data_in_metadata, print the well names that are not in combined_metadata
            print("The following well names are not in the metadata:")
            print(unique_well_names[~check_data_in_metadata])
        # drop metadata not in water data
        # Step 1: Create a boolean mask where True indicates the presence of 'well_name' from combined_metadata in unique_well_names
        mask = combined_metadata['well_name'].isin(unique_well_names)
        # Step 2: Use the mask to filter combined_metadata, keeping only the rows where 'well_name' is in unique_well_names
        combined_metadata = combined_metadata[mask]

        cols_to_keep = [
            'well_name', 'rl_elevation', 'rl_datum', 'rl_source',
            'ground_level_datum', 'ground_level_source', 'well_depth', 'top_topscreen',
            'bottom_bottomscreen', 'nztm_x', 'nztm_y', 'other', 'dist_mp_to_ground_level'
        ]

        combined_metadata = append_to_other(df=combined_metadata, needed_columns=cols_to_keep)
        combined_metadata.drop(columns=[col for col in combined_metadata.columns if
                                        col not in cols_to_keep and col != 'other'],
                               inplace=True)

        for column in combined_water_data:
            # Check if the column is of pandas nullable Int64 type
            if pd.api.types.is_integer_dtype(combined_water_data[column]) and combined_water_data[
                column].isnull().any():
                # Convert to float64 if there are NaN values, as NaN cannot be represented in pandas' non-nullable integer types
                combined_water_data[column] = combined_water_data[column].astype('float')
            elif pd.api.types.is_integer_dtype(combined_water_data[column]):
                # Convert to NumPy's int64 if there are no NaN values and it is a pandas Int64 type
                combined_water_data[column] = combined_water_data[column].astype('int64')

        renew_hdf5_store(new_data=combined_water_data, old_path=local_paths['save_path'],
                         store_key=local_paths['wl_store_key'])
        renew_hdf5_store(new_data=combined_metadata, old_path=local_paths['save_path'],
                         store_key=local_paths['gisborne_metadata_store_key'])

    return {'combined_water_data': combined_water_data, 'combined_metadata': combined_metadata}


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
        'thethys_local_save_path': local_base_path.joinpath("gwl_gisborne", "cleaned_data", "tethys_gw_data.hdf"),
        'local_path': local_path_mapping
    }

    # Store keys are hardcoded as they are specific to this setup
    local_paths['thethys_gw_depth_local_store_key'] = 'gisborn_gw_depth_data'
    local_paths['thethys_gw_level_local_store_key'] = 'gisborn_gw_level_data'
    local_paths['wl_store_key'] = 'gisborne_gwl_data'
    local_paths['gisborne_metadata_store_key'] = 'gisborne_metadata'
    local_paths['save_path'] = groundwater_data.joinpath('gwl_gisborne', 'cleaned_data', 'combined_gisborne_data.hdf')

    return local_paths


########################################################################################################################
def get_gdc_data(recalc=False, redownload=False):
    local_paths = _get_folder_and_local_paths(source_dir=groundwater_data.joinpath('gwl_gisborne'),
                                              local_dir=unbacked_dir.joinpath('gisborne_working/'),
                                              redownload=redownload)
    meta_data_requirements = needed_cols_and_types("GDC")
    return output(local_paths, meta_data_requirements, recalc=recalc)


save_path = groundwater_data.joinpath('gwl_gisborne', 'cleaned_data', 'combined_gisborne_data.hdf')
wl_store_key = 'gisborne_gwl_data'
gisborne_metadata_store_key = 'gisborne_metadata'

if __name__ == '__main__':
    date = get_gdc_data(recalc=True)
    pass
