"""
created Evelyn_Charlesworth
edited by Patrick Durney
on: 3/07/2023
"""

# This python script cleans and processes the Southland data"""
import numpy as np
import pandas as pd

from komanawa.komanawa_nz_depth_to_water.head_data_processing.data_processing_functions import \
    (find_overlapping_files, copy_with_prompt, \
     _get_summary_stats, append_to_other, needed_cols_and_types, data_checks, \
     metadata_checks, renew_hdf5_store, get_hdf5_store_keys, pull_tethys_data_store, assign_flags_based_on_null_values,
     aggregate_water_data)
from komanawa.komanawa_nz_depth_to_water.head_data_processing.merge_rows import merge_rows_if_possible
from komanawa.komanawa_nz_depth_to_water.project_base import groundwater_data, unbacked_dir


def _get_southland_tethys_data(local_paths, meta_data_requirements):
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
                                         council="Southland")

    tethys_data_water_level_24h = tethys_data['/Environment Southland_water_level_24H']

    tethys_metadata = pull_tethys_data_store(
        unbacked_dir.joinpath('tetheys_2024_all', 'tethys_meta_fully_processed.hdf'),
        meta_keys, council="Southland")

    tethys_metadata_water_level_24h = tethys_metadata['/Environment Southland_water_level_24H_metadata']
    tethys_metadata_water_level_24h = tethys_metadata_water_level_24h.rename(
        columns={"bore_depth": "well_depth", 'bore_top_of_screen': 'top_topscreen',
                 'bore_bottom_of_screen': 'bottom_bottomscreen', 'tetheys_elevation': 'rl_elevation'})

    site_names = pd.read_excel(local_paths['local_path'] / 'ES_GroundwaterLevel.xlsx', sheet_name='Site Names')
    site_names = site_names.rename(columns={"alt_well_name": "well_name", "well_name": "alt_name"})
    site_names.set_index('well_name', inplace=True)

    tethys_metadata_water_level_24h.set_index('well_name', inplace=True)
    tethys_metadata_water_level_24h = tethys_metadata_water_level_24h.combine_first(site_names)
    tethys_metadata_water_level_24h.reset_index(inplace=True)

    tethys_water_level_24H = tethys_data_water_level_24h.sort_values(by=['well_name', 'date'], ascending=[True, True])

    tethys_water_level_24H = tethys_data_water_level_24h[needed_gw_columns]

    for col, dtype in needed_gw_columns_type.items():
        tethys_water_level_24H[col] = tethys_water_level_24H[col].astype(dtype)

    tethys_water_level_24H['data_source'] = "tethys"

    assign_flags_based_on_null_values(tethys_water_level_24H, 'depth_to_water', 'dtw_flag', 1, 0)
    assign_flags_based_on_null_values(tethys_water_level_24H, 'gw_elevation', 'water_elev_flag', 1, 0)

    assign_flags_based_on_null_values(tethys_water_level_24H, 'depth_to_water', 'dtw_flag', 1, 0)
    assign_flags_based_on_null_values(tethys_water_level_24H, 'gw_elevation', 'water_elev_flag', 1, 0)

    for col in meta_data_requirements['needed_columns']:
        if col not in tethys_metadata_water_level_24h.columns:
            tethys_metadata_water_level_24h[col] = meta_data_requirements['default_values'].get(col)

    for col, dtype in meta_data_requirements['col_types'].items():
        tethys_metadata_water_level_24h[col] = tethys_metadata_water_level_24h[col].astype(dtype)

    if 'other' not in tethys_metadata_water_level_24h.columns:
        tethys_metadata_water_level_24h['other'] = ''

    tethys_metadata_water_level_24h = append_to_other(df=tethys_metadata_water_level_24h,
                                                      needed_columns=meta_data_requirements["needed_columns"])

    columns_to_select = meta_data_requirements['needed_columns'] + ['alt_name']
    tethys_metadata_water_level_24h = tethys_metadata_water_level_24h[columns_to_select]

    tethys_metadata_water_level_24h['source'] = 'tethys'
    tethys_metadata_water_level_24h['start_date'] = pd.to_datetime(tethys_metadata_water_level_24h['start_date'])
    tethys_metadata_water_level_24h['end_date'] = pd.to_datetime(tethys_metadata_water_level_24h['end_date'])

    return {'tethys_groundwater_data': tethys_water_level_24H,
            'tethys_metadata_combined': tethys_metadata_water_level_24h}


def _get_southland_checks_data(local_paths):
    """Read and process groundwater checks data from Southland.
        Returns:
            pd.DataFrame: The processed groundwater checks data.
        """
    # Define file path
    file_path = local_paths['local_path'] / "ES_GroundwaterLevel.xlsx"

    # Read the checks data
    checks_data = pd.read_excel(file_path, sheet_name='EC_edited_checks')
    # Rename columns explicitly
    checks_data = checks_data.rename(columns={"well_name": "alt_well_name"})

    # Read site names
    site_names = pd.read_excel(file_path, sheet_name='Site Names')

    # Merge dataframes explicitly
    df = pd.merge(checks_data, site_names, on='alt_well_name', how='left')

    # Convert water level to string and remove specific characters
    df['water_level'] = df['water_level'].astype(str)
    df['water_level'] = df['water_level'].str.replace('<', '')
    df['water_level'] = df['water_level'].str.replace('>', '')
    df['water_level'] = df['water_level'].str.replace('*', '')

    # Convert cleaned water level back to float and change units from mm to m
    df['water_level'] = df['water_level'].astype(float) / 1000

    # Update comments based on removals - this part is tricky without lambdas or inplace,
    # so we're opting for a direct assignment approach, which might not capture all nuances.
    df['comments'] = ''  # Initialize comments column
    # You might need a more sophisticated approach here to capture all comment scenarios.

    # Convert date column to datetime format
    df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d %H:%M:%S', errors='coerce')

    return df


def _get_southland_dip_data(local_paths):
    """ this function reads in the dip data as provided by Southland (sent to us)
    :return dataframe, raw data"""


    southland_dip_data = pd.read_excel(
        local_paths['local_path'] / 'GroundwaterLevel_updated.xlsx',
        sheet_name='Dips')

    southland_dip_data_names = pd.read_excel(
        local_paths['local_path'] / 'GroundwaterLevel_updated.xlsx',
        sheet_name='Site Names', header=None)
    southland_dip_data_names = southland_dip_data_names.rename(columns={0: 'well_name', 1: 'alt_name'})

    # renaming the columns
    new_names = {'Site Name': 'alt_name', 'Time': 'date', 'Groundwater Level (RTS)': 'depth_to_water',
                 'Unnamed: 3': 'comments'}
    southland_dip_data.rename(columns=new_names, inplace=True)
    # dropping the first row
    southland_dip_data.drop(0, inplace=True)
    southland_dip_data = pd.merge(southland_dip_data, southland_dip_data_names, on='alt_name', how='left')

    # handling datetime
    southland_dip_data['date'] = pd.to_datetime(southland_dip_data['date'], format='%d/%m/%Y %H:%M:%S')

    return southland_dip_data


def _get_southland_metadata(local_paths):
    """
    This function reads in and cleans the Southland metadata that was provided by ES
    :return: dataframe, the ES metadata
    """

    southland_metadata = pd.read_excel(
        local_paths['local_path'] / 'GroundwaterLevel_updated.xlsx',
        sheet_name='Well Details')

    # renaming columns
    new_names = {'WELL_NO': 'well_name', 'GRID_EAST': 'nztm_x', 'GRID_NORTH': 'nztm_y', 'REFERENCE_RL': 'elevation',
                 'REFERENCE_DESCRIPTION': 'elevation_point', 'DEPTH': 'well_depth', 'TOP_SCREEN_1': 'top_topscreen',
                 'BOTTOM_SCREEN_1': 'bottom_bottomscreen',
                 'INITIAL_SWL': 'depth_to_water_static', 'GroundWater_Zone': 'aquifer'}
    southland_metadata.rename(columns=new_names, inplace=True)

    # dropping the unnecessary columns
    drop_columns = ['dbo_WELL_TYPES.DESCRIPTION', 'Status', 'QAR_CODE', 'EstOrMeas.How', 'EstRepOrMeas.How',
                    'DRILLED_DEPTH',
                    'DIAMETER', 'dbo_USE_CODES_1.DESCRIPTION', 'dbo_USE_CODES_2.DESCRIPTION',
                    'dbo_USE_CODES_3.DESCRIPTION', 'DATE_DRILLED',
                    'dbo_DRILLERS.DESCRIPTION', 'dbo_DRILL_METHODS.DESCRIPTION', 'CASING_MATERIAL',
                    'dbo_SCREEN_TYPES_1.DESCRIPTION', 'dbo_SCREEN_TYPES_2.DESCRIPTION',
                    'PositiveHead', 'PUMP_HOURS', 'YIELD', 'DRAWDOWN', 'TOP_SCREEN_2', 'BOTTOM_SCREEN_2']
    southland_metadata.drop(columns=drop_columns, inplace=True)

    #  handling datatypes
    southland_metadata = southland_metadata.astype(
        {'well_name': 'str', 'nztm_x': 'float', 'nztm_y': 'float', 'elevation': 'float',
         'elevation_point': 'str', 'well_depth': 'float', 'top_topscreen': 'float', 'bottom_bottomscreen': 'float',
         'depth_to_water_static': 'float', 'aquifer': 'str'})

    return southland_metadata


def output(local_paths, meta_data_requirements, recalc=False):
    """This function combines the two sets of metadata and cleans it
    :return: dataframe"""
    water_data_store_path = local_paths['save_path']
    store_key_water_data = local_paths['wl_store_key']
    store_key_metadata = local_paths['southland_metadata_store_key']

    # Check if data needs to be recalculated or if the HDF files don't exist
    if not recalc and water_data_store_path.exists():
        combined_water_data = pd.read_hdf(water_data_store_path, store_key_water_data)
        combined_metadata = pd.read_hdf(water_data_store_path, store_key_metadata)

    else:
        needed_gw_columns_type = {'well_name': "str", 'depth_to_water': "float", 'gw_elevation': "float",
                                  'dtw_flag': "int",
                                  'water_elev_flag': 'int',
                                  'data_source': 'str', 'elevation_datum': "str", 'other': "str"}

        tethys_data = _get_southland_tethys_data(local_paths, meta_data_requirements)
        tethy_gw_data = tethys_data['tethys_groundwater_data']
        tethy_gw_data['date'] = pd.to_datetime(tethy_gw_data['date'])

        tethys_metadata = tethys_data['tethys_metadata_combined']
        tethys_alt_name = tethys_metadata[['well_name', 'alt_name']]
        tethy_gw_data = pd.merge(tethy_gw_data, tethys_alt_name, on='well_name', how='left')

        southland_gwl_check_data = _get_southland_checks_data(local_paths)
        southland_gwl_check_data = southland_gwl_check_data.rename(
            columns={"alt_well_name": "well_name", "well_name": "alt_name", "water_level": "gw_elevation"})
        assign_flags_based_on_null_values(southland_gwl_check_data, 'depth_to_water', 'dtw_flag', 3, 0)
        assign_flags_based_on_null_values(southland_gwl_check_data, 'gw_elevation', 'water_elev_flag', 3, 0)

        southland_dip_data = _get_southland_dip_data(local_paths)
        southland_dip_data['depth_to_water'] = southland_dip_data['depth_to_water'] * -1

        assign_flags_based_on_null_values(southland_dip_data, 'depth_to_water', 'dtw_flag', 3, 0)
        assign_flags_based_on_null_values(southland_dip_data, 'gw_elevation', 'water_elev_flag', 3, 0)

        southland_dip_data.columns.to_list()
        southland_gwl_check_data.columns.to_list()
        tethy_gw_data.columns.to_list()

        tethy_gw_data = tethy_gw_data.reset_index(drop=True)
        southland_gwl_check_data = southland_gwl_check_data.reset_index(drop=True)
        southland_dip_data = southland_dip_data.reset_index(drop=True)
        combined_water_data = pd.concat([tethy_gw_data, southland_gwl_check_data, southland_dip_data],
                                        ignore_index=True)
        combined_water_data["alt_name"] = np.where(pd.isnull(combined_water_data["alt_name"]),
                                                   combined_water_data["well_name"], combined_water_data["alt_name"])
        combined_water_data = combined_water_data.rename(columns={"alt_name": "well_name", "well_name": "alt_name"})

        combined_water_data['date'] = pd.to_datetime(combined_water_data['date']).dt.date
        combined_water_data['date'] = pd.to_datetime(combined_water_data['date'])
        combined_water_data = aggregate_water_data(combined_water_data)
        combined_water_data = combined_water_data.sort_values(by=['depth_to_water', "well_name"],
                                                              ascending=[True, True])

        combined_water_data['data_source'] = np.where(combined_water_data['data_source'].isna(), 'src',
                                                      combined_water_data['data_source'])

        for column, dtype in needed_gw_columns_type.items():
            combined_water_data[column] = combined_water_data[column].astype(dtype)

        tethys_metadata['alt_name'] = np.where(pd.isnull(tethys_metadata["alt_name"]),
                                               tethys_metadata["well_name"], tethys_metadata["alt_name"])
        tethys_metadata = tethys_metadata.rename(columns={"alt_name": "well_name", "well_name": "alt_name"})

        src_metadata = _get_southland_metadata(local_paths)
        src_metadata = src_metadata.rename(columns={"elevation": "rl_elevation"})

        # combining the two metadata sets
        tethys_metadata['start_date'] = pd.to_datetime(tethys_metadata['start_date'])
        tethys_metadata['end_date'] = pd.to_datetime(tethys_metadata['end_date'])
        tethys_metadata['well_depth'] = tethys_metadata['well_depth'].astype(float)

        combined_metadata = pd.concat([tethys_metadata, src_metadata], ignore_index=True)

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

        # combined_metadata = pd.concat([tetheys_metadata, src_metadata], ignore_index=True).sort_values(by='well_name')

        stats = _get_summary_stats(combined_water_data)
        stats = stats.set_index('well_name')
        combined_metadata = combined_metadata.set_index('well_name')
        combined_metadata = combined_metadata.combine_first(stats)
        combined_metadata = combined_metadata.reset_index()

        combined_metadata = combined_metadata.sort_values(by=['well_name', 'start_date'], ascending=[True, True])
        combined_metadata = combined_metadata.dropna(subset=['well_name'])

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
                         store_key=local_paths['southland_metadata_store_key'])

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
        'es_groundwater_data': local_path_mapping.joinpath('gwl_southland', 'ES_GroundwaterLevel.xlsx'),
        'es_groundwater_data_updated': local_path_mapping.joinpath('gwl_southland', 'GroundwaterLevel_updated.xlsx'),
        'thethys_local_save_path': local_base_path.joinpath("gwl_southland", "cleaned_data", "tethys_gw_data.hdf"),
        'southland_local_save_path': local_base_path.joinpath("gwl_southland", "cleaned_data", "southland_gw_data.hdf"),
        'local_path': local_path_mapping
    }

    # Store keys are hardcoded as they are specific to this setup
    local_paths['thethys_gw_depth_local_store_key'] = 'southland_depth_data'
    local_paths['water_level_data_store_key'] = 'water_level_data'
    local_paths['wl_store_key'] = 'southland_gwl_data'
    local_paths['southland_metadata_store_key'] = 'southland_metadata'
    local_paths['save_path'] = groundwater_data.joinpath('gwl_southland', 'cleaned_data', 'combined_southland_data.hdf')

    return local_paths


def get_src_data(recalc=False, redownload=False):
    local_paths = _get_folder_and_local_paths(source_dir=groundwater_data.joinpath('gwl_southland'),
                                              local_dir=unbacked_dir.joinpath('southland_working/'),
                                              redownload=redownload)
    meta_data_requirements = needed_cols_and_types('SRC')
    return output(local_paths, meta_data_requirements, recalc=recalc)


if __name__ == '__main__':
    data = get_src_data(recalc=False)
    pass
