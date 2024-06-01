"""
This Python script : does xxx
created by: Patrick_Durney
on: 1/05/24
"""
import itertools

import pandas as pd
from komanawa.nz_depth_to_water.generate_dataset.project_base import project_dir
from tabulate import tabulate
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


def load_data():
    wd = pd.read_hdf(project_dir.joinpath('Data/gwl_data/final_water_data.hdf'), 'wl_store_key')
    md = pd.read_hdf(project_dir.joinpath('Data/gwl_data/final_metadata.hdf'), 'metadata')
    return wd, md


def get_data_stats(wd, md):
    # Get the number of unique sites
    n_sites = len(md['site_name'].unique())
    # get number of observations
    n_obs = len(wd)
    # get start of record
    start_date = wd.date.min()
    # get end of record
    end_date = wd.date.max()
    # get average number of observations per site
    n_obs_per_site = wd.groupby('site_name').size().mean()
    # get number of sites with only one observation
    n_sites_one_obs = (wd.groupby('site_name').size() == 1).sum()
    # get number of sites with less than 10 observations
    n_sites_less_than_10_obs = (wd.groupby('site_name').size() < 10).sum()
    # get average number of observations per site with more than one observation
    n_obs_per_site_more_than_one = wd.groupby('site_name').size()[wd.groupby('site_name').size() > 1].mean()
    # get number of sites with more than one observation
    n_sites_more_than_one = (wd.groupby('site_name').size() > 1).sum()
    # make a pd df of the above first converting all to strings
    # Convert all to pandas Series
    overview_table = pd.Series()
    overview_table.loc['n sites'] = n_sites
    overview_table.loc['n obs.'] = n_obs
    overview_table.loc['start date'] = start_date.date().isoformat()
    overview_table.loc['end date'] = end_date.date().isoformat()
    overview_table.loc['mean n obs./site'] = n_obs_per_site
    overview_table.loc['n sites with only one obs.'] = n_sites_one_obs
    overview_table.loc['n sites < 10 obs.'] = n_sites_less_than_10_obs
    overview_table.name = 'Value'
    overview_table.index.name = 'Metric'
    overview_table.index = overview_table.index.str.capitalize()

    # get number of bores per council
    n_bores_per_council = md.groupby('source')['site_name'].nunique()
    # start of record per council
    start_date_per_council = wd.groupby('source').apply(lambda x: x.date.min())
    # end of record per council
    end_date_per_council = wd.groupby('source').apply(lambda x: x.date.max())
    # get number of observations per council
    n_obs_per_council = wd.groupby('source').size()
    # get average number of observations per site per council
    n_obs_per_site_per_council = wd.groupby('source')['site_name'].value_counts().groupby('source').mean()
    # get number of sites with more than one observation per council
    n_sites_more_than_one_per_council = wd.groupby('source')['site_name'].value_counts().groupby('source').apply(
        lambda x: (x > 1).sum())

    # Concatenate the series into a DataFrame and lable columns with the metric name
    source_summary_table = pd.concat(
        [n_bores_per_council, start_date_per_council, end_date_per_council, n_obs_per_council,
         n_obs_per_site_per_council, n_sites_more_than_one_per_council],
        axis=1)  # Concatenate the series into a DataFrame

    source_summary_table.columns = ['n bores ', 'start date', 'end date', 'n obs.',
                                    'mean n obs./site', 'n sites 1+ obs.']
    source_summary_table['start date'] = source_summary_table['start date'].dt.date
    source_summary_table['end date'] = source_summary_table['end date'].dt.date
    # Function to write DataFrame as reST table

    return overview_table, source_summary_table


def write_rst_table_with_tabulate(df, file_path, title="Summary of Metadata"):
    if isinstance(df, pd.Series):
        df = df.to_frame()
    # Generate the table in rst format using tabulate
    table = tabulate(df, headers='keys', tablefmt='rst',
                     floatfmt=",.2f",
                     intfmt=',d')
    genpath = Path(__file__).relative_to(Path(__file__).parents[4])
    with open(file_path, 'w') as file:
        file.write(f".. table {title} generated from {genpath} :\n\n")
        file.write(f".. rubric:: {title}\n\n")
        file.write(table)


def get_colors(vals, cmap='tab20'):
    n_scens = len(vals)
    if n_scens < 20:
        cmap = plt.get_cmap(cmap)
        colors = [cmap(e / (n_scens + 1)) for e in range(n_scens)]
    else:
        colors = []
        i = 0
        cmap = plt.get_cmap(cmap)
        for v in vals:
            colors.append(cmap(i / 20))
            i += 1
            if i == 20:
                i = 0
    return colors


def _dummy(x):
    return x


def get_running_totals(wd):
    '''
    figure cumulative n_records and n sites vs time (overall and by source)
    Returns:

    '''

    wd['year'] = wd.date.dt.year
    # get the cumulative number of records excluding this date: '1900-01-01 00:00:00'
    wd = wd[(wd.date != '1900-01-01 00:00:00')]

    sources = wd['source'].unique()
    years = list(sorted([y for y in wd['year'].unique() if np.isfinite(y)]))

    sum_by_source = wd.groupby('source').agg({'depth_to_water': 'count'}).reset_index()

    cumulative_n_records = wd.groupby('year').agg({'depth_to_water': 'count'}).cumsum().reset_index()

    # get the cumulative number of sites

    cumulative_n_sites = pd.Series(index=years, data=0, name='site_name')
    cumulative_n_sites.index.name = 'year'
    for y in years:
        cumulative_n_sites.loc[y] = wd[wd['year'] <= y]['site_name'].nunique()

    cumulative_n_sites = cumulative_n_sites.to_frame().reset_index()

    # get the cumulative number of records per source
    n_records_per_source_per_year = wd.groupby(['year', 'source']).agg({'depth_to_water': 'count'})
    for y, s in itertools.product(years, sources):
        if (y, s) not in n_records_per_source_per_year.index:
            n_records_per_source_per_year.loc[(y, s), 'depth_to_water'] = 0
    n_records_per_source_per_year = n_records_per_source_per_year.reset_index()
    n_records_per_source_per_year = n_records_per_source_per_year.sort_values(['source', 'year'])

    cumulitve_sites_by_source = pd.Series(index=pd.MultiIndex.from_product([years, sources], names=['year', 'source']),
                                          data=0, name='unique_sites')
    for y, s in itertools.product(years, sources):
        cumulitve_sites_by_source.loc[(y, s)] = wd[(wd['year'] <= y) & (wd['source'] == s)]['site_name'].nunique()
    cumulitve_sites_by_source = cumulitve_sites_by_source.to_frame().reset_index()

    outfigs = {}
    fig, ax = plt.subplots(figsize=(10, 6))
    # plot the cumulative number of records
    ax.plot(cumulative_n_records['year'], cumulative_n_records['depth_to_water'] * 1e-6, label='Cumulative n records',
            ls='--',
            color='b')
    ax2 = ax.twinx()
    ax2.plot(cumulative_n_sites['year'], cumulative_n_sites['site_name'], label='Cumulative n sites', ls='-', color='r')
    ax.set_xlabel('Year')
    ax.set_ylabel('Cumulative n records (millions)')
    ax2.set_ylabel('Cumulative n sites')
    handles, labels = ax.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(handles + handles2, labels + labels2, loc='upper left')
    ax.set_title('Cumulative number of records and sites')
    fig.tight_layout()
    outfigs['cumulative_n_records'] = fig

    soruces = list(sorted(n_records_per_source_per_year['source'].unique()))
    colors = get_colors(soruces, cmap='tab20')

    fig, ax = plt.subplots(figsize=(10, 6))
    prev = pd.Series(index=n_records_per_source_per_year['year'].unique(), data=0)
    for source, c in zip(soruces, colors):
        source_data = n_records_per_source_per_year[n_records_per_source_per_year['source'] == source]
        source_data = source_data.sort_values('year')
        source_data = source_data.set_index('year')
        ax.fill_between(prev.index, prev, prev + source_data['depth_to_water'].cumsum() * 1e-6, label=f'{source}')
        prev += source_data['depth_to_water'].cumsum() * 1e-6
    ax.set_xlabel('Year')
    ax.set_ylabel('Number of records (millions)')
    ax.set_title('Cumulative number of records per source')
    ax.legend()
    fig.tight_layout()
    outfigs['cumulative_n_records_per_source'] = fig

    fig, ax = plt.subplots(figsize=(10, 6))
    prev = pd.Series(index=years, data=0)
    for source, c in zip(soruces, colors):
        source_data = cumulitve_sites_by_source[cumulitve_sites_by_source['source'] == source]
        source_data = source_data.sort_values('year')
        source_data = source_data.set_index('year')
        ax.fill_between(prev.index, prev, prev + source_data['unique_sites'], label=f'{source}')
        prev += source_data['unique_sites']
    ax.set_xlabel('Year')
    ax.set_ylabel('Number of sites')
    ax.set_title('Cumulative number of sites per source')
    ax.legend()
    fig.tight_layout()
    outfigs['cumulative_n_sites_per_source'] = fig
    return outfigs
