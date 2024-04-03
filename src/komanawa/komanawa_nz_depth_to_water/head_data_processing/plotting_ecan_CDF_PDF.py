"""
created Evelyn_Charlesworth 
on: 23/05/2023
"""
"""This script plots CDFs, PDFs and histograms from multiple datasets to allow for comparison """

import pandas as pd
import matplotlib.pyplot as plt
from komanawa.komanawa_nz_depth_to_water.project_base import project_dir, groundwater_data, gis_data
import numpy as np
from scipy.stats import gaussian_kde
from scipy import stats
from matplotlib.ticker import MultipleLocator
from komanawa.komanawa_nz_depth_to_water.head_data_processing.ashley_case_study_gwl_data import subset_ashley_gwl_data, clean_ashley_metadata
from komanawa.komanawa_nz_depth_to_water.head_data_processing.get_clean_amandine_data import get_all_chch_gwl_data


def get_swl_data():
    """ This function reads in the SWT data (Scott's layer) for the ashley area
    :return dataframe"""

    read_path = gis_data.joinpath('NZ_SWT_ashley_area.csv')
    swl_data = pd.read_csv(read_path)

    return swl_data


def get_ewt_data():
    """
    This function reads in the EWT data for the ashley area
    :return: dataframe
    """
    read_path = gis_data.joinpath('EWT_ashley_area.csv')
    ewt_data = pd.read_csv(read_path)

    return ewt_data


def filter_ashley_data():
    """
    This function filters the ashley metadata based on the required criteria (listed in the readme).
    The ashley timeseries data will then be subset based on the well names
    :return: dataframe
    """
    # reading in the data
    ashley_metadata = clean_ashley_metadata()

    # filtering based on the criteria
    ashley_filtered = ashley_metadata[
        (ashley_metadata['reading_count'] >= 20) & (ashley_metadata['artesian'] == False) & (
                    ashley_metadata['max_gwl'] >= -1)]

    return ashley_filtered


def plot_histograms():
    """
    This function plots histograms of the SWT, EWT and Ashley GWL data
    :return:
    """

    # reading in the data
    swl_data = get_swl_data()
    ewt_data = get_ewt_data()
    # not using the filtered data here as plotting the average
    ashley_data = clean_ashley_metadata()

    # plotting the histograms
    fig, ax = plt.subplots(1, 3, figsize=(15, 5))
    # plotting the SWL data
    ax[0].hist(swl_data['SWL'], bins=20, color='blue')
    ax[0].set_title('SWL data')
    ax[0].set_xlabel('DTW (m)')
    ax[0].set_ylabel('Frequency')
    # plotting the EWT data
    ax[1].hist(ewt_data['VALUE'], bins=20, color='green')
    ax[1].set_title('EWT data')
    ax[1].set_xlabel('DTW (m)')
    ax[1].set_ylabel('Frequency')
    # plotting the Ashley GWL data
    ax[2].hist(ashley_data['mean_gwl'], bins=20, color='red')
    ax[2].set_title('Ashley GWL data')
    ax[2].set_xlabel('DTW (m)')
    ax[2].set_ylabel('Frequency')

    plt.show()
    #plt.savefig(groundwater_data.joinpath('gwl_ecan', 'From_ecan', 'cleaned_data', 'comparison_hist_plots.png'))


def plot_cdfs():
    """
    This function plots cdfs of the SWT, EWT and Ashley data
    :return:
    """

    # reading in the data
    swl_data = get_swl_data()
    ewt_data = get_ewt_data()
    ashley_data = clean_ashley_metadata()

    # plotting the CDFs
    fig, ax = plt.subplots(1, 3, figsize=(15, 5))
    # plotting the SWL data
    # sorting the data first (as per method Matt suggested)
    sorted_swl = np.sort(swl_data['SWL'])
    yvals_swl = np.arange(len(sorted_swl)) / float(len(sorted_swl))
    ax[0].plot(sorted_swl, yvals_swl, color='blue', label='SWL data')
    ax[0].set_title('SWL CDF plot')
    ax[0].set_xlabel('DTW (m)')
    ax[0].set_ylabel('Frequency')
    # plotting the EWT data
    sorted_ewt = np.sort(ewt_data['VALUE'])
    yvals_ewt = np.arange(len(sorted_ewt)) / float(len(sorted_ewt))
    ax[1].plot(sorted_ewt, yvals_ewt, color='green', label='EWT data')
    ax[1].set_title('EWT CDF plot')
    ax[1].set_xlabel('DTW (m)')
    ax[1].set_ylabel('Frequency')

    # plotting the jacobs gwl data



    # plotting the Ashley GWL data
    #sorted_ashley = np.sort(ashley_data['mean_gwl'])
    #yvals_ashley = np.arange(len(sorted_ashley)) / float(len(sorted_ashley))
    #ax[2].plot(sorted_ashley, yvals_ashley, color='red', label='Ashley GWL data')
    #ax[2].set_title('Ashley GWL data')
    #ax[2].set_xlabel('DTW (m)')
    #ax[2].set_ylabel('Frequency')

    plt.show()
    plt.savefig(groundwater_data.joinpath('gwl_ecan', 'From_ecan', 'cleaned_data', 'comparison_CDF_plots.png'))


def plot_cdf_comparison():
    """
    plotting the cdfs all on one plot
    :return:
    """

    # reading in the data
    swl_data = get_swl_data()
    ewt_data = get_ewt_data()
    jacobs_data = get_jacobs_data()

    # sorting the data
    sorted_swl = np.sort(swl_data['SWL'])
    sorted_ewt = np.sort(ewt_data['VALUE'])
    sorted_jacobs = np.sort(jacobs_data['VALUE'])

    # getting cumulative probabilities
    yvals_swl = np.arange(len(sorted_swl)) / float(len(sorted_swl))
    yvals_ewt = np.arange(len(sorted_ewt)) / float(len(sorted_ewt))
    yvals_jacobs = np.arange(len(sorted_jacobs)) / float(len(sorted_jacobs))

    # plotting the cdfs
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(sorted_swl, yvals_swl, color='blue', label='Lincoln Agritech data')
    ax.plot(sorted_ewt, yvals_ewt, color='green', label='EWT data')
    ax.plot(sorted_jacobs, yvals_jacobs, color='red', label='Jacobs data')

    ax.set_title('CDF plots')
    ax.set_xlabel('DTW (m)')
    ax.set_ylabel('Frequency')
    ax.legend()

    # set the x axis limits
    ax.set_xlim([0, 20])
    ax.xaxis.set_major_locator(MultipleLocator(1))

    #plt.show()

    plt.savefig(groundwater_data.joinpath('dtw_layers_comparison_CDF_plots_1m.png'))


def plot_pdfs():
    """
    plotting pdfs of the surfaces
    :return:
    """

    # reading in the data
    swl_data = get_swl_data()
    ewt_data = get_ewt_data()
    jacobs_data = get_jacobs_data()

    # kde estimations
    swl_pdf = gaussian_kde(swl_data['SWL'])
    ewt_pdf = gaussian_kde(ewt_data['VALUE'])
    jacobs_pdf = gaussian_kde(jacobs_data['VALUE'])

    # set up x values
    x = np.linspace(0, 20, 100)

    # plotting the PDFs
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(x, swl_pdf(x), color='blue', label='Lincoln Agritech data')
    ax.plot(x, ewt_pdf(x), color='green', label='EWT data')
    ax.plot(x, jacobs_pdf(x), color='red', label='Jacobs data')

    ax.set_title('PDF Plots')
    ax.set_xlabel('DTW (m)')
    ax.set_ylabel('Probability Density')
    ax.legend()

    # set the x axis limits
    ax.set_xlim([0, 20])

    plt.savefig(groundwater_data.joinpath('dtw_layers_comparison_PDF_plots.png'))


def plot_individual_ashley_hists():
    """ This function plots the histograms for each well in the ashley dataset in order to visualise the distribution
    :return None """

    # reading in the ashley timeseries data
    ashley_timeseries_data = subset_ashley_gwl_data()
    # filtering based on the criteria
    ashley_filtered = filter_ashley_data()
    filtered_well_names = ashley_filtered['well_name'].unique()
    ashley_filtered_timeseries = ashley_timeseries_data[ashley_timeseries_data['well_name'].isin(filtered_well_names)]
    # replacing the well names / with _ so the plots can be saved
    ashley_filtered_timeseries['well_name'] = ashley_filtered_timeseries['well_name'].str.replace('/', '_')

    # plotting a histogram per well
    for well in ashley_filtered_timeseries['well_name'].unique():
        # subset the data
        well_data = ashley_filtered_timeseries[ashley_filtered_timeseries['well_name'] == well]
        # create a new figure for each well
        fig, ax = plt.subplots()
        # plotting the pdfs
        ax.hist(well_data['depth_to_water_ground'], bins=20, alpha = 0.5, density=True)
        ax.set_title(well)
        # save the individual plots
        save_path = groundwater_data.joinpath('gwl_ecan', 'From_ecan', 'cleaned_data', 'ashley_well_plots_hist',
                                              f"{well}.png")
        fig.savefig(save_path)


def plot_individual_ashley_cdfs():
    """ This function plots the cdfs for each well in the ashley dataset
    :return None """

    # reading in the ashley timeseries data
    ashley_timeseries_data = subset_ashley_gwl_data()
    # filtering based on the criteria
    ashley_filtered = filter_ashley_data()
    filtered_well_names = ashley_filtered['well_name'].unique()
    ashley_filtered_timeseries = ashley_timeseries_data[ashley_timeseries_data['well_name'].isin(filtered_well_names)]
    # replacing the well names / with _ so the plots can be saved
    ashley_filtered_timeseries['well_name'] = ashley_filtered_timeseries['well_name'].str.replace('/', '_')

    normal_dist_wells = []
    # go through each of the wells
    for well in ashley_filtered_timeseries['well_name'].unique():
        # subset the data for that well
        well_data = ashley_filtered_timeseries[ashley_filtered_timeseries['well_name'] == well]
        # sort the data
        sorted_data_1 = np.sort(well_data['depth_to_water'])
        # get the y values
        yvals_1 = np.arange(len(sorted_data_1)) / float(len(sorted_data_1))
        # create a new figure for each well
        fig, ax = plt.subplots()
        ax.plot(sorted_data_1, yvals_1)
        ax.set_title(well)
        # save the individual plots
        save_path = groundwater_data.joinpath('gwl_ecan', 'From_ecan', 'cleaned_data', 'ashley_well_plots',
                                              f"{well}.png")
        fig.savefig(save_path)

        # check if the data is normally distributed
        if check_distribution(well_data['depth_to_water']):
            normal_dist_wells.append(well)


def plot_individual_chch_cdfs():
    """ This function plots the cdfs for each well in the Amandine's chch dataset
    :return None """

    # reading in amandine's chch well data
    all_chch_well_data = get_all_chch_gwl_data()
    # filter based on the depth criteria
    # dropping the data column
    all_chch_well_data.drop(columns=['Date'], inplace=True)
    # filter based on a depth criteria
    # if the GWL never gets within 1m of the ground, exclude it
    # want to check the min of each column as the DTW is positive here
    for col in all_chch_well_data.columns:
        if all_chch_well_data[col].min() <= 1:
            gwl_data = all_chch_well_data[col]
            # sort the data
            sorted_data = np.sort(gwl_data)
            # get the y values
            yvals = np.arange(len(sorted_data)) / float(len(sorted_data))
            # create a new figure for each well
            fig, ax = plt.subplots()
            ax.plot(sorted_data, yvals)
            ax.set_title(col)
            # save the individual plots
            save_path1 = groundwater_data.joinpath('gwl_ecan', 'From_ecan', 'cleaned_data', 'chch_well_plots',
                                                   f"{col}.png")
            #fig.savefig(save_path1)


def check_distribution(data):
    """
    This function checks the distribution of datasets to see if they are normally distributed
    :return:
    """

    # performing the Shapiro-Wilk test
    stat, p = stats.shapiro(data)

    # determining if the data is normally distributed based on the p-value
    alpha = 0.05

    if p > alpha:
        return True


def get_normally_dist_data():
    """
    This function uses the list of normally distributed well names to subset the data for only the
    normally distributed data
    :return: dataframe
    """

    # reading in the normally distributed well names
    normally_dist_list = plot_individual_ashley_cdfs()
    # need to replace all of the _ with / otherwise won't recognise as the same
    normally_dist_list = [x.replace('_', '/') for x in normally_dist_list]
    # reading in the ashley timeseries data
    ashley_timeseries_data = subset_ashley_gwl_data()
    # filtering based on the criteria
    ashley_filtered = filter_ashley_data()
    filtered_well_names = ashley_filtered['well_name'].unique()
    ashley_filtered_timeseries = ashley_timeseries_data[ashley_timeseries_data['well_name'].isin(filtered_well_names)]

    # subset the data for the normally distributed wells
    normally_dist_data = ashley_filtered_timeseries[ashley_filtered_timeseries['well_name'].isin(normally_dist_list)]
    normally_dist_data.reset_index(inplace=True, drop=True)
    normally_dist_data.drop(columns=['Unnamed: 0'], inplace=True)

    # reading out the data
    save_path = groundwater_data.joinpath('gwl_ecan', 'From_ecan', 'cleaned_data', 'normally_dist_data.csv')
    normally_dist_data.to_csv(save_path)

    return normally_dist_data


def get_jacobs_data():
    """
    Reading in the Jacobs data for the ashley area
    :return:
    """

    # reading in the data
    read_path = gis_data.joinpath('jacobs_ashley_area.csv')
    jacobs_data = pd.read_csv(read_path)

    return jacobs_data

    return jacobs_data

if __name__ == '__main__':
    #a = get_swl_data()
    #b = get_ewt_data()
    #c = get_ashley_metadata()
    #d = plot_histograms()
    #e = plot_cdfs()
    #f = get_ashley_timeseries()
    #g = plot_individual_ashley_cdfs()
    #h = filter_ashley_data()
    #i = get_normally_dist_data()
    #j = plot_cdf_comparison()
    #k = plot_pdfs()
    l = plot_individual_ashley_hists()
pass
