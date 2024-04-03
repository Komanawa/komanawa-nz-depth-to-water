"""
This Python script : does xxx
created by: Patrick_Durney
on: 15/02/24
"""

import os
import pandas as pd
import numpy as np
from project_base import groundwater_data, unbacked_dir
from data_processing_functions import renew_hdf5_store, process_hdf5_data
import shutil
import subprocess
from pathlib import Path
import pyproj
import traceback


def _get_tethys_2024_folder_and_local_paths(source_dir, local_dir, redownload=False):
    """
    Copies the 2024 copy of the Tethys files to a local directory if redownload is True and the source directory exists.

    Parameters:
    - source_dir: str representing the subdirectory within the groundwater_data directory to be copied.
    - local_dir: Path object representing the base local directory where files will be copied.
    - redownload: bool indicating whether to force re-downloading or overwriting existing files.
    """
    raise NotImplementedError('depreciated')
    # Assuming 'groundwater_data' is a predefined Path object pointing to the base data directory
    src_dir = groundwater_data.joinpath(source_dir)
    dst_dir = local_dir.joinpath(src_dir.name)

    if redownload:
        # Check if the source directory exists and is a directory
        if src_dir.exists() and src_dir.is_dir():
            # Check if the destination directory exists, and if not, create it
            if not dst_dir.exists():
                dst_dir.mkdir(parents=True, exist_ok=True)
            # Copy the entire directory structure from source to destination
            shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
            print(f"Successfully copied {src_dir} to {dst_dir}")
        else:
            print(f"Source directory {src_dir} does not exist or is not a directory.")


# plan B

def _get_tethys_2024_folder_and_local_paths_v2(source_dir, local_dir, redownload=False):
    src_dir = groundwater_data.joinpath(source_dir)  # Assuming 'groundwater_data' is defined elsewhere
    dst_dir = local_dir.joinpath(src_dir.name)

    if redownload and src_dir.is_dir():
        # rsync command with --exclude option to skip "canterbury" directories
        command = ["rsync", "-av", "--delete", "--exclude", "*canterbury*/", f"{src_dir}/", f"{dst_dir}/"]
        try:
            subprocess.run(command, check=True)
            print(f"Successfully synced {src_dir} to {dst_dir}")
        except subprocess.CalledProcessError as e:
            print(f"Error syncing {src_dir} to {dst_dir}: {e}")
    else:
        print(f"Redownload not requested or source directory {src_dir} does not exist/is not a directory.")


def _rename_local_folders(parent_directory):  # review not sure why... add a quick doc string or comment
    # Iterate over each entry in the parent directory
    for entry in os.listdir(parent_directory):
        full_entry_path = os.path.join(parent_directory, entry)

        # Check if the entry is a directory
        if os.path.isdir(full_entry_path):
            # Find the last underscore in the directory name
            last_underscore_index = entry.rfind('_')

            # If an underscore was found, and it's not at the start or end of the name
            if last_underscore_index > 0 and last_underscore_index < len(entry) - 1:
                # Construct the new directory name by removing the part after the last underscore
                new_name = entry[:last_underscore_index]
                new_full_path = os.path.join(parent_directory, new_name)

                # Rename the directory
                os.rename(full_entry_path, new_full_path)


def create_tethys_gw_database(parent_directory, save_path):
    # Ensure save_path is a Path object and exists
    save_path = Path(save_path)
    if not save_path.parent.exists():
        save_path.parent.mkdir(parents=True, exist_ok=True)

    # Iterate over each entry in the parent directory
    # review glob might provide a cleaner way to do this, but this isn't bad

    parent_directory = Path(parent_directory)
    data_files = list(parent_directory.glob('**/data/*.csv'))
    metadata_files = list(parent_directory.glob('**/0_all_stations.csv'))

    for entry in os.listdir(parent_directory):  # review Path.iterdir() is a better option
        folder_path = os.path.join(parent_directory, entry)
        data_folder_path = os.path.join(folder_path, 'data')
        metadata_file_path = os.path.join(folder_path, '0_all_stations.csv')

        # Check if the entry is a directory and contains a 'data' subdirectory
        if os.path.isdir(folder_path) and os.path.isdir(data_folder_path):
            # Process data files in the 'data' subdirectory
            process_data_files(data_folder_path, save_path, entry)

            # Process metadata file
            if os.path.exists(metadata_file_path):
                process_metadata_file(metadata_file_path, save_path, f'{entry}_metadata')


def process_data_files(data_folder_path, save_path, store_key):
    debug_path = save_path.parent.joinpath('data_processing_errors.log')
    debug_path.unlink(missing_ok=True)
    list_dfs = []
    files_processed = 0  # Counter for files processed

    for i, file in enumerate(os.listdir(data_folder_path)):  # review quick way to get a counter
        file_path = os.path.join(data_folder_path, file)
        if os.path.isfile(file_path):
            try:
                raw_df = pd.read_csv(file_path, skiprows=1)

                # Extract the part of the file name to use as 'tethys_station_id'
                # Assuming the format is 'ID_OTHER.csv' and ID is what you want to extract
                tethys_station_id = file.split('_')[0]

                # Add 'tethys_station_id' as a new column to raw_df
                raw_df['tethys_station_id'] = tethys_station_id

                list_dfs.append(raw_df)
                files_processed += 1
                print(f"Processed file: {file_path}")  # Debugging print
            except Exception as e:
                # review I would add a debuging module as so:

                with open(debug_path, 'a') as f:
                    f.write(f"Error processing file {file_path=}: {e}\n")
                    f.write(traceback.format_exc() + '\n')
                print(f"Error processing file {file_path}: {e}")  # Debugging print for file processing errors

    print(f"Total files processed: {files_processed}")
    if not list_dfs:
        print(f"No DataFrames to concatenate. Please check the input files in {data_folder_path}.")
        return  # Early exit if no DataFrames to concatenate

    try:
        combined_df = pd.concat(list_dfs, ignore_index=True)
        renew_hdf5_store(save_path, store_key, combined_df)
        print(f"Data successfully saved to {save_path} under key {store_key}")  # Confirmation print
    except ValueError as e:
        print(f"Error concatenating DataFrames: {e}")  # Debugging print for concatenation errors


def process_metadata_file(metadata_file_path, save_path, store_key):
    metadata_df = pd.read_csv(metadata_file_path, skiprows=0)
    with pd.HDFStore(save_path, mode='a') as store:
        if f'/{store_key}' in store.keys():
            store.remove(store_key)
        store.put(store_key, metadata_df, format='fixed')


def process_hdf5_data(save_path, new_save_path, recalc=False):
    save_path = Path(save_path)
    new_save_path = Path(new_save_path)

    if new_save_path.exists() and not recalc:
        print(f"{new_save_path} already exists and recalc is False. Exiting function.")
        return

    with pd.HDFStore(save_path, mode='r') as store:
        for store_key in store.keys():
            if 'metadata' not in store_key:  # Assuming 'metadata' in the name indicates metadata
                processed_tethys_data = store[store_key]

                # Apply your data processing here
                drop_columns = ['quality_code', 'lon', 'lat']
                processed_tethys_data.drop(columns=drop_columns, inplace=True)

                new_names = {
                    'time': 'date',
                    'name': 'site_name',
                    # Add other column renaming as required
                }
                filtered_new_names = {old: new for old, new in new_names.items() if
                                      old in processed_tethys_data.columns}
                processed_tethys_data.rename(columns=filtered_new_names, inplace=True)

                # Perform further processing as needed...

                # Save the processed DataFrame to the new HDF5 store
                with pd.HDFStore(new_save_path, mode='a') as new_store:
                    new_store.put(store_key, processed_tethys_data, format='fixed')
                print(f"Processed and saved data for {store_key} to {new_save_path}")

    print("Processing complete.")


def process_hdf5_metadata_individual(save_path, new_save_path, recalc=False):
    save_path = Path(save_path)
    new_save_path = Path(new_save_path)

    # Check if the new HDF5 file exists and whether to recalculate
    if new_save_path.exists() and recalc == False:
        print(f"{new_save_path} already exists and recalc is False. Exiting function.")
        return
    else:
        # Process each metadata store in the original HDF5
        new_save_path.unlink()
        with pd.HDFStore(save_path, mode='r') as store:
            for store_key in store.keys():
                # Filter for metadata keys
                if 'metadata' in store_key:
                    metadata_df = store[store_key]

                    # Apply any necessary transformations to the metadata

                    # For example, dropping unnecessary columns
                    metadata_df = metadata_df.drop(columns=['quality_code'], errors='ignore')

                    # Rename columns if necessary
                    new_names = {'time': 'date', 'name': 'site_name'}
                    metadata_df.rename(columns={k: v for k, v in new_names.items() if k in metadata_df.columns},
                                       inplace=True)

                    # Save the processed metadata to the new HDF5 store using the original key
                    with pd.HDFStore(new_save_path, mode='a') as new_store:
                        if store_key in new_store.keys():  # Check if the key exists
                            new_store.remove(store_key)  # Remove the existing metadata if it exists
                        new_store.put(store_key, metadata_df, format='table')
                        print(f"Processed and saved metadata for {store_key} to {new_save_path}")

                    print("Processing complete.")
                print("Processing complete.")


def addtional_processing_hdf5_data(save_path, new_save_path, recalc=False):
    save_path = Path(save_path)
    new_save_path = Path(new_save_path)
    needed_gw_columns = ['well_name', 'date', 'depth_to_water', 'gw_elevation', 'dtw_flag', 'water_elev_flag',
                         'data_source', 'elevation_datum', 'other']

    needed_gw_columns_type = {'well_name': "str", 'depth_to_water': "float", 'gw_elevation': "float",
                              'dtw_flag': "Int64",
                              'water_elev_flag': 'Int64',
                              'data_source': 'str', 'elevation_datum': "str", 'other': "str"}

    if new_save_path.exists() and not recalc:
        print(f"{new_save_path} already exists and recalc is False. Exiting function.")
        return

    with pd.HDFStore(save_path, mode='r') as store:
        for store_key in store.keys():
            if 'metadata' not in store_key:  # Assuming 'metadata' in the name indicates metadata
                processed_tethys_data = store[store_key]

                processed_tethys_data = processed_tethys_data.rename(
                    columns={'site_name': 'well_name', 'altitude': 'tethys_elevation'})

                if "water_level" and "24H" in store_key:
                    processed_tethys_data = processed_tethys_data.rename(
                        columns={'water_level': 'gw_elevation'})
                    processed_tethys_data['water_elev_flag'] = 1
                    processed_tethys_data['dtw_flag'] = 6
                elif "water_level" and "None" in store_key:
                    processed_tethys_data = processed_tethys_data.rename(
                        columns={'water_level': 'gw_elevation'})
                    processed_tethys_data['water_elev_flag'] = 2
                    processed_tethys_data['dtw_flag'] = 6
                elif "groundwater_depth" and "24H" in store_key:
                    processed_tethys_data = processed_tethys_data.rename(
                        columns={'groundwater_depth': 'depth_to_water'})
                    processed_tethys_data['dtw_flag'] = 1
                    processed_tethys_data['water_elev_flag'] = 5
                elif "groundwater_depth" and "None" in store_key:
                    processed_tethys_data = processed_tethys_data.rename(
                        columns={'groundwater_depth': 'depth_to_water'})
                    processed_tethys_data['dtw_flag'] = 2
                    processed_tethys_data['water_elev_flag'] = 5

                for column in needed_gw_columns:
                    if column not in processed_tethys_data.columns:
                        # Add the missing column and initialize with NaNs or another suitable default value
                        processed_tethys_data[column] = np.nan

                for column, dtype in needed_gw_columns_type.items():
                    processed_tethys_data[column] = processed_tethys_data[column].astype(dtype)

                for column in needed_gw_columns:
                    # Check if the column is of pandas nullable Int64 type
                    if pd.api.types.is_integer_dtype(processed_tethys_data[column]) and processed_tethys_data[
                        column].isnull().any():
                        # Convert to float64 if there are NaN values, as NaN cannot be represented in pandas' non-nullable integer types
                        processed_tethys_data[column] = processed_tethys_data[column].astype('float64')
                    elif pd.api.types.is_integer_dtype(processed_tethys_data[column]):
                        # Convert to NumPy's int64 if there are no NaN values and it is a pandas Int64 type
                        processed_tethys_data[column] = processed_tethys_data[column].astype('int64')

                # Perform further processing as needed...

                # Save the processed DataFrame to the new HDF5 store
                with pd.HDFStore(new_save_path, mode='a') as new_store:
                    new_store.put(store_key, processed_tethys_data, format='fixed')
                print(f"Processed and saved data for {store_key} to {new_save_path}")

    print("Processing complete.")


def additional_processing_hdf5_metadata_individual(data_store_path, original_metadata_store_path,
                                                   new_metadata_store_path, recalc=False):
    data_store_path = Path(data_store_path)
    original_metadata_store_path = Path(original_metadata_store_path)
    new_metadata_store_path = Path(new_metadata_store_path)

    if not data_store_path.exists() or not original_metadata_store_path.exists():
        print("Data store or original metadata store does not exist. Exiting function.")
        return

    with pd.HDFStore(data_store_path, mode='r') as data_store, pd.HDFStore(original_metadata_store_path,
                                                                           mode='r') as original_metadata_store:
        if recalc:
            with pd.HDFStore(new_metadata_store_path, mode='a') as new_metadata_store:
                for data_key in data_store.keys():
                    if 'metadata' not in data_key:
                        data_df = data_store[data_key]
                        metadata_key = f"{data_key}_metadata"

                        data_df = data_df.drop_duplicates(subset=['tethys_station_id', 'date'])

                        if metadata_key in original_metadata_store.keys():
                            metadata_df = original_metadata_store[metadata_key]
                            if 'well_name' in data_df.columns:
                                # Keep all columns from data_df and merge with metadata_df
                                combined_df = pd.merge(metadata_df, data_df, on='tethys_station_id', how='left')

                                # Check for 'alt_name' and 'ref' columns and convert them to string type
                                if 'alt_name' in combined_df.columns:
                                    combined_df['alt_name'] = combined_df['alt_name'].astype(str)
                                if 'ref' in combined_df.columns:
                                    combined_df['ref'] = combined_df['ref'].astype(str)

                                combined_df = combined_df.rename(
                                    columns={'from_date': 'start_date', 'to_date': 'end_date',
                                             'num_samp': 'reading_count', 'altitude': "tetheys_elevation"})

                                lat_long = pyproj.Proj('epsg:4326')
                                nztm = pyproj.Proj('epsg:2193')

                                combined_df['nztm_y'], combined_df['nztm_x'] = (
                                    pyproj.transform(lat_long, nztm, combined_df['lat'],
                                                     combined_df['lon']))
                                combined_df = combined_df.round({'nztm_x': 0, 'nztm_y': 0})

                                new_metadata_store.put(metadata_key, combined_df, format='table')
                                print(f"Updated metadata for {metadata_key} with information from data store.")

                        print("Processing complete.")

    print("Processing complete.")



def get_tethys_store_paths(recalc=False, redownload=False, recalc_download=False, recalc_rename=False, recalc_create_db=False,
                           recalc_process_data=False, recalc_process_metadata=False, recalc_additional_processing=False,
                           recalc_additional_metadata_processing=False):
    """
    Obtains paths to the Tethys data store and metadata store, with options to recalculate paths and redownload data.
    Allows for fine-grained control over which steps of the process are executed, including data download, renaming,
    database creation, data processing, and more.

    :param recalc: bool, general flag to recalculate all steps if True.
    :param redownload: bool, general flag to redownload all data if True.
    :param recalc_download: bool, specific flag to redownload data from the remote source.
    :param recalc_rename: bool, specific flag to rename local folders for standardization.
    :param recalc_create_db: bool, specific flag to recreate the groundwater database.
    :param recalc_process_data: bool, specific flag to reprocess the HDF5 data store.
    :param recalc_process_metadata: bool, specific flag to reprocess the HDF5 metadata store.
    :param recalc_additional_processing: bool, specific flag for additional data processing steps.
    :param recalc_additional_metadata_processing: bool, specific flag for additional metadata processing steps.
    :return: tuple of Path objects, paths to the metadata store and the Tethys ts data store.
    """
    # Define paths for metadata and data stores
    save_path_meta = groundwater_data.joinpath('tethys_gwl_data_pull_2024_metadata.hdf')
    save_path_data = groundwater_data.joinpath('tethys_gwl_data_pull_2024_tsdata.hdf')

    # Check existing paths and return if recalculation is not required
    if not recalc and (save_path_meta.exists() and save_path_data.exists()):
        print(f"{save_path_meta} and {save_path_data} already exist and recalc is False. Exiting function.")
        return save_path_meta, save_path_data

    # Determine if any step needs recalculation based on specific flags or the general recalc flag
    if recalc or redownload or recalc_download:
        # Redownload data step
        _get_tethys_2024_folder_and_local_paths_v2(source_dir=groundwater_data.joinpath('tethys_gwl_data_pull_2024'),
                                                   local_dir=unbacked_dir.joinpath('tetheys_2024_all'),
                                                   redownload=redownload or recalc_download)

    if recalc or recalc_rename:
        # Rename folders step
        _rename_local_folders(unbacked_dir.joinpath('tetheys_2024_all', 'tethys_gwl_data_pull'))

    if recalc or recalc_create_db:
        # Create database step
        create_tethys_gw_database(parent_directory=unbacked_dir.joinpath('tetheys_2024_all', 'tethys_gwl_data_pull'),
                                  save_path=unbacked_dir.joinpath('tetheys_2024_all', 'tethys_gwl_data_pull.hdf'))

    if recalc or recalc_process_data:
        # Process data step
        process_hdf5_data(unbacked_dir.joinpath('tetheys_2024_all', 'tethys_gwl_data_pull.hdf'),
                          unbacked_dir.joinpath('tetheys_2024_all', 'tethys_processed.hdf'), recalc=True)

    if recalc or recalc_process_metadata:
        # Process metadata step
        process_hdf5_metadata_individual(unbacked_dir.joinpath('tetheys_2024_all', 'tethys_gwl_data_pull.hdf'),
                                         unbacked_dir.joinpath('tetheys_2024_all', 'tethys_meta_processed.hdf'),
                                         recalc=True)

    if recalc or recalc_additional_processing:
        # Additional data processing step
        addtional_processing_hdf5_data(save_path=unbacked_dir.joinpath('tetheys_2024_all', 'tethys_processed.hdf'),
                                       new_save_path=unbacked_dir.joinpath('tetheys_2024_all',
                                                                           'tethys_fully_processed.hdf'),
                                       recalc=True)

    if recalc or recalc_additional_metadata_processing:
        # Additional metadata processing step
        additional_processing_hdf5_metadata_individual(
            data_store_path=unbacked_dir.joinpath('tetheys_2024_all', 'tethys_fully_processed.hdf'),
            original_metadata_store_path=unbacked_dir.joinpath('tetheys_2024_all', 'tethys_meta_processed.hdf'),
            new_metadata_store_path=unbacked_dir.joinpath(
                'tetheys_2024_all',
                'tethys_meta_fully_processed.hdf'), recalc=True)

    # push the finished stores to the google drive
    shutil.copy(unbacked_dir.joinpath('tetheys_2024_all', 'tethys_meta_fully_processed.hdf'), save_path_meta)
    shutil.copy(unbacked_dir.joinpath('tetheys_2024_all', 'tethys_fully_processed.hdf'), save_path_data)
    return save_path_meta, save_path_data




if __name__ == '__main__':
    # review I would sort the projection of data here.
    # review a bit hard to follow what is going on here...
    # review, typically bad form to comment out stuff with out explaining why  I'm assuming you don't need to re-run
    # reivew I would wrap up the full process in a function and call it here
    get_tethys_store_paths(recalc=False)
