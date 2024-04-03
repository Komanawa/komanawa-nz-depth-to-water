"""
This Python script cleans and processes the ECan/Ashley Future Coasts GWL timeseries data
created Evelyn_Charlesworth
finalised BY person: Patrick Durney
on: 02-02-2024
"""

import os
import sys
import time

import numpy as np
import pandas as pd
from pandas.api.types import is_string_dtype, is_float_dtype, \
    is_datetime64_any_dtype  # review I personally prefer to call these as pd.api.types.is...

from data_processing_functions import find_overlapping_files, copy_with_prompt, _get_summary_stats, \
    needed_cols_and_types, renew_hdf5_store, assign_flags_based_on_null_values
from project_base import groundwater_data, unbacked_dir


def get_final_ecan_data(local_paths, recalc=False):
    """
    A function that gets and returns the final ECan datasets, both the GWL and the metadata
    :param recalc: boolean, if True, the data will be recalculated
    :param save: boolean, if True, the data will be saved to the google drive
    :return: (final_cleaned_metadata, final_cleaned_gwl) both pd.DataFrame
    """
    recalc_path = local_paths['save_path']
    if recalc_path.exists() and not recalc:
        combined_metadata = pd.read_hdf(recalc_path, local_paths['ecan_metadata_store_key'])
        combined_water_data = pd.read_hdf(recalc_path, local_paths['wl_store_key'])
    else:
        # reading in the final data
        combined_metadata = _get_final_ecan_metadata_with_summary_stats(local_paths)
        combined_water_data = _clean_ecan_gwl_data(local_paths=local_paths)

        renew_hdf5_store(local_paths['save_path'], local_paths['wl_store_key'], combined_water_data)
        renew_hdf5_store(local_paths['save_path'], local_paths['ecan_metadata_store_key'], combined_metadata)

        # review saving it as a shapefile - not -working on remotes
        # specifying the projection
    #         crs = 'EPSG:2193'
    #         # creating the Geodataframe
    #         geometry = [Point(xy) for xy in zip(combined_metadata['nztm_x'], combined_metadata['nztm_y'])]
    #         gdf = gpd.GeoDataFrame(combined_metadata, geometry=geometry)
    #         # converting datetimes to strings so I can save it
    # #        gdf['start_date'] = gdf['start_date'].astype(str)
    # #        gdf['end_date'] = gdf['end_date'].astype(str)
    #         output_path = gis_data.joinpath('vector', 'cleaned_ecan_metadata.shp')
    #         gdf.to_file(output_path, driver='ESRI Shapefile', crs=crs)

    return {'combined_metadata': combined_metadata, 'combined_water_data': combined_water_data}


def _get_ecan_gwl_data(folder_path, recalc=False):
    """
    A function that reads in the raw ECan GWL data. There are 4 spreadsheets, and it combines them into one dataframe
    :return: dataframe, the combined GWL data from the 4 spreadsheets provided
    """
    t = time.time()
    # uses a recalc method
    save_path = unbacked_dir.joinpath('ecan_working', 'combined_ecan_data.hdf')
    store_key = 'ecan_gwl_data'
    if save_path.exists() and not recalc:
        combined_ecan_gwl_df = pd.read_hdf(save_path, store_key)
    else:
        timeseries_path = folder_path / 'GWL_data'

        list_dfs = []
        for file in os.listdir(timeseries_path):
            file_path = os.path.join(timeseries_path, file)
            raw_df = pd.read_excel(file_path, skiprows=0, dtype=str, engine='openpyxl')
            list_dfs.append(raw_df)
        combined_ecan_gwl_df = pd.concat(list_dfs, ignore_index=True)
        combined_ecan_gwl_df.to_hdf(save_path, store_key)

    print(sys._getframe().f_code.co_name)
    print(time.time() - t)
    return combined_ecan_gwl_df


def _clean_ecan_gwl_data(local_paths):
    """
    A function that cleans the raw ECan GWL data
    dtw_flag = 1= logger, 2= manual, 3= static_oneoff, 4= calculated frm gw_elevation, 5= aquifer test, 6= other
    water_ele_flag = 1= logger, 2= manual, 3= static_oneoff, 4= aquifer test, 5= other
    nte:     tide_da_dict = {'N': 'manually collected by ECan', 'F': 'provided by external party', 'D': 'logger reading',
                    'Y': 'logger reading',
                    'A': 'aquifer test'}
    :return: dataframe, the clean ECan GWL data
    """
    positive = -1
    # reading in the raw data
    ecan_gwl_data = _get_ecan_gwl_data(local_paths, recalc=False)
    # raise NotImplementedError
    ecan_gwl_data["DEPTH_TO_WATER"] = ecan_gwl_data["DEPTH_TO_WATER"].astype(float)
    # make depth to water an actual depth to water - i.e. positive
    ecan_gwl_data["DEPTH_TO_WATER"] = ecan_gwl_data["DEPTH_TO_WATER"] * positive
    ecan_gwl_data = ecan_gwl_data.sort_values(by=['WELL_NO', "DATE_READ"], ascending=[True, True])
    # renaming the columns
    new_names = {'WELL_NO': 'well_name', 'DATE_READ': 'date', 'DEPTH_TO_WATER': 'depth_to_water_mp',
                 'TIDEDA_FLAG': 'tideda_flag', 'COMMENTS': 'comments'}
    ecan_gwl_data = ecan_gwl_data.rename(columns=new_names)

    # sorting the df by well name
    ecan_gwl_data = ecan_gwl_data.sort_values(by='well_name')
    ecan_gwl_data = ecan_gwl_data.reset_index(drop=True)

    # all of the dtw data is from ECan
    ecan_gwl_data['data_source'] = 'ECAN'

    # removing the strange data from the start level of a steptest
    ecan_gwl_data = ecan_gwl_data[ecan_gwl_data['depth_to_water_mp'] != -2090 * positive]


    # changing the depth to water from dtw from mp to dtw from ground
    # reading in ecan metadata (without the summary stats, just the original plain metadata)
    ecan_metadata = _clean_ecan_metadata(local_paths)
    # replacing the NaN values with zeros for the dist_mp_to_ground_level
    ecan_metadata.dist_mp_to_ground_level.fillna(0)
    # using indexing to get the DTW from ground
    ecan_metadata = ecan_metadata.set_index('well_name')
    # replacing the well names with the dist to MP
    # remember this is a copy, not a deep copy/editing the original
    # depth_to_water_mp is positive and dist_mp_to_ground_level negative
    # so adding dist_mp_to_ground from depth_to_water_mp gives dtw_from_ground
    ecan_gwl_data['dist_mp_to_ground_level'] =ecan_metadata.loc[
        ecan_gwl_data.well_name, "dist_mp_to_ground_level"].values
    # assigning those with NaN (as above) or with gwl > 0 as artesian
    # assigning all the dtw with +999 as NaN, ecan's code for artesian but not measured
    idx = ecan_gwl_data['depth_to_water_mp'] <= 997 * positive

    ecan_gwl_data['artesian'] = (ecan_gwl_data['depth_to_water_mp']+ ecan_gwl_data['dist_mp_to_ground_level']) < 0
    ecan_gwl_data.loc[idx, 'depth_to_water_mp'] = np.nan

    # assigning all the dtw with -999 as NaN and dry (ecan's code
    idx = ecan_gwl_data['depth_to_water_mp'] >= -997 * positive
    ecan_gwl_data.loc[idx, 'depth_to_water_mp'] = np.nan
    ecan_gwl_data['dry_well'] = False
    ecan_gwl_data.loc[idx, 'dry_well'] = True

    # adding in an elevation of the groundwater column
    ecan_gwl_data['gw_elevation'] = np.nan
    ecan_gwl_data['elevation_datum'] = None

    # dropping the wells with too high dist to ground mp - e.g these are entered as 400
    wells_to_drop = ['BX23/0884', 'BX23/0896', 'BX23/0898', 'BX23/0905', 'CA19/0049']
    ecan_gwl_data = ecan_gwl_data[~ecan_gwl_data['well_name'].isin(wells_to_drop)]
    ecan_gwl_data = ecan_gwl_data.rename(columns={'depth_to_water_mp': 'depth_to_water'})

    ecan_gwl_data['dtw_flag'] = 0
    # Step 2: Apply conditions
    # Condition when tideda_flag is 'F', set dtw_flag to 3
    ecan_gwl_data.loc[ecan_gwl_data['tideda_flag'] == 'F', 'dtw_flag'] = 3
    ecan_gwl_data.loc[ecan_gwl_data['tideda_flag'] == 'f', 'dtw_flag'] = 3
    # Condition when tideda_flag is 'N', set dtw_flag to 2
    ecan_gwl_data.loc[ecan_gwl_data['tideda_flag'] == 'N', 'dtw_flag'] = 2
    ecan_gwl_data.loc[ecan_gwl_data['tideda_flag'] == 'n', 'dtw_flag'] = 2
    # Condition when tideda_flag is 'D' or y, set dtw_flag to 1
    ecan_gwl_data.loc[ecan_gwl_data['tideda_flag'] == 'D', 'dtw_flag'] = 1
    ecan_gwl_data.loc[ecan_gwl_data['tideda_flag'] == 'd', 'dtw_flag'] = 1
    ecan_gwl_data.loc[ecan_gwl_data['tideda_flag'] == 'Y', 'dtw_flag'] = 1
    # Condition when tideda_flag is 'A', set dtw_flag to 5
    ecan_gwl_data.loc[ecan_gwl_data['tideda_flag'] == 'A', 'dtw_flag'] = 5

    ecan_gwl_data['water_elev_flag'] = 0


    # handling data types
    ecan_gwl_data = ecan_gwl_data.astype(
        {'well_name': 'str', 'depth_to_water': 'float', 'dtw_flag': 'int', 'water_elev_flag': 'int',
         'comments': 'str',
         'artesian': 'bool', 'dry_well': 'bool', 'gw_elevation': 'float',
         'elevation_datum': 'str'})

    ecan_gwl_data['date'] = pd.to_datetime(ecan_gwl_data['date'])

    def _combine_columns(row, columns):
        combined_values = []
        for col in columns:
            value = row[col]
            # Convert the value to string to ensure proper concatenation
            value_str = str(value) if pd.notnull(value) else ''
            combined_values.append(f"{col}: {value_str}")
        return ', '.join(combined_values)

    columns_to_combine = ['dry_well', 'artesian', 'comments']
    ecan_gwl_data['other'] = ecan_gwl_data.apply(_combine_columns, columns=columns_to_combine, axis=1)

    # data check
    data_checks(ecan_gwl_data)

    # reordering the columns
    ecan_gwl_data = ecan_gwl_data[
        ['well_name', 'date', 'depth_to_water', 'gw_elevation', 'dtw_flag',
         'water_elev_flag', 'data_source',
         'elevation_datum', 'other']]

    ecan_gwl_data = ecan_gwl_data.astype(
        {'well_name': 'str', 'depth_to_water': 'float', 'dtw_flag': 'int', 'gw_elevation': 'float',
         'elevation_datum': 'str', 'water_elev_flag': 'int', 'other': 'str', 'data_source': 'str'})

    return ecan_gwl_data


def data_checks(data):
    """
    This function checks the data to see if there are any issues with it, using assertions
    :return: nothing
    """

    t = time.time()
    # first checking it's a dataframe
    assert isinstance(data, pd.DataFrame), 'data is not a dataframe'
    # checking all the strings
    string_columns = ['well_name', 'comments']
    for column in string_columns:
        assert is_string_dtype(data[column]), f'{column} is not a string'

    # checking all floats
    float_columns = ['depth_to_water', 'gw_elevation']
    for column in float_columns:
        assert is_float_dtype(data[column]), f'{column} is not a float'

    # pddatetime
    datetime_cols = ['date']
    for column in datetime_cols:
        assert pd.api.types.is_datetime64_any_dtype(data[column]), f'{column} is not a datetime'

    # checking the GWL ranges
    too_high_idx = data[data['depth_to_water'] < -26]
    if not too_high_idx.empty:
        save_path = unbacked_dir.joinpath('too_high_idx.csv')
        too_high_idx.to_csv(save_path)
        raise ValueError('Wells with too high GWLs are saved to the unbacked project folder')
    else:
        print('all looks ok')

    too_low_idx = data[data['depth_to_water'] > 310]
    if not too_low_idx.empty:
        save_path = unbacked_dir.joinpath('too_low_idx.csv')
        too_low_idx.to_csv(save_path)
        raise ValueError('Wells with too low GWLs are saved to the unbacked project folder')
    else:
        print('all looks ok')

    # checking for any unwanted NaNs
    assert (data['depth_to_water'].isna() & (~data['artesian'] | ~data[
        'dry_well'])).any(), 'NaN values found where artesian or dry well is False'

    print(sys._getframe().f_code.co_name)
    print(time.time() - t)


def _get_ecan_metadata(local_paths):
    """
    A function that reads in the raw ECan metadata
    :return: dataframe, the raw data read directly from the Excel spreadsheet
    """

    t = time.time()
    # defining the path
    ecan_metadata_path = local_paths['local_path'] / 'From_ecan' / 'WellMetadata_updated.xlsx'

    # reading in the raw data
    raw_ecan_metadata = pd.read_excel(ecan_metadata_path)

    print(sys._getframe().f_code.co_name)
    print(time.time() - t)
    return raw_ecan_metadata


def _get_extra_ecan_metadata(local_paths):
    """
    A function that reads in the extra ECan raw metadata (provided on 16/05 to make up the metadata that was missing)
    :return: dataframe, the raw data read directly from the Excel spreadsheet
    """
    t = time.time()

    # defining the path
    extra_ecan_metadata_path = local_paths['local_path'] /'From_ecan' / 'missing_metadata.xlsx'

    extra_ecan_metadata = pd.read_excel(extra_ecan_metadata_path)

    print(sys._getframe().f_code.co_name)
    print(time.time() - t)
    return extra_ecan_metadata


def _clean_ecan_metadata(local_paths):
    """
    This subfunction sorts and cleans the ECan metadata
    :return: dataframe, the clean ECan metadata
    """

    t = time.time()
    # reading in the raw data
    ecan_metadata = _get_ecan_metadata(local_paths)
    # renaming the columns
    new_names = {'Well Number': 'well_name', 'Well Depth': 'well_depth', 'MP Elevation L1937': 'mp_elevation_L1937',
                 'MP Elevation NZVD': 'mp_elevation_NZVD', 'MP to Ground Level': 'dist_mp_to_ground_level',
                 'NZTMX': 'nztm_x', 'NZTMY': 'nztm_y',
                 'Top of Top Screen': 'top_topscreen', 'Bottom of Bottom Screen': 'bottom_bottomscreen',
                 'Screen Count': 'screen_count'}
    ecan_metadata = ecan_metadata.rename(columns=new_names)
    # keynote dropping mp_elevation_NZVD, no idea where this is from but its wrong
    ecan_metadata = ecan_metadata.drop(columns=['mp_elevation_NZVD'])

    # handling exit data types
    ecan_metadata = ecan_metadata.astype({'well_name': 'str', 'well_depth': 'float', 'mp_elevation_L1937': 'float',
                                         'dist_mp_to_ground_level': 'float',
                                          'nztm_x': 'float', 'nztm_y': 'float',
                                          'top_topscreen': 'float', 'bottom_bottomscreen': 'float',
                                          'screen_count': 'float'})

    # reading in the extra ecan metadata
    extra_ecan_metadata = _get_extra_ecan_metadata(local_paths)

    # renaming the columns
    # nb: don't need to rename the well_name column as it is already named correctly
    new_names_2 = {'well_name': 'well_name', 'Comment': 'comment', 'Well Depth': 'well_depth',
                   'MP Elevation L1937': 'mp_elevation_L1937',
                   'MP Elevation NZVD': 'mp_elevation_NZVD', 'MP to Ground Level': 'dist_mp_to_ground_level',
                   'NZTMX': 'nztm_x', 'NZTMY': 'nztm_y',
                   'Top of Top Screen': 'top_topscreen', 'Bottom of Bottom Screen': 'bottom_bottomscreen',
                   'Screen Count': 'screen_count'}
    extra_ecan_metadata = extra_ecan_metadata.rename(columns=new_names_2)

    # handling exit datatypes for the extra metadata
    extra_ecan_metadata = extra_ecan_metadata.astype(
        {'well_name': 'str', 'comment': 'str', 'well_depth': 'float', 'mp_elevation_L1937': 'float',
         'mp_elevation_NZVD': 'float', 'dist_mp_to_ground_level': 'float',
         'nztm_x': 'float', 'nztm_y': 'float',
         'top_topscreen': 'float', 'bottom_bottomscreen': 'float',
         'screen_count': 'float'})

    # joining the two dataframes
    all_ecan_metadata = pd.concat([ecan_metadata, extra_ecan_metadata], ignore_index=True)

    # handling exit datatypes for merged
    all_ecan_metadata = all_ecan_metadata.astype(
        {'well_name': 'str', 'comment': 'str', 'well_depth': 'float', 'mp_elevation_L1937': 'float',
         'mp_elevation_NZVD': 'float', 'dist_mp_to_ground_level': 'float',
         'nztm_x': 'float', 'nztm_y': 'float',
         'top_topscreen': 'float', 'bottom_bottomscreen': 'float',
         'screen_count': 'float'})

    all_ecan_metadata = all_ecan_metadata.loc[pd.notna(all_ecan_metadata['nztm_x'])]

    # combining the elevation column and creating a datum flag column
    all_ecan_metadata['rl_elevation'] = all_ecan_metadata['mp_elevation_NZVD'].combine_first(
        all_ecan_metadata['mp_elevation_L1937'])
    all_ecan_metadata['rl_datum'] = np.where(all_ecan_metadata['mp_elevation_NZVD'].notna(), 'NZVD2016', 'L1937')
    all_ecan_metadata['rl_source'] = 'Environment Canterbury'
    # drop the old columns
    all_ecan_metadata = all_ecan_metadata.drop(columns=['mp_elevation_NZVD', 'mp_elevation_L1937'])

    # doing ground elevation columns
    # where the dist_mp_to_ground is NaN, filling with zero and will flag
    all_ecan_metadata['ground_level_elevation'] = all_ecan_metadata['rl_elevation'] + all_ecan_metadata[
        'dist_mp_to_ground_level'].fillna(0)
    # adding in the ground level elevation datum - will be the same as the RL datum
    all_ecan_metadata['ground_level_elevation_datum'] = all_ecan_metadata['rl_datum']
    # adding in the ground level elevation source
    all_ecan_metadata['ground_level_elevation_source'] = np.where(all_ecan_metadata['dist_mp_to_ground_level'].notna(),
                                                                  'Environment Canterbury', 'no MP height, assumed 0')
    # removing the comments - not needed
    all_ecan_metadata = all_ecan_metadata.drop(columns=['comment'])

    # handling extra datatypes
    all_ecan_metadata = all_ecan_metadata.astype({'rl_elevation': 'float', 'rl_datum': 'str', 'rl_source': 'str',
                                                  'ground_level_elevation': 'float',
                                                  'ground_level_elevation_datum': 'str',
                                                  'ground_level_elevation_source': 'str'})

    print(sys._getframe().f_code.co_name)
    print(time.time() - t)
    return all_ecan_metadata


def _get_final_ecan_metadata_with_summary_stats(local_paths):
    t = time.time()

    original_metadata = _clean_ecan_metadata(local_paths)
    ecan_gwl_data = _clean_ecan_gwl_data(local_paths)
    ecan_gwl_data = ecan_gwl_data.rename(columns={'depth_to_water_mp': 'depth_to_water'})
    # reading in the extra metadata
    summary_stats = _get_summary_stats(ecan_gwl_data)

    # creating the merged dataframe
    # doing an outer join to see where there are wells without original metadata (e.g no well depth etc)
    merged_ecan_metadata = pd.merge(original_metadata, summary_stats, on='well_name', how='outer')
    merged_ecan_metadata['artesian'] = np.where(
        (merged_ecan_metadata['min_dtw'].notnull()) & (merged_ecan_metadata['min_dtw'] < 0),
        True,
        False
    )

    merged_ecan_metadata['dry_well'] = np.where(
        (merged_ecan_metadata['max_dtw'].notnull()) & (merged_ecan_metadata['max_dtw'] > 400),
        True,
        False
    )

    # handling exit data types
    merged_ecan_metadata = merged_ecan_metadata.astype(
        {'well_name': 'str', 'well_depth': 'float', 'rl_elevation': 'float', 'rl_datum': 'str', 'rl_source': 'str',
         'ground_level_elevation': 'float',
         'ground_level_elevation_datum': 'str',
         'ground_level_elevation_source': 'str', 'nztm_x': 'float', 'nztm_y': 'float',
         'top_topscreen': 'float', 'bottom_bottomscreen': 'float',
         'screen_count': 'float', 'mean_dtw': 'float', 'median_dtw': 'float', 'std_dtw': 'float',
         'max_dtw': 'float', 'min_dtw': 'float', 'mean_gwl': 'float', 'median_gwl': 'float', 'std_gwl': 'float',
         'max_gwl': 'float', 'min_gwl': 'float', 'artesian': 'bool', 'dry_well': 'bool'})
    merged_ecan_metadata['start_date'] = pd.to_datetime(merged_ecan_metadata['start_date'],
                                                        format='%Y=%m-%d')
    merged_ecan_metadata['end_date'] = pd.to_datetime(merged_ecan_metadata['end_date'],
                                                      format='%Y=%m-%d')

    # doing data checks before saving
    metadata_data_checks(merged_ecan_metadata)

    # ordering columns
    merged_ecan_metadata = merged_ecan_metadata[
        ['well_name', 'rl_elevation', 'rl_datum', 'rl_source', 'dist_mp_to_ground_level', 'ground_level_elevation',
         'ground_level_elevation_datum', 'ground_level_elevation_source', 'well_depth', 'nztm_x', 'nztm_y',
         'top_topscreen',
         'bottom_bottomscreen', 'screen_count', 'reading_count', 'start_date', 'end_date', 'mean_dtw',
         'median_dtw', 'std_dtw', 'max_dtw', 'min_dtw', 'mean_gwl',
         'median_gwl', 'std_gwl', 'max_gwl', 'min_gwl', 'artesian', 'dry_well']]

    cols_to_keep = [
        'well_name', 'rl_elevation', 'rl_datum', 'rl_source',
        'ground_level_datum', 'ground_level_source', 'well_depth', 'top_topscreen',
        'bottom_bottomscreen', 'nztm_x', 'nztm_y', 'other', 'dist_mp_to_ground_level'
    ]

    # Iterate through each row and consolidate columns not in cols_to_keep into 'other'
    for index, row in merged_ecan_metadata.iterrows():
        other_values = []
        for col in merged_ecan_metadata.columns:
            if col not in cols_to_keep:
                # Append "column_name: value" to the list
                other_values.append(f"{col}: {row[col]}")
                merged_ecan_metadata.at[index, 'other'] = ', '.join(
                    other_values)  # Join all "col: value" pairs with ', '

    # Drop columns not in cols_to_keep and not 'other'
    merged_ecan_metadata.drop(
        columns=[col for col in merged_ecan_metadata.columns if col not in cols_to_keep and col != 'other'],
        inplace=True)

    print(sys._getframe().f_code.co_name)
    print(time.time() - t)
    return merged_ecan_metadata


def metadata_data_checks(data):
    """
    This function checks the data to see if there are any issues with it using assertions
    :return: nothing
    """

    t = time.time()

    # first checking it's a dataframe
    assert isinstance(data, pd.DataFrame), 'data is not a dataframe'

    # checking all the strings
    string_columns = ['well_name']
    for column in string_columns:
        assert is_string_dtype(data[column]), f'{column} is not a string'

    # checking all floats
    float_columns = ['well_depth', 'dist_mp_to_ground_level', 'nztm_x',
                     'nztm_y', 'top_topscreen', 'bottom_bottomscreen', 'screen_count', 'reading_count', 'mean_dtw',
                     'median_dtw', 'std_dtw', 'max_dtw', 'min_dtw']
    for column in float_columns:
        assert is_float_dtype(data[column]), f'{column} is not a float'

    # pddatetime
    datetime_cols = ['start_date', 'end_date']
    for column in datetime_cols:
        assert is_datetime64_any_dtype(data[column]), f'{column} is not a datetime'

    # checking the GWL ranges
    too_high_idx = data[data['mean_dtw'] < -26]
    if not too_high_idx.empty:
        save_path = unbacked_dir.joinpath('mean_gwl_too_high_idx.csv')
        too_high_idx.to_csv(save_path)
        raise ValueError('Wells with too high GWLs are saved to the unbacked project folder')



    too_low_idx = data[data['mean_dtw'] > 310]
    if not too_low_idx.empty:
        save_path = unbacked_dir.joinpath('mean_gwl_too_low_idx.csv')
        too_low_idx.to_csv(save_path)
        raise ValueError('Wells with too low GWLs are saved to the unbacked project folder')
    else:
        print('all looks ok')
    # checking for unique data in the well name
    assert data['well_name'].nunique() == len(data), 'there are duplicate well names in the data'
    print(sys._getframe().f_code.co_name)
    print(time.time() - t)


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
        'ecan_local_save_path': local_base_path.joinpath("gwl_ecan", "cleaned_data", "ecan_gw_data.hdf"),
        'local_path': local_path_mapping
    }

    # Store keys are hardcoded as they are specific to this setup
    local_paths['wl_store_key'] = 'ecan_gwl_data'
    local_paths['ecan_metadata_store_key'] = 'ecan_metadata'
    local_paths['save_path'] = groundwater_data.joinpath('gwl_ecan', 'From_ecan', 'cleaned_data', 'combined_ecan_data.hdf')

    return local_paths


def get_ecan_data(recalc=False, redownload=False):
    local_paths = _get_folder_and_local_paths(source_dir=groundwater_data.joinpath('gwl_ecan'),
                                              local_dir=unbacked_dir.joinpath('ecan_working/'), redownload=redownload)
    meta_data_requirements = needed_cols_and_types('ECAN')

    return get_final_ecan_data(local_paths,
                            recalc=recalc)


if __name__ == '__main__':
    out = get_ecan_data(recalc=True, redownload=False)
    pass
