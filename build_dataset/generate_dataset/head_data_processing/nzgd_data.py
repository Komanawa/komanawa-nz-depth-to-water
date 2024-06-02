"""
created matt_dumont & P Durney
this script is used to get the data from the NZGD database and process it into a format that can be used in the final database
on: 23/02/24
"""

import numpy as np
import pandas as pd
import pyproj

from build_dataset.generate_dataset.head_data_processing.data_processing_functions import find_overlapping_files, \
    copy_with_prompt, \
    _get_summary_stats, needed_cols_and_types, metadata_checks, \
    data_checks, append_to_other, renew_hdf5_store, assign_flags_based_on_null_values
from build_dataset.generate_dataset.project_base import groundwater_data, unbacked_dir, project_dir


def get_transient_data(local_paths, meta_data_requirements, recalc=False):
    water_data_store_path = local_paths['local_path'] / 'transient_wl.hdf'
    store_key_manual_water_data = 'manual_water_data'
    store_key_ts_water_data = 'ts_water_data'
    store_key_metadata = 'metadata_combined'

    # Check if data needs to be recalculated or if the HDF files don't exist
    if not recalc and water_data_store_path.exists():
        combined_manual_df = pd.read_hdf(water_data_store_path, store_key_manual_water_data)
        combined_ts_df = pd.read_hdf(water_data_store_path, store_key_ts_water_data)
        combined_meta_df = pd.read_hdf(water_data_store_path, store_key_metadata)

    else:
        path = local_paths['local_path'] / 'NZGDExportInstrumentLogs'
        # Initialize a list to store the DataFrames for each CSV file
        list_manual = []
        list_meta = []
        list_ts = []
        # Loop through each file in the directory
        for file in path.iterdir():
            # Construct the full path to the file
            file_path = path / file
            # Check if the current file is a CSV file
            if file_path.suffix == '.xlsx':
                # Read the CSV file, skipping the first 20 rows
                key = file_path.stem
                raw_data = pd.read_excel(file_path, skiprows=0, sheet_name="Manual Reading")
                raw_data['key'] = key
                raw_metadata = pd.read_excel(file_path, skiprows=0, sheet_name="Export template")
                raw_metadata['key'] = key
                raw_ts_data = pd.read_excel(file_path, skiprows=0, sheet_name="Transducer Summary Readings")
                raw_ts_data['key'] = key
                # Add the processed DataFrame to the list
                list_manual.append(raw_data)
                list_meta.append(raw_metadata)
                list_ts.append(raw_ts_data)

        combined_manual_df = pd.concat(list_manual, ignore_index=True)
        combined_manual_df['date'] = pd.to_datetime(combined_manual_df['Reading Date'], dayfirst=True, errors='coerce')
        combined_manual_df = combined_manual_df.drop(columns=['Reading Date'])
        combined_manual_df = combined_manual_df.rename(
            columns={'key': 'site_name', 'Water Level (m)': 'depth_to_water', 'Is Dry': 'dry_well',
                     'measured Standpipe Depth (m)': 'well_depth'})
        assign_flags_based_on_null_values(combined_manual_df, 'depth_to_water', 'dtw_flag', 2, 0)
        assign_flags_based_on_null_values(combined_manual_df, 'gw_elevation', 'water_elev_flag', 2, 0)
        combined_manual_df = combined_manual_df.drop(columns=['dry_well'])
        combined_manual_df['Comments'] = combined_manual_df['Comments'].astype(str)

        combined_meta_df = pd.concat(list_meta, ignore_index=True)
        combined_meta_df = combined_meta_df[
            ['key', 'Reference', 'NZTM X', 'NZTM Y', 'Vertical Datum', 'Ground level (m)',
             '(Standpipe,Borehole, Pieometer) depth (m)',
             'Collar height (m)', 'Depth to screen top (m)', 'Depth to screen bottom (m)']]
        combined_meta_df = combined_meta_df.rename(
            columns={'key': 'site_name', 'Reference': 'bore_no', 'NZTM X': 'nztm_x',
                     'NZTM Y': 'nztm_y', 'Vertical Datum': 'rl_datum',
                     'Ground level (m)': 'rl_elevation',
                     '(Standpipe,Borehole, Pieometer) depth (m)': 'well_depth',
                     'Collar height (m)': 'collar_height',
                     'Depth to screen top (m)': 'top_topscreen',
                     'Depth to screen bottom (m)': 'bottom_bottomscreen'})

        combined_meta_df = combined_meta_df.round({'nztm_x': 0, 'nztm_y': 0})
        for col in meta_data_requirements['needed_columns']:
            if col not in combined_meta_df.columns:
                combined_meta_df[col] = meta_data_requirements['default_values'].get(col)

        for col, dtype in meta_data_requirements['col_types'].items():
            combined_meta_df[col] = combined_meta_df[col].astype(dtype)

        combined_meta_df = append_to_other(df=combined_meta_df,
                                           needed_columns=meta_data_requirements["needed_columns"])
        combined_meta_df['source'] = 'NZGD'

        combined_ts_df = pd.concat(list_ts, ignore_index=True)
        combined_ts_df = combined_ts_df.dropna(subset=['Max Water Level (m)'])
        combined_ts_df['date'] = pd.to_datetime(combined_ts_df['Date'], dayfirst=True, errors='coerce')
        combined_ts_df['depth_to_water'] = (combined_ts_df['Max Water Level (m)'] + combined_ts_df[
            'Min Water Level (m)']) / 2
        combined_ts_df = combined_ts_df.rename(
            columns={'key': 'site_name', 'Is Dry': 'dry_well'})
        combined_ts_df = combined_ts_df.drop(columns=['Date', 'Max Water Level (m)', 'Min Water Level (m)'])
        combined_ts_df['date'] = pd.to_datetime(combined_ts_df['date']).dt.date
        combined_ts_df = combined_ts_df.groupby(['site_name', 'date', 'File Name']).mean('depth_to_water').reset_index()
        assign_flags_based_on_null_values(combined_ts_df, 'depth_to_water', 'dtw_flag', 1, 0)
        assign_flags_based_on_null_values(combined_ts_df, 'gw_elevation', 'water_elev_flag', 1, 0)
        combined_ts_df['date'] = pd.to_datetime(combined_ts_df['date'])

        for column in combined_meta_df:
            # Check if the column is of pandas nullable Int64 type
            if pd.api.types.is_integer_dtype(combined_meta_df[column]) and combined_meta_df[
                column].isnull().any():
                # Convert to float64 if there are NaN values, as NaN cannot be represented in pandas' non-nullable integer types
                combined_meta_df[column] = combined_meta_df[column].astype('float64')
            elif pd.api.types.is_integer_dtype(combined_meta_df[column]):
                # Convert to NumPy's int64 if there are no NaN values and it is a pandas Int64 type
                combined_meta_df[column] = combined_meta_df[column].astype('int64')

        def convert_boolean_columns(df):
            for col in df.columns:
                if df[col].dtype == 'boolean':
                    df[col] = df[col].astype('int64')

        # Convert boolean columns for each DataFrame
        convert_boolean_columns(combined_manual_df)
        convert_boolean_columns(combined_ts_df)
        convert_boolean_columns(combined_meta_df)

        # Continue with HDF5 storage operations
        renew_hdf5_store(new_data=combined_manual_df, old_path=water_data_store_path,
                         store_key=store_key_manual_water_data)
        renew_hdf5_store(new_data=combined_ts_df, old_path=water_data_store_path, store_key=store_key_ts_water_data)
        renew_hdf5_store(new_data=combined_meta_df, old_path=water_data_store_path, store_key=store_key_metadata)

    return {'combined_manual_df': combined_manual_df, 'combined_meta_df': combined_meta_df,
            'combined_ts_df': combined_ts_df}


def get_static_data(local_paths, meta_data_requirements, recalc=False):
    water_data_store_path = local_paths['local_path'] / 'static_wl.hdf'
    store_key_water_data = 'water_data'
    store_key_metadata = 'metadata_combined'

    # Check if data needs to be recalculated or if the HDF files don't exist
    if not recalc and water_data_store_path.exists():
        nzgd_water_data = pd.read_hdf(water_data_store_path, store_key_water_data)
        nzgd_metadata = pd.read_hdf(water_data_store_path, store_key_metadata)

    else:
        needed_gw_columns = ['well_name', 'date', 'depth_to_water', 'gw_elevation', 'dtw_flag', 'water_elev_flag',
                             'data_source', 'elevation_datum', 'other']
        needed_gw_columns_type = {'well_name': "str", 'depth_to_water': "float", 'gw_elevation': "float",
                                  'dtw_flag': "int",
                                  'water_elev_flag': 'int',
                                  'data_source': 'str', 'elevation_datum': "str", 'other': "str"}

        nzgd_path = local_paths['local_path'] / 'NZGD_220224 for Komanawa.xlsx'

        nzgd_data = pd.read_excel(nzgd_path)
        nzgd_data = nzgd_data.rename(
            columns={'LocationID': 'well_name', 'CoordinateSystem': 'coordinate_system', 'Easting\Latitude': 'easting',
                     'Northing\Longitude': 'northing', 'Ground Level': 'rl_elevation', 'Total Depth': 'well_depth',
                     'Ground water measured?': 'ground_water_measured',
                     'Depth to ground water': 'depth_to_water', 'Ground water measured date': 'date'})

        nzgd_data = nzgd_data[['well_name', 'coordinate_system', 'easting',
                               'northing', 'rl_elevation', 'well_depth', 'ground_water_measured',
                               'depth_to_water', 'date']]

        nzgd_data = nzgd_data[nzgd_data['ground_water_measured'] == "Yes"]
        nzgd_data['source'] = 'NZGD'
        nzgd_data['date'] = pd.to_datetime(nzgd_data['date'], dayfirst=True, errors='coerce')
        nzgd_water_data = nzgd_data[['well_name', 'date', 'depth_to_water']].copy()
        assign_flags_based_on_null_values(nzgd_water_data, 'depth_to_water', 'dtw_flag', 3, 0)
        assign_flags_based_on_null_values(nzgd_water_data, 'gw_elevation', 'water_elev_flag', 3, 0)
        nzgd_water_data['data_source'] = 'NZGD'
        nzgd_water_data = append_to_other(df=nzgd_water_data, needed_columns=needed_gw_columns)

        for column in needed_gw_columns:
            if column not in nzgd_water_data.columns:
                # Add the missing column and initialize with NaNs
                nzgd_water_data[column] = np.nan

        nzgd_water_data.drop(columns=[col for col in nzgd_water_data.columns if
                                      col not in needed_gw_columns and col != 'other'],
                             inplace=True)

        for column, dtype in needed_gw_columns_type.items():
            nzgd_water_data[column] = nzgd_water_data[column].astype(dtype)

        # get list of coord_systems - nzgd_metadata_coords = nzgd_data['coordinate_system'].unique()
        nzgd_metadata = nzgd_data.drop(columns=['depth_to_water', 'date']).copy()
        nzgd_metadata['easting'] = nzgd_metadata['easting'].str.replace(',', '', regex=False)
        nzgd_metadata['northing'] = nzgd_metadata['northing'].str.replace(',', '', regex=False)
        nzgd_metadata['easting'] = pd.to_numeric(nzgd_metadata['easting'], errors='coerce')
        nzgd_metadata['northing'] = pd.to_numeric(nzgd_metadata['northing'], errors='coerce')

        coordinate_system_mapping = {
            'NZMG 49 (EPSG27200)': "EPSG:27200",
            'WGS 1984': "EPSG:4326",
            'NZTM 2000 (EPSG2193)': "EPSG:2193",
            'Mount Eden 2000 (EPSG2105)': "EPSG:2105",
            'Bay of Plenty 2000 (EPSG2106)': "EPSG:2106",
            'Wellington 2000 (EPSG2113)': "EPSG:2113",
            'Mount Pleasant 2000 (EPSG2124)': "EPSG:2124",
            'Timaru 2000 (EPSG2126)': "EPSG:2126",
            'Wanganui 2000 (EPSG2111)': "EPSG:2111",
            'Mount Eden 49 (EPSG27205)': "EPSG:27205",
            'Lindis Peak 2000 (EPSG2127)': "EPSG:2127",
            'Hawkes Bay 2000 (EPSG2108)': "EPSG:2108",
            'Marlborough 2000 (EPSG2120)': "EPSG:2120",
            'Nelson 2000 (EPSG2115)': "EPSG:2115",
            'Bay of Plenty 49 (EPSG27206)': "EPSG:27206",
            'Jacksons Bay 2000 (EPSG2123)': "EPSG:2123",
            'Bluff 2000 (EPSG2132)': "EPSG:2132",
            'North Taieri 2000 (EPSG2131)': "EPSG:2131",
            'Wellington 49 (EPSG27213)': "EPSG:27213",
            'Grey 2000 (EPSG2118)': "EPSG:2118",
            'Hokitika 2000 (EPSG2121)': "EPSG:2121",
            'Poverty Bay 49 (EPSG27207)': "EPSG:27207",
            'Mount Nicholas 2000 (EPSG2128)': "EPSG:2128",
            'Amuri 2000 (EPSG2119)': "EPSG:2119",
            'Poverty Bay 2000 (EPSG2107)': "EPSG:2107",
            'Buller 2000 (EPSG2117)': "EPSG:2117",
            'Taranaki 2000 (EPSG2109)': "EPSG:2109",
        }

        default_crs = "EPSG:2193"  # Example: NZTM 2000

        def transform_group(group):
            # Retrieve the coordinate system for the current group
            source_crs = coordinate_system_mapping.get(group.name, default_crs)
            # Initialize the transformer for this group
            transformer = pyproj.Transformer.from_crs(source_crs, default_crs, always_xy=True)
            # Perform the transformation for the entire group
            try:
                group['nztm_x'], group['nztm_y'] = transformer.transform(group['easting'].values,
                                                                         group['northing'].values)
            except Exception as e:
                # Handle or log the exception as needed
                print(f"Error transforming coordinates for group {group.name}: {e}")
                group['nztm_x'], group['nztm_y'] = None, None

            return group

        # Group by 'coordinate_system' and apply the transformation to each group
        nzgd_metadata = nzgd_metadata.groupby('coordinate_system').apply(transform_group)

        nzgd_metadata = nzgd_metadata.drop(columns={'easting', 'northing', 'coordinate_system'})
        nzgd_metadata = nzgd_metadata.round({'nztm_x': 0, 'nztm_y': 0})

        for col in meta_data_requirements['needed_columns']:
            if col not in nzgd_metadata.columns:
                nzgd_metadata[col] = meta_data_requirements['default_values'].get(col)

        for col, dtype in meta_data_requirements['col_types'].items():
            nzgd_metadata[col] = nzgd_metadata[col].astype(dtype)

        if 'other' not in nzgd_metadata.columns:
            nzgd_metadata['other'] = ''

        for column in nzgd_metadata:
            # Check if the column is of pandas nullable Int64 type
            if pd.api.types.is_integer_dtype(nzgd_metadata[column]) and nzgd_metadata[
                column].isnull().any():
                # Convert to float64 if there are NaN values, as NaN cannot be represented in pandas' non-nullable integer types
                nzgd_metadata[column] = nzgd_metadata[column].astype('float64')
            elif pd.api.types.is_integer_dtype(nzgd_metadata[column]):
                # Convert to NumPy's int64 if there are no NaN values and it is a pandas Int64 type
                nzgd_metadata[column] = nzgd_metadata[column].astype('int64')

        for col in nzgd_metadata.columns:
            if nzgd_metadata[col].dtype == 'boolean':
                nzgd_metadata[col] = nzgd_metadata[col].astype('int64')

        renew_hdf5_store(new_data=nzgd_water_data, old_path=water_data_store_path,
                         store_key=store_key_water_data)
        renew_hdf5_store(new_data=nzgd_metadata, old_path=water_data_store_path,
                         store_key=store_key_metadata)

    return {'nzgd_water_data': nzgd_water_data, 'nzgd_metadata': nzgd_metadata}


def output(meta_data_requirements, local_paths, recalc=False):
    water_data_store_path = local_paths['save_path']
    store_key_water_data = local_paths['wl_store_key']
    store_key_metadata = local_paths['nzgd_metadata_store_key']

    if not recalc and water_data_store_path.exists():
        combined_water_data = pd.read_hdf(water_data_store_path, store_key_water_data)
        combined_metadata = pd.read_hdf(water_data_store_path, store_key_metadata)

    else:
        static_data = get_static_data(local_paths, meta_data_requirements, recalc=False)

        nzgd_water_data = static_data['nzgd_water_data'].copy()
        nzgd_metadata = static_data['nzgd_metadata'].copy()

        transient_data = get_transient_data(local_paths, meta_data_requirements, recalc=False)

        tranisent_manual_water_data = transient_data['combined_manual_df'].copy()

        transient_metadata = transient_data['combined_meta_df'].copy()
        transient_metadata['dist_mp_to_ground_level'] = transient_metadata['collar_height']
        transient_metadata = transient_metadata.drop(columns=['collar_height'])
        transient_metadata['well_name'] = transient_metadata['bore_no'].astype(str)
        transient_metadata = transient_metadata.drop(columns=['bore_no'])

        transient_ts_data = transient_data['combined_ts_df'].copy()

        combined_metadata = pd.concat([nzgd_metadata, transient_metadata], ignore_index=True)

        # keynote - there appear to be some duplicate well names in the metadata but they may not be the smae sites, hare to tell
        # default_precision = 0.1  # for example, default precision is 2 decimal places
        # # create dict of precisis ofr none str columns
        # precisions = {col: default_precision for col in combined_metadata.columns
        #               if combined_metadata[col].dtype != object and not pd.api.types.is_datetime64_any_dtype(
        #         combined_metadata[col])}
        # precisions['nztm_x'] = 50
        # precisions['nztm_y'] = 50
        #
        # # Create a list of columns to skip, which are of string type
        # skip_cols = [col for col in combined_metadata.columns
        #              if
        #              combined_metadata[col].dtype == object or pd.api.types.is_datetime64_any_dtype(
        #                  combined_metadata[col])]
        #
        # aggregation_functions = {col: np.nanmean for col in precisions}
        # combined_metadata = merge_rows_if_possible(combined_metadata, on='well_name', precision=precisions,
        #                                            skip_cols=skip_cols, actions=aggregation_functions)
        combined_metadata['well_name'] = np.where(combined_metadata['well_name'] == 'bh1', 'BH1',
                                                  combined_metadata['well_name'])

        combined_metadata_names = combined_metadata[['well_name', 'site_name']].dropna()

        combined_water_data = pd.concat([nzgd_water_data, tranisent_manual_water_data, transient_ts_data],
                                        ignore_index=True)
        combined_water_data = pd.merge(combined_water_data, combined_metadata_names, on='site_name', how='left')
        combined_water_data['well_name'] = np.where(pd.isnull(combined_water_data['well_name_x']),
                                                    combined_water_data['well_name_y'],
                                                    combined_water_data['well_name_x'])
        combined_water_data = combined_water_data.drop(columns=['well_name_x', 'well_name_y'])

        # combined_water_data = aggregate_water_data(combined_water_data)

        stats = _get_summary_stats(combined_water_data)
        stats = stats.set_index('well_name')
        combined_metadata = combined_metadata.set_index('well_name')
        combined_metadata = combined_metadata.combine_first(stats)
        combined_metadata = combined_metadata.reset_index()

        combined_metadata = append_to_other(df=combined_metadata,
                                            needed_columns=meta_data_requirements["needed_columns"])
        combined_metadata = combined_metadata[meta_data_requirements['needed_columns']]
        combined_metadata['start_date'] = pd.to_datetime(combined_metadata['start_date'])
        combined_metadata['end_date'] = pd.to_datetime(combined_metadata['end_date'])
        combined_metadata = combined_metadata.dropna(subset=['well_name'])

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
        combined_metadata['well_name'] = combined_metadata['well_name'].astype(str)
        combined_metadata['other'] = combined_metadata['other'].astype(str)

        renew_hdf5_store(new_data=combined_water_data, old_path=local_paths['save_path'],
                         store_key=local_paths['wl_store_key'])
        renew_hdf5_store(new_data=combined_metadata, old_path=local_paths['save_path'],
                         store_key=local_paths['nzgd_metadata_store_key'])

    return {'combined_water_data': combined_water_data, 'nzgd_metadata': combined_metadata}


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
        'local_path': local_path_mapping
    }

    # Store keys are hardcoded as they are specific to this setup

    local_paths['wl_store_key'] = 'nzgd_gwl_data'
    local_paths['nzgd_metadata_store_key'] = 'nzgd_metadata'
    local_paths['save_path'] = groundwater_data.joinpath('nzgd', 'cleaned_data',
                                                         'combined_nzgd_data.hdf')

    return local_paths


def get_nzgd_data(recalc=False, redownload=False):
    local_paths = _get_folder_and_local_paths(source_dir=project_dir.joinpath('Data/NZGDExportInstrumentLogs/'),
                                              local_dir=unbacked_dir.joinpath('nzgd_working/'), redownload=redownload)
    meta_data_requirements = needed_cols_and_types('NZGD')
    return output(meta_data_requirements, local_paths, recalc=recalc)


if __name__ == '__main__':
    data = get_nzgd_data(recalc=True)
