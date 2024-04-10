"""
This Python script : combines all the processed data from the previous indiviual
databases into a single database for each of data and metadata.
created by: Patrick_Durney
on: 26/02/24
"""

import numpy as np
import pandas as pd
try:
    from komanawa.ksl_tools.spatial.lidar_support import get_best_elv
except ImportError:
    from komanawa.komanawa_nz_depth_to_water.dummy_packages import get_best_elv

from komanawa.komanawa_nz_depth_to_water.head_data_processing import get_bop_data, get_auk_data, get_ecan_data, get_gdc_data, get_hbrc_data, \
    get_hrc_data, get_mdc_data, get_nrc_data, get_orc_data, get_src_data, get_trc_data, get_tdc_data, get_wrc_data, \
    get_gwrc_data, get_wcrc_data, get_nzgd_data, data_processing_functions
from komanawa.komanawa_nz_depth_to_water.project_base import project_dir

def build_final_meta_data(recalc=False):
    meta_data_store_path = project_dir.joinpath('Data/gwl_data/final_meta_data.hdf')
    store_key_metadata = 'meta_and_elv'

    # Check if data needs to be recalculated or if the HDF files don't exist
    if not recalc and meta_data_store_path.exists():
        print("Loading metadata from HDF file.")
        metadata = pd.read_hdf(meta_data_store_path, store_key_metadata)
        elevation = pd.read_hdf(meta_data_store_path, 'elv')
    else:
        print("Recalculating metadata.")
        bop = get_bop_data(recalc=False, redownload=False)
        auk = get_auk_data(recalc=False, redownload=False)
        gdc = get_gdc_data(recalc=False, redownload=False)
        hbrc = get_hbrc_data(recalc=False, redownload=False)
        hrc = get_hrc_data(recalc=False, redownload=False)
        mdc = get_mdc_data(recalc=False, redownload=False)
        nrc = get_nrc_data(recalc=False, redownload=False)
        orc = get_orc_data(recalc=False, redownload=False)
        src = get_src_data(recalc=False, redownload=False)
        trc = get_trc_data(recalc=False, redownload=False)
        tdc = get_tdc_data(recalc=True, redownload=False)
        wrc = get_wrc_data(recalc=False)
        gwrc = get_gwrc_data(recalc=False, redownload=False)
        wcrc = get_wcrc_data(recalc=False, redownload=False)
        nzgd = get_nzgd_data(recalc=False, redownload=False)
        ecan = get_ecan_data(recalc=False)

        bop = bop['combined_metadata']
        auk = auk['combined_metadata']
        gdc = gdc['combined_metadata']
        hbrc = hbrc['combined_metadata']
        hrc = hrc['combined_metadata']
        mdc = mdc['combined_metadata']
        nrc = nrc['combined_metadata']
        orc = orc['combined_metadata']
        src = src['combined_metadata']
        trc = trc['combined_metadata']
        tdc = tdc['combined_metadata']
        wrc = wrc['combined_metadata']
        gwrc = gwrc['combined_metadata']
        wcrc = wcrc['combined_metadata']
        nzgd = nzgd['nzgd_metadata']
        ecan = ecan['combined_metadata']

        bop['source'] = 'bop'
        auk['source'] = 'auk'
        gdc['source'] = 'gdc'
        hbrc['source'] = 'hbrc'
        hrc['source'] = 'hrc'
        mdc['source'] = 'mdc'
        nrc['source'] = 'nrc'
        orc['source'] = 'orc'
        src['source'] = 'src'
        trc['source'] = 'trc'
        tdc['source'] = 'tdc'
        wrc['source'] = 'wrc'
        gwrc['source'] = 'gwrc'
        wcrc['source'] = 'wcrc'
        nzgd['source'] = 'nzgd'
        ecan['source'] = 'ecan'

        # combine all the data into a single dataframe

        metadata = pd.concat([auk, bop, gdc, hbrc, hrc, mdc, nrc, orc, src, trc, tdc, wrc, gwrc, wcrc, nzgd, ecan],
                             axis=0,
                             ignore_index=True)


        elevation, elevation_source, source_mapper = get_best_elv(metadata['nztm_x'], metadata['nztm_y'],
                                                                  fill_with_8m_dem=True)

        df = pd.DataFrame({'dem_elv': elevation, 'dem_source': elevation_source})
        df['source_mapper'] = df['dem_source'].map(source_mapper['survey'])
        df['source_mapper'] = df['source_mapper'].astype(str)
        metadata['dem_elv'] = elevation
        metadata['dem_source'] = elevation_source
        metadata['dem_elv'] = metadata['dem_elv'].astype(float)
        metadata['dem_source'] = metadata['dem_source'].astype(int)
        metadata['source_mapper'] = metadata['dem_source'].map(source_mapper['survey'])
        metadata['source_mapper'] = metadata['source_mapper'].astype(str)

        data_processing_functions.renew_hdf5_store(old_path=meta_data_store_path,
                                                   store_key='elv',
                                                   new_data=df)

        data_processing_functions.renew_hdf5_store(old_path=meta_data_store_path,
                                                   store_key='meta_and_elv',
                                                   new_data=metadata)
    return metadata


def build_final_water_data(recalc=False, recalc_sub=False, redownload=False):
    water_data_store_path = project_dir.joinpath('Data/gwl_data/final_water_data.hdf')
    meta_data_store_path = project_dir.joinpath('Data/gwl_data/final_metadata.hdf')

    if not recalc and water_data_store_path.exists():
        final_gw_data = pd.read_hdf(water_data_store_path, 'wl_store_key')
        metadata_db = pd.read_hdf(meta_data_store_path, 'metadata')
    else:
        metadata_db = build_final_meta_data(recalc=recalc_sub)
        metadata_subset = metadata_db[['well_name', 'rl_elevation', 'dem_elv', 'source', 'dem_source', 'source_mapper',
                                       'dist_mp_to_ground_level']]

        def process_source_data(source_function, source_name, recalc_sub, redownload):
            # Check if the 'redownload' argument is accepted by the source function
            if 'redownload' in source_function.__code__.co_varnames:
                source_data = source_function(recalc=recalc_sub, redownload=redownload)
            else:
                source_data = source_function(recalc=recalc_sub)
            data = source_data['combined_water_data']
            data['source'] = source_name  # Set the 'source' field for each dataset
            data = pd.merge(data, metadata_subset, on=['well_name', 'source'], how='left')
            data['diff'] = data['gw_elevation'] + data['depth_to_water']
            data_group = data[['well_name', 'source', 'diff']].dropna(subset=['diff'])
            mean_diff = data_group.groupby(['well_name', 'source']).mean().reset_index().rename(
                columns={'diff': 'mean_diff'})
            data = pd.merge(data, mean_diff, on=['well_name', 'source'], how='left')

            data['depth_to_water'] = np.where(pd.isnull(data['depth_to_water']) & pd.notnull(data['mean_diff']),
                                              data['mean_diff'] - data['gw_elevation'], data['depth_to_water'])
            data['depth_to_water'] = np.where(pd.isnull(data['depth_to_water']),
                                              data['dem_elv'] - data['gw_elevation'], data['depth_to_water'])
            data['gw_elevation'] = np.where(
                pd.notnull(data['depth_to_water']) & pd.notnull(data['dist_mp_to_ground_level']),
                data['dem_elv'] - data['dist_mp_to_ground_level'] - data['depth_to_water'],
                data['dem_elv'] - data['depth_to_water'])

            data['water_elev_flag'] = np.where(data['water_elev_flag']==0, data['dtw_flag'], data['water_elev_flag'])

            if source_name == 'orc':
                data['gw_elevation'] = np.where(
                    (data['gw_elevation'] - data['dem_elv'] > 50),
                    data['gw_elevation'] - 100,
                    data['gw_elevation']
                )
            # Final Data Adjustments
            # For 'hbrc' dataset, drop rows where 'depth_to_water' > 200
            if source_name == 'hbrc':
                data = data.drop(data[data['depth_to_water'] > 200].index)


            return data.dropna(subset=['depth_to_water'])


        sources = [
            (get_bop_data, 'bop'),
            (get_auk_data, 'auk'),
            (get_gdc_data, 'gdc'),
            (get_hbrc_data, 'hbrc'),
            (get_hrc_data, 'hrc'),
            (get_mdc_data, 'mdc'),
            (get_nrc_data, 'nrc'),
            (get_orc_data, 'orc'),
            (get_src_data, 'src'),
            (get_trc_data, 'trc'),
            (get_tdc_data, 'tdc'),
            (get_wrc_data, 'wrc'),
            (get_gwrc_data, 'gwrc'),
            (get_wcrc_data, 'wcrc'),
            (get_ecan_data, 'ecan'),
            (get_nzgd_data, 'nzgd')
        ]

        processed_data = [process_source_data(source_func, source_name, recalc_sub,
                                              redownload if source_func in [get_hbrc_data, get_hrc_data, get_mdc_data,
                                                                            get_nrc_data, get_orc_data,
                                                                            get_tdc_data] else False) for
                          source_func, source_name in sources]

        gw_data = pd.concat(processed_data, ignore_index=True)
        gw_data['site_name'] = gw_data['well_name'] + '_' + gw_data['source']
        gw_data['depth_to_water_cor'] = np.where(pd.notnull(gw_data['dist_mp_to_ground_level']),
                                                 gw_data['depth_to_water'] - gw_data['dist_mp_to_ground_level'],
                                                 gw_data['depth_to_water'])

          # fix wierdness in the data
        condition = (gw_data['source'] == 'orc') & (gw_data['depth_to_water'] <= -10)
        # Using np.where to add 100 to 'depth_to_water' where the condition is True
        gw_data['depth_to_water_cor'] = np.where(condition, gw_data['depth_to_water'] + 100, gw_data['depth_to_water'])
        condition2 = (gw_data['source'] == 'auk') & ((abs(gw_data['depth_to_water_cor'])
                                            - abs(gw_data['depth_to_water'])) > 10)
        gw_data['depth_to_water_cor'] = np.where(condition2, gw_data['depth_to_water'], gw_data['depth_to_water_cor'])
        # General condition for multiple datasets to drop rows where 'dem_source' == -1
        gw_data = gw_data.drop(gw_data[gw_data['dem_source'] == -1].index)
        # keynote dropping gw data if dtw flag is 6 or water_elev is 5
        gw_data = gw_data.drop(gw_data[(gw_data['dtw_flag'] == 6) | (gw_data['water_elev_flag'] == 5)].index)

        # drop gw_levels where depth to water is greater than 300 or less than -50
        gw_data= gw_data.drop(gw_data[(gw_data['depth_to_water'] > 300) | (gw_data['depth_to_water'] < -50)].index)
        gw_data['depth_to_water_old'] = gw_data['depth_to_water']
        gw_data['depth_to_water'] = gw_data['depth_to_water_cor']
        gw_data['gw_elevation'] = np.where(pd.isnull(gw_data['gw_elevation']),
                                           gw_data['rl_elevation'] - gw_data['depth_to_water'], gw_data['gw_elevation'])

        stats = data_processing_functions._get_summary_stats(gw_data, group_column='site_name')
        metadata_db['site_name'] = metadata_db['well_name'] + '_' + metadata_db['source']
        metadata_db = pd.merge(metadata_db, stats, on='site_name', how='left').drop_duplicates(subset=['site_name'])
        metadata_db['rl_elevation'] = metadata_db['dem_elv'].astype(float)
        metadata_db['rl_datum'] = 'nzvd2016'
        metadata_db['rl_source'] = metadata_db['source_mapper']
        metadata_db['ground_level_datum'] = 'nzvd2016'

        needed_columns = data_processing_functions.needed_cols_and_types('Ecan')['needed_columns']
        metadata_db = metadata_db[
            [col for col in metadata_db.columns if col in needed_columns or col in ['other', 'source', 'site_name']]]
        metadata_db = metadata_db.dropna(subset=['well_name', 'nztm_x', 'nztm_y'])

        final_gw_data = gw_data[
            ['well_name', 'date', 'site_name', 'depth_to_water_cor', 'depth_to_water', 'gw_elevation', 'dtw_flag',
             'source',
             'water_elev_flag']]
        data_processing_functions.renew_hdf5_store(old_path=meta_data_store_path, store_key='metadata',
                                                   new_data=metadata_db)
        data_processing_functions.renew_hdf5_store(old_path=water_data_store_path, store_key='wl_store_key',
                                                   new_data=final_gw_data)
    return {'final_gw_data': final_gw_data, 'metadata_db': metadata_db}


def check_repaired_function():
    wd_orig = pd.read_hdf(project_dir.joinpath('Data/gwl_data/final_water_data.hdf'), 'wl_store_key')
    wd_test = pd.read_hdf(project_dir.joinpath('Data/gwl_data/final_water_data_test.hdf'), 'wl_store_key')
    md_orig = pd.read_hdf(project_dir.joinpath('Data/gwl_data/final_metadata.hdf'), 'metadata')
    md_test = pd.read_hdf(project_dir.joinpath('Data/gwl_data/final_metadata_test.hdf'), 'metadata')


if __name__ == '__main__':
    #build_final_meta_data(recalc=True)
    build_final_water_data(recalc_sub=False, recalc=True)
