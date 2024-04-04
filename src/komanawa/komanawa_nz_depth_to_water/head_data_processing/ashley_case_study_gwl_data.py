"""
created Evelyn_Charlesworth 
on: 22/06/2023
"""

""" This Python script cleans and subsets the Ashley case study data"""

import pandas as pd
from komanawa.komanawa_nz_depth_to_water.project_base import groundwater_data
from get_clean_ecan_gwl_data import get_final_ecan_data


def subset_ashley_gwl_data():
    """ This is a function that extracts the timeseries data for the wells located in the Ashley case study area,
    based on the qgis file
    :return dataframe, the subsetted time series data"""

    # the ashley data path
    # nb this is des criteria
     # reading this in to get the well names in the ashley area
    ashley_data_path = groundwater_data.joinpath('gwl_ecan', 'From_ecan', 'cleaned_data',
                                                 'Filtered_clipped_cleaned_ashly.csv')
    # reading in the ashley data
    ashley_data = pd.read_csv(ashley_data_path)

    # reading in the full ecan dataset
    ecan_gwl_data = get_final_ecan_data()[1]

    # subsetting ecan_gwl_data based on the ashley_data well names
    ashley_subset = ecan_gwl_data[ecan_gwl_data['well_name'].isin(ashley_data['well_name'])]
    ashley_subset.reset_index(drop=True, inplace=True)

    # reading out the ashley gwl
    save_path = groundwater_data.joinpath('gwl_ecan', 'From_ecan', 'cleaned_data', 'updated_ashley_ecan_gwl_data.xlsx')
    ashley_subset.to_excel(save_path)

    return ashley_subset

def clean_ashley_metadata():
    """
    This function cleans & updatse the Ashley metadata based on the ECan cleaning process. This is done separately as the Ashley
    metadata is created from the qGis layer, so needs to be updated based on the python processing
    :return: dataframe
    """
    # the ashley data path
    # nb this is des criteria
    ashley_data_path = groundwater_data.joinpath('gwl_ecan', 'From_ecan', 'cleaned_data',
                                                 'Filtered_clipped_cleaned_ashly.csv')
    # reading in the ashley data
    # reading this in to get the well names in the ashley area
    ashley_data = pd.read_csv(ashley_data_path)

    # reading in the full ecan metadata dataset
    ecan_metadata = get_final_ecan_data()[0]

    # subsetting ecan_gwl_data based on the ashley_data well names
    ashley_meta_subset = ecan_metadata[ecan_metadata['well_name'].isin(ashley_data['well_name'])]
    ashley_meta_subset.reset_index(drop=True, inplace=True)

    # reading out the ashley gwl
    save_path = groundwater_data.joinpath('gwl_ecan', 'From_ecan', 'cleaned_data',
                                          'updated_ashley_ecan_metadata.xlsx')
    ashley_meta_subset.to_excel(save_path)

    return ashley_meta_subset


if __name__ == '__main__':
    a = subset_ashley_gwl_data()
    b = clean_ashley_metadata()
    pass