"""
This Python script : does xxx
created by: Patrick_Durney
on: 1/05/24
"""

import pandas as pd
from komanawa.komanawa_nz_depth_to_water.project_base import project_dir
from tabulate import tabulate


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
    n_sites_series = pd.Series([n_sites], name='n sites')
    n_obs_series = pd.Series([n_obs], name='n obs')
    start_date_series = pd.Series([start_date], name='record start_date')
    start_date_series = start_date_series.dt.date
    end_date_series = pd.Series([end_date], name='record end date')
    end_date_series = end_date_series.dt.date
    n_obs_per_site_series = pd.Series([n_obs_per_site], name='average n obs per site')
    n_sites_one_obs_series = pd.Series([n_sites_one_obs], name='n sites with only one obs')
    n_sites_less_than_10_obs_series = pd.Series([n_sites_less_than_10_obs], name='n sites less than 10_obs')

    # Concatenate the series into a DataFrame
    table1 = pd.concat([n_sites_series, n_obs_series, start_date_series, end_date_series, n_obs_per_site_series,
                        n_sites_one_obs_series, n_sites_less_than_10_obs_series], axis=1)
    # transpose the table
    table1 = table1.T


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
    table2= pd.concat([n_bores_per_council, start_date_per_council, end_date_per_council, n_obs_per_council,
                       n_obs_per_site_per_council, n_sites_more_than_one_per_council], axis=1)  # Concatenate the series into a DataFrame


    table2.columns = ['n bores ', 'record start date', 'record end date', 'n obs',
                        'average n obs per site', 'n sites more than one observation']
    table2['record start date'] = table2['record start date'].dt.date
    table2['record end date'] = table2['record end date'].dt.date
    # Function to write DataFrame as reST table

    return table1, table2

def write_rst_table_with_tabulate(df, file_path, title="Summary of Metadata"):
    # Generate the table in rst format using tabulate
    table = tabulate(df, headers='keys', tablefmt='rst')

    with open(file_path, 'w') as file:
        file.write(f".. _{title}:\n\n")
        file.write(f".. rubric:: {title}\n\n")
        file.write(table)

def _check_data():
    '''this function is to check the data make sense'''
    # subset the wd for nzgd source
    nzgd = wd[wd.source == 'nzgd']
    # get the meta data
    nzgd_md = md[md.source == 'nzgd']



if __name__ == '__main__':
    wd, md = load_data()
    table1, table2 = get_data_stats(wd, md)
    # Write table1 and table2 as .rst tables
    write_rst_table_with_tabulate(table1, project_dir.joinpath('Data', 'table1.rst'))
    write_rst_table_with_tabulate(table2, project_dir.joinpath('Data', 'table2.rst'))
    raise NotImplementedError



