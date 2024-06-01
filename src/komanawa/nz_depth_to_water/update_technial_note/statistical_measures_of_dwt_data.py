"""
This Python script : does xxx
created by: Patrick_Durney
on: 18/04/24
"""

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from scipy.stats import johnsonsu
from scipy.stats import kurtosis
from tabulate import tabulate
from pathlib import Path
from komanawa.nz_depth_to_water.update_technial_note.data_stats import write_rst_table_with_tabulate

depth_categories_desc = {1: 'well depth < 10m or unknown depth and max dtw < 10m',
                         2: '10m <= well depth < 30m or unknown depth and max 10m <= dtw < 30m',
                         3: 'Deeper wells', }  # todo let's add this to the tables... see what outputs look like first.


def categorise_depth_to_water(data):
    # Create depth categories based on well depth
    data['depth_cat'] = 3
    data.loc[(data['well_depth'] < 10) | np.isnan(data['well_depth']), 'depth_cat'] = 1
    data.loc[(data['well_depth'] >= 10) & (data['well_depth'] < 30), 'depth_cat'] = 2
    data.loc[(data['max_dtw'] >= 10) & (data['depth_cat'] == 1), 'depth_cat'] = 2
    data.loc[(data['max_dtw'] > 30) & (data['depth_cat'] == 2), 'depth_cat'] = 3


def _has_depth_less_than_one_meter(depths):
    return (depths < -1).any()


def _prepare_data(wd, md):
    """
    This function loads the data, merges it, and applies several transformations and filters.
    :param wd: time series water level data
    :param md: metadata
    :return:
    """

    # Merge the data on 'site_name'
    data = pd.merge(wd, md, on='site_name', how='left')

    # Apply filters to the data
    data = data[data['dtw_flag'] <= 4]
    data = data.drop(columns=['max_dtw'])

    # Correct the depth to water for 'auk' source
    idx = (data['source_x'] == 'auk') & ((abs(data['depth_to_water_cor'])
                                          - abs(data['depth_to_water'])) > 10)
    data.loc[idx, 'depth_to_water_cor'] = data.loc[idx, 'depth_to_water']

    # Recalculate max depth to water
    grouped = data.groupby('site_name').agg({'depth_to_water_cor': 'max'})
    grouped = grouped.reset_index()
    grouped = grouped.rename(columns={'depth_to_water_cor': 'max_dtw'})
    data = data.merge(grouped, on='site_name', how='left')

    # Fix orc wierdness
    idx = (data['source_x'] == 'orc') & data['depth_to_water_cor'] <= -10
    data.loc[idx, 'depth_to_water_cor'] = data.loc[idx, 'depth_to_water_cor'] + 100

    # Apply transformations to the data
    data['top_topscreen'] = abs(data['top_topscreen'])
    data['well_depth'] = np.where(data['well_depth'] < abs(data['top_topscreen']), abs(data['top_topscreen']),
                                  data['well_depth'])
    categorise_depth_to_water(data)
    # Select relevant columns and apply final filter
    data = data[['site_name', 'nztm_x', 'nztm_y', 'date', 'depth_to_water_cor', 'depth_cat']]

    return data


def _calculate_johnson_su_probabilities(data_frame, depth_column):
    # Calculate for each site or category
    results = []
    for site_name, group in data_frame.groupby('site_name'):
        raw_data = group[depth_column].dropna().values  # Ensure no NaN values

        if len(raw_data) > 30:  # Ensure sufficient data points for reliable fitting
            params = johnsonsu.fit(raw_data)
            probability_01 = johnsonsu.cdf(0.1, *params)
            annual_frequency_01 = probability_01 * 365
            probability_05 = johnsonsu.cdf(0.5, *params)
            annual_frequency_05 = probability_05 * 365
            probability_1 = johnsonsu.cdf(1, *params)
            annual_frequency_1 = probability_1 * 365

            results.append({
                'site_name': site_name,
                'Probability (<0.1m)': probability_01,
                'Annual Frequency (<0.1m)': annual_frequency_01,
                'Probability (<0.5m)': probability_05,
                'Annual Frequency (<0.5m)': annual_frequency_05,
                'Probability (<1m)': probability_1,
                'Annual Frequency (<1m)': annual_frequency_1
            })

    return pd.DataFrame(results)


# Function to calculate quantiles
def quantile_01(x):
    return x.quantile(0.01)


def quantile_99(x):
    return x.quantile(0.99)


def _calculate_stats(data, depth_cat):
    data_filtered = data[data['depth_cat'] == depth_cat]
    stats = data_filtered.groupby('mean_depth_bin').agg({
        'mean': ['mean', quantile_01, quantile_99],
        'std': ['median', quantile_01, quantile_99],
        'max': ['max'],
        'min': ['min'],
        'skew': ['median', quantile_01, quantile_99],
        'kurtosis': ['median', quantile_01, quantile_99],
        'reading_count': 'sum'
    })
    # round to 3 dp
    stats = stats.round(3)
    stats.columns = ['_'.join(col).strip() for col in stats.columns.values]

    stats['depth_cat'] = depth_cat
    stats['mean_dtw_range'] = stats['mean_quantile_01'].astype(str) + ' - ' + stats['mean_quantile_99'].astype(str)
    stats['std_range'] = stats['std_quantile_01'].astype(str) + ' - ' + stats['std_quantile_99'].astype(str)
    stats['skew_range'] = stats['skew_quantile_01'].astype(str) + ' - ' + stats['skew_quantile_99'].astype(str)
    stats['kurtosis_range'] = stats['kurtosis_quantile_01'].astype(str) + ' - ' + stats[
        'kurtosis_quantile_99'].astype(str)
    stats['dtw_range'] = stats['min_min'].astype(str) + ' - ' + stats['max_max'].astype(str)
    stats = stats.drop(columns=['mean_quantile_01', 'mean_quantile_99', 'std_quantile_01',
                                'std_quantile_99', 'skew_quantile_01', 'skew_quantile_99',
                                'kurtosis_quantile_01', 'kurtosis_quantile_99', 'max_max', 'min_min'])
    stats = stats[
        ['depth_cat', 'mean_mean', 'mean_dtw_range', 'dtw_range', 'std_median', 'std_range', 'skew_median',
         'skew_range', 'kurtosis_median', 'kurtosis_range', 'reading_count_sum']]
    stats = stats.rename(columns={'mean_mean': 'mean', 'mean_dtw_range': 'mean_range',
                                  'std_median': 'std_median', 'std_range': 'std_range',
                                  'skew_median': 'skew_median', 'skew_range': 'skew_range',
                                  'kurtosis_median': 'kurtosis_median', 'kurtosis_range': 'kurtosis_range',
                                  'dtw_range': 'dtw_range', 'reading_count_sum': 'observation_reading_count'})
    return stats


def hist_sd(outdir, wd, md):
    """
    This function generates histograms of the mean and standard deviation of the corrected depth to water. It first loads the data, merges it, and applies several transformations and filters.    It then groups the data by site_name and calculates the mean and standard deviation of the corrected depth to water.    Finally, it generates and displays histograms of these calculated means and standard deviations.

    :param outdir:
    :param wd: time series water level data
    :param md: metadata
    :return:
    """

    outdir = Path(outdir)
    outdir.mkdir(exist_ok=True)
    outdir.joinpath('_static').mkdir(exist_ok=True)
    outdir.joinpath('tables').mkdir(exist_ok=True)
    data = _prepare_data(wd, md)
    data['site<-1m'] = data.groupby('site_name')['depth_to_water_cor'].transform(_has_depth_less_than_one_meter)
    data['site<-1m'] = data['site<-1m'].astype(int)
    data = data[data['site<-1m'] == 0]
    data = data.dropna(subset=['nztm_x'])

    # Next split the data into bins by mean depth to water to produce summary stats tables for each bin
    # binds <0.1m, <0.5m, 0.75m,<1m, <1.5m, <2m, <3m, <5m, <10m, <15, <20m,<30m,<50m,<75m,<100m,>100m
    bins = [-np.inf, 0.1, 0.5, 1, 1.5, 2, 3, 5, 10, 15, 20, 30, 50, 75, 100, np.inf]
    # labels are from previous bin value to current bin value eg <1m, <1.5m is 1m to 1.5m
    # Generate labels based on the bins
    bin_labels = []
    for i in range(len(bins) - 1):
        if bins[i] == -np.inf:
            bin_labels.append(f"<{bins[i + 1]}m")
        elif bins[i + 1] == np.inf:
            bin_labels.append(f">{bins[i]}m")
        else:
            bin_labels.append(f"{bins[i]}m to {bins[i + 1]}m")

    # Calculate number of readings per site
    stats_detail = data

    # todo patrick is this codes still needed????? if not let's get rid of it
    # stats_detail['reading_count'] = stats_detail.groupby('site_name')['site_name'].transform('size')
    # stats_detail = stats_detail[
    #     stats_detail['reading_count'] >= 30]  # n=30 stats rule of thumb for min n for sd calculation

    # Select unique sites
    unique_sites = stats_detail.drop_duplicates(
        subset='site_name')  # 3210 sites accross all depth clats that have mre than 30 points

    # unique_sites = unique_sites[unique_sites['depth_cat'] == depth_cat]  # 1537 sites in depth cat 1 with more than 30 obs
    # # we are only concerned with well that represent the shallow resource, hence the filter for depth cat 1
    # stats_detail = stats_detail[stats_detail['depth_cat'] == depth_cat]

    # Then, add the reading count as a new column
    stats_detail['reading_count'] = stats_detail.groupby('site_name')['site_name'].transform('size')
    stats_detail = stats_detail.drop(columns=['nztm_x', 'nztm_y'])
    stats_detail = stats_detail[stats_detail['reading_count'] >= 30]

    # Group by site_name and calculate mean and standard deviation of depth to water corrected
    stats = stats_detail.groupby(['depth_cat', 'site_name']).agg({
        'depth_to_water_cor': ['mean', 'std', 'max', 'min', 'skew', lambda x: kurtosis(x)],
        'depth_cat': 'first',
        'reading_count': 'first'
    })

    stats = stats.reset_index()
    # reduce the data to 1 index level by merging the index levels
    stats.columns = ['_'.join(col).strip() for col in stats.columns.values]
    stats = stats.rename(columns={'site_name_': 'site_name', 'depth_to_water_cor_<lambda_0>': 'kurtosis',
                                  'depth_to_water_cor_skew': 'skew', 'depth_to_water_cor_mean': 'mean',
                                  'depth_to_water_cor_std': 'std', 'depth_to_water_cor_max': 'max',
                                  'depth_to_water_cor_min': 'min', 'nztm_x_first': 'nztm_x',
                                  'nztm_y_first': 'nztm_y', 'depth_cat_first': 'depth_cat',
                                  'reading_count_first': 'reading_count'})

    # Apply pd.cut to create bins
    stats['mean_depth_bin'] = pd.cut(stats['mean'], bins=bins, labels=bin_labels)
    # Check if any entries are in the '>5.0' category
    print(stats[stats['mean_depth_bin'] == '>5.0'])
    stats_useful = stats.drop(columns=['site_name'])

    stats_depth_cat1 = _calculate_stats(stats_useful, 1)
    stats_depth_cat2 = _calculate_stats(stats_useful, 2)
    stats_depth_cat3 = _calculate_stats(stats_useful, 3)

    all_stats = pd.concat([stats_depth_cat1, stats_depth_cat2, stats_depth_cat3], axis=0)
    all_stats = all_stats.dropna()
    # Extract data and headers from the DataFrame
    out = all_stats.values.tolist()
    headers = all_stats.columns.tolist()

    # Generate the RST table
    rst_table = tabulate(out, headers, tablefmt="rst")
    print(rst_table) # todo save this to a file, what exactly is this? # todo add the depth to water bin to the table and it'll make sense....

    # Save the stats to a csv file
    # todo why are we saving this? should it be included in our outputs???
    # all_stats.to_csv(KslEnv.large_working.joinpath('UNbacked', 'Fut', 'stats.csv'))

    # bind stats back to the orignial dataframe on site_name
    stats_detail = pd.merge(stats_detail, stats, on='site_name', how='left')
    sites = stats_detail
    sites = sites.drop_duplicates(subset='site_name')

    stats_results = _calculate_johnson_su_probabilities(stats_detail, 'depth_to_water_cor')
    stats_results = stats_results.reset_index()

    stats_final = pd.merge(stats_results, sites, on='site_name', how='left')

    # todo review tables and make sure the naming is good/consistent
    # next we group by bins and calculate the mean max and min and sd of each probaility and class, skew and kurtosis, min and max and mean of each bin
    summary_stats = stats_final.groupby('mean_depth_bin').agg(
        {'Annual Frequency (<0.1m)': ['mean', 'std', 'max', 'min'],
         'Annual Frequency (<0.5m)': ['mean', 'std', 'max', 'min'],
         'Annual Frequency (<1m)': ['mean', 'std', 'max', 'min'],
         'Probability (<0.1m)': ['mean', 'std'],
         'Probability (<0.5m)': ['mean', 'std'],
         'Probability (<1m)': ['mean', 'std']})

    write_rst_table_with_tabulate(summary_stats, outdir.joinpath('tables', 'summary_variation_stats.rst'),
                                  'Summary of Variation Statistics')  # todo better name

    # next we produce some nice tables for the report, one for each depth frequency
    for depth in ['0.1', '0.5', '1']:
        temp = stats_final.groupby('mean_depth_bin').agg(
            {f'Annual Frequency (<{depth}m)': ['mean', 'std', 'max', 'min'],
             f'Probability (<{depth}m)': ['mean', 'std']})

        write_rst_table_with_tabulate(temp, outdir.joinpath('tables', f'prob_less_{depth}.rst'),
                                      f'Annual Frequency and Probability of Depth to Water <{depth}m')

    # note renaming stats detail stats for these plots
    stats = stats_detail

    for dtw_threshold in [np.inf, 2, 1, 0.5]:

        stats_temp = stats[stats['mean'] < dtw_threshold]
        fig = plt.figure(figsize=(10, 6))
        gs = fig.add_gridspec(2, 2, height_ratios=[1, 0.3])
        ax_dtw = fig.add_subplot(gs[0, 0])
        ax_dtw_cum = ax_dtw.twinx()
        ax_std = fig.add_subplot(gs[0, 1])
        ax_legend = fig.add_subplot(gs[1, :])
        ax_legend.axis('off')

        ax_dtw.hist(stats_temp['mean'], bins=50, alpha=0.7, color='blue', edgecolor='black',
                    label='Mean Depth to Water')
        ax_dtw.set_xlabel('Mean Depth to Water')
        ax_dtw.set_ylabel('Frequency')

        # Save the histogram of SD Depth to Water
        ax_std.hist(stats_temp['std'], bins=50, alpha=0.7, color='orange', edgecolor='black',
                    label='SD Depth to Water')
        ax_std.set_title('Histogram of SD Depth to Water')
        ax_std.set_xlabel('Standard Deviation Depth to Water')
        ax_std.set_ylabel('Frequency')

        # Save the CDF of  Depth to Water
        ax_dtw_cum.hist(stats_temp['depth_to_water_cor'], bins=100, alpha=0.7, color='red', edgecolor='black',
                        cumulative=True,
                        density=True, label='CDF of Depth to Water')
        ax_dtw_cum.axhline(y=0.75, color='k', linestyle='--', label='75% Cumulative Probability')
        ax_dtw_cum.axhline(y=0.95, color='k', linestyle=':', label='95% Cumulative Probability')
        ax_dtw_cum.set_xlim(-0.1, 2)
        ax_dtw_cum.set_ylabel('Cumulative Probability')
        handles_cum, labels_cum = ax_dtw_cum.get_legend_handles_labels()
        handles_dtw, labels_dtw = ax_dtw.get_legend_handles_labels()
        handles_std, labels_std = ax_std.get_legend_handles_labels()
        all_handles = handles_cum + handles_dtw + handles_std
        all_labels = labels_cum + labels_dtw + labels_std
        ax_legend.legend(all_handles, all_labels, loc='center')
        if dtw_threshold == np.inf:
            fig.suptitle(f'Analysis of Depth to Water')
        else:
            fig.suptitle(f'Analysis of Depth to Water less than {dtw_threshold}m')
        fig.tight_layout()
        fig.savefig(outdir.joinpath('_static', f'hist_sd_depth_to_water_lt_{dtw_threshold}.png'))
        plt.close(fig)


def exceedance_prob(outdir, wd, md, depth_cat=1):
    """
    This function generates exceedance probability plots for the corrected depth to water. It first loads the data, merges it, and applies several transformations and filters.

    :param outdir: the output directory
    :param wd: time series water level data
    :param md: metadata
    :param depth_cat: depth category (1, 2, or 3)
    :return:
    """
    outdir = Path(outdir)
    outdir.mkdir(exist_ok=True)
    outdir.joinpath('_static').mkdir(exist_ok=True)

    raw_data = _prepare_data(wd, md)

    data = raw_data.copy()
    # remove clearly artesean_sites

    data['site<-1m'] = data.groupby('site_name')['depth_to_water_cor'].transform(_has_depth_less_than_one_meter)
    data['site<-1m'] = data['site<-1m'].astype(int)
    data = data[data['site<-1m'] == 0]

    # remove spatial errors
    data = data.dropna(subset=['nztm_x'])

    # subsample to sites with more than 30 readings
    data['reading_count'] = data.groupby('site_name')['site_name'].transform('size')
    data = data[data['reading_count'] >= 30]

    # drop wells greated than 10m depth
    data = data[data['depth_cat'] == depth_cat]

    # for sake of argument we will assume that
    # todo patrick is this codes still needed????? if not let's get rid of it
    # # get boolean of sites where depth_to_water_cor is less than 0.5
    # data['site<0.5m'] = data.groupby('site_name')['depth_to_water_cor'].transform(has_depth_less_than_half_meter)
    # data['site<0.5m'] = data['site<0.5m'].astype(int)
    # data = data[data['site<0.5m'] == 1]
    # data['mean_dtw']= data.groupby('site_name')['depth_to_water_cor'].transform('mean')
    # data['date'] = pd.to_datetime(data['date'])
    # unique_sites = data.drop_duplicates(subset='site_name')

    # attempted fto find number of day exceeding 0.1 m but the issue is the data is too sparse to be meaningful
    ##Set the depth threshold
    # depth_threshold = 0.1
    #
    # # Group by year and count days where depth is less than the threshold
    # exceedance_days = data[data['depth_to_water_cor'] < depth_threshold].groupby(
    #     [data['site_name'], data['date'].dt.year]
    # ).size().reset_index(name='days_below_threshold')

    # using cdf of depth to water to find exceedance probability

    sorted_depth = np.sort(data['depth_to_water_cor'])

    # Calculate CDF values
    cdf = np.arange(1, len(sorted_depth) + 1) / len(sorted_depth)

    # Plotting the CDF
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(sorted_depth, cdf, marker='.', linestyle='none')
    ax.set_title('Cumulative Distribution Function of Depth to Water')
    ax.set_xlabel('Depth to Water (m)')
    ax.set_ylabel('CDF')
    fig.savefig(outdir.joinpath(f'cdf_depth_to_water_depth_cat_{depth_cat}.png'))
    plt.close(fig)

