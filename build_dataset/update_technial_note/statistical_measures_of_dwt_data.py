"""
This Python script : does xxx
created by: Patrick_Durney
on: 18/04/24
"""

from pathlib import Path

import numpy as np
import pandas as pd
from komanawa.ksl_tools.spatial.lidar_support.build_lidar_support import KslEnv
from komanawa.modeltools import RectangularModelTools
from matplotlib import pyplot as plt
from scipy.stats import johnsonsu, kurtosis
from collections import deque

from build_dataset.generate_dataset.project_base import groundwater_data
from build_dataset.update_technial_note.data_stats import write_rst_table_with_tabulate

depth_categories_desc = {1: 'well depth < 10m or unknown depth and max dtw < 10m',
                         2: '10m <= well depth < 30m or unknown depth and max 10m <= dtw < 30m',
                         3: 'deep wells (>=30m)', }


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
    stats = data_filtered.groupby('mean_depth_bin', observed=False).agg({
        'mean': ['mean', quantile_01, quantile_99],
        'std': ['median', quantile_01, quantile_99],
        'max': ['max'],
        'min': ['min'],
        'skew': ['median', quantile_01, quantile_99],
        'kurtosis': ['median', quantile_01, quantile_99],
        'reading_count': 'sum',
        'site_name': 'nunique'
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
         'skew_range', 'kurtosis_median', 'kurtosis_range', 'reading_count_sum', 'site_name_nunique']]
    stats = stats.rename(columns={'mean_mean': 'mean', 'mean_dtw_range': 'mean_range',
                                  'std_median': 'std_median', 'std_range': 'std_range',
                                  'skew_median': 'skew_median', 'skew_range': 'skew_range',
                                  'kurtosis_median': 'kurtosis_median', 'kurtosis_range': 'kurtosis_range',
                                  'dtw_range': 'dtw_range', 'reading_count_sum': 'observation_reading_count',
                                  'site_name_nunique': 'n_sites'})
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

    # Select unique sites
    unique_sites = stats_detail.drop_duplicates(
        subset='site_name')  # 3210 sites accross all depth clats that have mre than 30 points

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
    stats_useful = stats.copy()

    stats_depth_cat1 = _calculate_stats(stats_useful, 1)
    stats_depth_cat2 = _calculate_stats(stats_useful, 2)
    stats_depth_cat3 = _calculate_stats(stats_useful, 3)
    tables = [stats_depth_cat1, stats_depth_cat2, stats_depth_cat3]
    depth_cats = [1, 2, 3]

    for stats_depth, depth_cat in zip(tables, depth_cats):
        stats_depth = stats_depth.copy()
        stats_depth = stats_depth.dropna()
        stats_depth.index.name = 'Mean DTW Bin'
        stats_depth['n_obs.'] = stats_depth['observation_reading_count']
        stats_depth = stats_depth[['std_median',
                                   'std_range', 'skew_median', 'skew_range', 'kurtosis_median',
                                   'kurtosis_range', 'n_obs.', 'n_sites']]
        stats_depth.columns = [e.replace('_', ' ').capitalize() for e in stats_depth.columns]
        write_rst_table_with_tabulate(stats_depth, outdir.joinpath('tables', f'stats_depth_cat_{depth_cat}.rst'),
                                      f'Summary of variance and skewness for {depth_categories_desc[depth_cat]}')

    # Extract data and headers from the DataFrame

    # bind stats back to the orignial dataframe on site_name
    stats_detail = pd.merge(stats_detail, stats, on='site_name', how='left')
    sites = stats_detail
    sites = sites.drop_duplicates(subset='site_name')

    stats_results = _calculate_johnson_su_probabilities(stats_detail, 'depth_to_water_cor')
    stats_results = stats_results.reset_index()

    stats_final = pd.merge(stats_results, sites, on='site_name', how='left')

    # next we produce some nice tables for the report, one for each depth frequency
    for depth in ['0.1', '0.5', '1']:
        temp = stats_final.groupby('mean_depth_bin', observed=False).agg(
            {f'Annual Frequency (<{depth}m)': ['mean', 'std', 'min', 'max', ],
             f'Probability (<{depth}m)': ['mean', 'std']})

        t = [' '.join(reversed(col)).strip().capitalize() for col in temp.columns.values]
        t = [e.replace(f'annual frequency (<{depth}m)', f'n days DTW < {depth}') for e in t]
        temp.columns = t
        temp.index.name = 'Mean DTW Bin'

        write_rst_table_with_tabulate(temp, outdir.joinpath('tables', f'prob_less_{depth}.rst'),
                                      f'Annual Frequency and Probability of Depth to Water <{depth}m')

    # note renaming stats detail stats for these plots
    stats = stats_detail

    for dtw_threshold in [np.inf, 2, 1, 0.5]:
        stats_temp = stats[stats['mean'] < dtw_threshold]
        fig = plt.figure(figsize=(10, 6))
        gs = fig.add_gridspec(2, 3, height_ratios=[1, 0.3])
        ax_dtw = fig.add_subplot(gs[0, 0])
        ax_dtw_cum = fig.add_subplot(gs[0, 2])
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
        ax_std.set_xlabel('Standard Deviation Depth to Water')
        ax_std.set_ylabel('Frequency')

        # Save the CDF of  Depth to Water
        cum_measure = stats_temp.loc[
            stats_temp.depth_to_water_cor < np.nanpercentile(stats_temp.depth_to_water_cor, 99), 'depth_to_water_cor']
        ax_dtw_cum.hist(cum_measure, bins=100, alpha=0.7, color='red', edgecolor='black',
                        cumulative=True,
                        density=True, label='CDF of Depth to Water')
        ax_dtw_cum.axhline(y=0.75, color='k', linestyle='--', label='75% Cumulative Probability')
        ax_dtw_cum.axhline(y=0.95, color='k', linestyle=':', label='95% Cumulative Probability')
        ax_dtw_cum.set_ylabel('Cumulative Probability')
        ax_dtw_cum.set_xlabel('Depth to Water')
        handles_cum, labels_cum = ax_dtw_cum.get_legend_handles_labels()
        handles_dtw, labels_dtw = ax_dtw.get_legend_handles_labels()
        handles_std, labels_std = ax_std.get_legend_handles_labels()
        all_handles = handles_dtw + handles_std + handles_cum
        all_labels = labels_dtw + labels_std + labels_cum
        ax_legend.legend(all_handles, all_labels, loc='center', ncol=3)
        if dtw_threshold == np.inf:
            fig.suptitle(f'Analysis of Depth to Water')
            ax_dtw_cum.set_xlim(-1, 150)
        else:
            fig.suptitle(f'Analysis of Depth to Water\nWhere the mean depth to water is less than {dtw_threshold}m')
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

    # using cdf of depth to water to find exceedance probability

    sorted_depth = np.sort(data['depth_to_water_cor'])

    # Calculate CDF values
    cdf = np.arange(1, len(sorted_depth) + 1) / len(sorted_depth)

    # Plotting the CDF
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(sorted_depth, cdf, c='k')
    ax.set_title(f'Cumulative Distribution Function of Depth to Water \nfor {depth_categories_desc[depth_cat]}')
    ax.set_xlabel('Depth to Water (m)')
    ax.set_ylabel('CDF')
    fig.savefig(outdir.joinpath('_static', f'cdf_depth_to_water_depth_cat_{depth_cat}.png'))
    plt.close(fig)


def density_plot_sites(recalc=False):
    """
    This function calculates the density of sites in the model domain and saves the results to .tiff files.
    It checks if recalculation is requested. If recalculation is requested, it calculates the density of sites based on the loaded data and saves the results to .tiff files.

    Parameters:
    recalc (bool): A flag indicating whether to recalculate the density of sites. Default is False.

    Returns:
    None. The function saves the results to .tiff files.
    """

    if recalc:
        # Load prior results and convert to DataFrame
        data = load_training_data()
        wd = data['wd']
        md = data['md']

        # Copy the data and reset the index
        new_df = md.copy().reset_index(drop=True)
        i, j = smt.convert_coords_to_matix(new_df['nztm_x'], new_df['nztm_y'], coords_out_domain='coerce')
        new_df['i'] = i
        new_df['j'] = j

        array = smt.get_no_flow()
        # make array 2d
        array = array[0]

        # Initialize a 2D array with NaN values
        grid = array.copy()*np.nan

        # Update the 2D array with the count of the number of sites in each cell
        df = new_df.groupby(['i', 'j']).size().reset_index(name='count')
        grid[df['i'], df['j']] = df['count']
        # replace nans in grid with 0
        grid = np.nan_to_num(grid)

        # now make copy of array again and find the number of cells to the nearest non nan cell in grid
        distance_grid_nearest_site = find_min_distance_to_target(grid, 1, array)
        distance_grid_nearest_10_sites = find_min_distance_to_target(grid, 10, array)

        # Save the results to .tiff files
        smt.io.array_to_raster(KslEnv.large_working.joinpath('UNbacked', 'Fut', f'obs_loc_dist1.tiff'), distance_grid_nearest_site, no_flow_layer=0)
        smt.io.array_to_raster(KslEnv.large_working.joinpath('UNbacked', 'Fut', f'obs_loc_dist_10_sites.tiff'), distance_grid_nearest_10_sites, no_flow_layer=0)

    else:
        pass


def load_training_data():
    wd = pd.read_hdf(groundwater_data.joinpath('final_water_data.hdf'), 'wl_store_key')
    md = pd.read_hdf(groundwater_data.joinpath('final_metadata.hdf'), 'metadata')
    return {'wd': wd, 'md': md}

def find_min_distance_to_target(grid, target, mask):
    """
    This function finds the minimum distance from each cell in a 2D grid to a target cell. It uses a Breadth-First Search (BFS) algorithm to traverse the grid.

    Parameters:
    grid (numpy.ndarray): A 2D numpy array representing the grid. The value in each cell represents the cumulative sum of sites in that cell.
    target (int): The target cumulative sum of sites. The function will stop BFS when this target is reached or exceeded.
    mask (numpy.ndarray): A 2D numpy array of the same shape as grid. It represents a mask for the grid where True indicates the cell is included in the BFS and False indicates it is not.

    Returns:
    result (numpy.ndarray): A 2D numpy array of the same shape as grid. Each cell contains the minimum distance to a cell in grid where the cumulative sum of sites meets or exceeds the target.
    """

    nrows, ncols = grid.shape
    directions = [
        (0, 1),  (1, 0),  (0, -1), (-1, 0),  # Right, Down, Left, Up
        (1, 1),  (1, -1), (-1, -1), (-1, 1)  # Diagonal movements
    ]
    result = np.full_like(grid, np.inf)  # Initialize result grid with infinity for unreached

    # Helper function to perform BFS from a given cell
    def bfs(r, c):
        queue = deque([(r, c, 0, grid[r][c])])  # row, col, distance, cumulative sum
        visited = set([(r, c)])

        while queue:
            cr, cc, dist, cum_sum = queue.popleft()

            # Check if the cumulative sum meets or exceeds the target
            if cum_sum >= target:
                return dist

            # Explore the possible directions
            for dr, dc in directions:
                nr, nc = cr + dr, cc + dc
                if 0 <= nr < nrows and 0 <= nc < ncols and (nr, nc) not in visited and mask[nr][nc]:
                    visited.add((nr, nc))
                    queue.append((nr, nc, dist + 1, cum_sum + grid[nr][nc]))

        return np.inf  # Return infinity if target is not reached

    # Perform BFS for each cell in the grid that is allowed by the mask and has a positive value
    for r in range(nrows):
        for c in range(ncols):
            if grid[r][c] >= 0 and mask[r][c]:
                result[r][c] = bfs(r, c)
            else:
                result[r][c] = -1  # For cells that are not viable starting points

    return result



temp_smt = RectangularModelTools.modeltools_from_shapefile(shapefile=KslEnv.large_working.joinpath('UNbacked',
                                                                                                   'OLW_predictor_datasets',
                                                                                                   'NZ_hydrogeologicalsystems_June2019',
                                                                                                   'NZ_hydrogeologicalsystem_polygon.shp'),
                                                           delr=1000, delc=1000, layer_type=1, layers=1,

                                                           model_version_name='mf6',
                                                           epsg_num=2193)

def _calc_noflow(recalc=False):
    """
    This function calculates the no-flow areas in the model domain. It checks if a pre-calculated no-flow array exists and loads it if it does.
    If the array does not exist or if recalculation is requested, it calculates the no-flow areas based on a shapefile and saves the result to a .npz file.

    Parameters:
    recalc (bool): A flag indicating whether to recalculate the no-flow areas even if a pre-calculated array exists. Default is False.

    Returns:
    no_flow (numpy.ndarray): A 3D numpy array representing the no-flow areas in the model domain. Each cell in the array is a boolean value indicating whether the corresponding cell in the model domain is a no-flow area.
    """

    save_path = Path('/home/patrick/PycharmProjects/komanawa-nz-depth-to-water/spatial/no_flow.npz')
    if not recalc and save_path.exists():
        return np.load(save_path)['no_flow']
    else:
        no_flow_path = '/home/patrick/PycharmProjects/komanawa-nz-depth-to-water/spatial/NZ_hydrogeologicalsystem_polygon.shp'
        # Convert the shapefile to a model array. The 'HS_id' field is used to determine the no-flow areas.
        no_flow = smt.io.shape_file_to_model_array(no_flow_path, 'HS_id', alltouched=True, overlapping_action='first')
        # Convert the model array to a binary array where 1 represents a no-flow area and 0 represents a flow area.
        no_flow = np.where(no_flow >= 1, 1, 0)
        # Convert the binary array to a boolean array.
        no_flow = no_flow.astype(bool)
        # Convert the 2D array to a 3D array.
        no_flow = no_flow[np.newaxis]
        # Save the boolean array to a .npz file.
        np.savez(save_path, no_flow=no_flow)
        return no_flow


smt = RectangularModelTools(llx=temp_smt.llx, lly=temp_smt.lly,
                            rows=temp_smt.rows,
                            cols=temp_smt.cols,
                            model_version_name='mf5',
                            delr=1000, delc=1000,
                            layer_type=1,
                            layers=1,
                            epsg_num=2193,
                            no_flow_calc= _calc_noflow,
                            )


if __name__ == '__main__':
    density_plot_sites(recalc=True)

