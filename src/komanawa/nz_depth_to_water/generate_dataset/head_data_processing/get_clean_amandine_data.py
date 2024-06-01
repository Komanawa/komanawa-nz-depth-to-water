"""
created Evelyn_Charlesworth 
on: 22/06/2023
"""

""" This Python script gets and cleans the data passed on from Amandine"""

import pandas as pd
from komanawa.nz_depth_to_water.generate_dataset.project_base import project_dir, groundwater_data, unbacked_dir, \
    gis_data


def get_clean_chch_gwl_data(recalc=False):
    """
    This function reads in the well data for ChCh, as provided by Amandine.
    This is the clean data - Amandine has already done some cleaning, as outlined in her readme
    :return: dataframe
    """
    # uses a recalc method
    save_path = groundwater_data.joinpath('Amandine data', 'clean_chch_well_data.hdf')
    store_key = 'clean_chch_well_data'
    if save_path.exists() and not recalc:
        clean_chch_well_df = pd.read_hdf(save_path, store_key)
    else:

        # reading in the raw data
        chch_gwl_data_path = groundwater_data.joinpath('Amandine data', 'ForZeb_May2023', 'Hourly_210WLS_16-20.csv')
        clean_chch_well_df = pd.read_csv(chch_gwl_data_path)

        clean_chch_well_df.to_hdf(save_path, store_key)

    # handling data types
    clean_chch_well_df['Date'] = pd.to_datetime(clean_chch_well_df['Date'], format='%Y-%m-%d %H:%M:%S')
    # nb: the format of this dataframe is different to the ECan data
    # each well is a column, and the DTW is rows

    return clean_chch_well_df


def get_all_chch_gwl_data(recalc=False):
    """
    This function reads in the well data for ChCh, as provided by Amandine.
    This is the all data - it has not been cleaned by Amandine. We are using this to get the Kaiapoi locations
    :return:
    """
    # uses a recalc method
    save_path = groundwater_data.joinpath('Amandine data','all_chch_well_data.hdf')
    store_key = 'all_chch_well_data'
    if save_path.exists() and not recalc:
        all_chch_well_df = pd.read_hdf(save_path, store_key)
    else:
        # reading in the raw data
        all_chch_gwl_data_path = groundwater_data.joinpath('Amandine data', 'ForZeb_May2023','Hourly_AllWLS_16-20.csv')
        all_chch_well_df = pd.read_csv(all_chch_gwl_data_path)

        all_chch_well_df.to_hdf(save_path, store_key)

    # handling data types
    all_chch_well_df['Date'] = pd.to_datetime(all_chch_well_df['Date'], format='%Y-%m-%d %H:%M:%S')
    # nb: the format of this dataframe is different to the ECan data
    # each well is a column, and the DTW is rows

    return all_chch_well_df


def get_all_wells_metadata():
    """
    This reads in the All Wells ECan layer
    :return: dataframe, the metadata for the ChCh wells
    """
    # defining the path
    all_wells_path = groundwater_data.joinpath('Amandine data', 'all_wells_data.csv')

    # reading in the data
    all_wells_metadata = pd.read_csv(all_wells_path)

    # changing the column names to lowercase
    all_wells_metadata.columns = all_wells_metadata.columns.str.lower()

    # changing the well name so it matches amandine's data
    all_wells_metadata['well_no'] = all_wells_metadata['well_no'].str.replace('/', '_')

    return all_wells_metadata


def clean_chch_wells_metadata():
    """
    This subsets the all wells metadata based on Amandine's clean ChCh well data
    :return: dataframe, the subsetted metadata for Amandine's clean ChCh well data
    """

    # reading in the all wells data
    all_wells_metadata = get_all_wells_metadata()

    # reading in the clean chch well data
    clean_chch_well_data = get_clean_chch_gwl_data()

    # getting the list of names to subset the all ecan wells for
    list_chch_wells = clean_chch_well_data.columns.tolist()
    # removing the date column
    list_chch_wells.remove('Date')

    # subsetting the all wells data with the list of chch wells
    clean_chch_wells_metadata = all_wells_metadata[all_wells_metadata['well_no'].isin(list_chch_wells)]

    # reading out to a csv
    save_path = groundwater_data.joinpath('Amandine data','cleaned_chch_wells_metadata.csv')
    clean_chch_wells_metadata.to_csv(save_path)

    return clean_chch_wells_metadata


def all_chch_wells_metadata():
    """ This subsets the all wells metadata based on Amandine's all ChCh well data (i.e. not just the cleaned data)
    :return: dataframe, the subsetted metadata for Amandine's all ChCh well data
    """

    # reading in the all wells data
    all_wells_metadata = get_all_wells_metadata()

    # reading in the clean chch well data
    all_chch_well_data = get_all_chch_gwl_data()

    # getting the list of names to subset the all ecan wells for
    list_all_chch_wells = all_chch_well_data.columns.tolist()
    # removing the date column
    list_all_chch_wells.remove('Date')

    # subsetting the all wells data with the list of chch wells
    all_chch_wells_metadata = all_wells_metadata[all_wells_metadata['well_no'].isin(list_all_chch_wells)]

    # reading out to a csv
    save_path = groundwater_data.joinpath('Amandine data','all_chch_wells_metadata.csv')
    all_chch_wells_metadata.to_csv(save_path)

    return all_chch_wells_metadata
