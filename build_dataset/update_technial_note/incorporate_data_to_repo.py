"""
created matt_dumont 
on: 6/2/24
"""
from pathlib import Path
import numpy as np
from komanawa.nz_depth_to_water.get_data import _convert_from_raw_to_int, _convert_to_intmapper, md_convert_cols, \
    wld_convert_cols, get_nz_depth_to_water

datadir = Path(__file__).parents[2].joinpath('src/komanawa/nz_depth_to_water/data')
assert datadir.exists(), f'{datadir} does not exist. should not get here'


def incorporate_data_to_repo(wld, md):
    """
    Incorporate the depth to water data and metadata into the repository.
    :param wld: pd.DataFrame, the depth to water data.
    :param md: pd.DataFrame, the metadata.
    :return:
    """
    wld = wld.copy()
    md = md.copy()
    complib = 'blosc'
    metadata_path = datadir.joinpath('metadata.hdf')
    wl_data, metadata, mappers = _convert_to_intmapper(wld, md)
    for col, mapper in mappers.items():
        mapper_path = datadir.joinpath(f'int_mapper_{col}.hdf')
        mapper.to_hdf(mapper_path, key=col, complib=complib, complevel=9)

    for col, precision in wld_convert_cols.items():
        wl_data[col] = _convert_from_raw_to_int(wl_data[col], precision)
    for col, precision in md_convert_cols.items():
        metadata[col] = _convert_from_raw_to_int(metadata[col], precision)

    for source in wld.source.unique():
        outpath = datadir.joinpath(f'depth_to_water_{source}.hdf')
        wld.loc[wld.source == source].to_hdf(outpath, key='depth_to_water', complib=complib, complevel=9, index=False)
    md.to_hdf(metadata_path, key='metadata', complib=complib, complevel=9, index=False)


def check_new_data(md, wld):
    """
    check if written data is different that saved data
    :param md:
    :param wld:
    :return:
    """

    got_wld, got_md = get_nz_depth_to_water()
    assert set(got_md.columns) == set(md.columns), f'{got_md.columns} != {md.columns}'
    assert set(got_wld.columns) == set(wld.columns), f'{got_wld.columns} != {wld.columns}'
    assert got_md.shape == md.shape, f'{got_md.shape} != {md.shape}'
    assert got_wld.shape == wld.shape, f'{got_wld.shape} != {wld.shape}'
    for col in got_md.columns:
        if col in md_convert_cols:
            assert np.allclose(got_md[col], md[col].round(md_convert_cols[col]),
                               equal_nan=True), f'{col} not equal'
        else:
            assert got_md[col].equals(md[col]), f'{col} not equal'
    got_wld = got_wld.sort_values(['site_name', 'date'])
    wld = wld.sort_values(['site_name', 'date'])
    for col in got_wld.columns:
        if col in wld_convert_cols:
            assert np.allclose(got_wld[col], wld[col].round(wld_convert_cols[col]), equal_nan=True), f'{col} not equal'
        elif col in ['date']:
            got_temp = got_wld[col].values
            temp = wld[col].values
            same = (got_temp == temp) | (np.isnan(temp) & np.isnan(got_temp))
            assert same.all(), f'{col} not equal'
        else:
            assert (got_wld[col].values == wld[col].values).all(), f'{col} not equal'


if __name__ == '__main__':
    import pandas as pd
    from komanawa.kslcore import KslEnv

    project_dir = KslEnv.shared_drive('Z21009FUT_FutureCoasts')
    md = pd.read_hdf(project_dir.joinpath('Data/gwl_data/final_metadata.hdf'), 'metadata')
    md.drop(columns='other', inplace=True)
    wd = pd.read_hdf(project_dir.joinpath('Data/gwl_data/final_water_data.hdf'), 'wl_store_key')
    incorporate_data_to_repo(wd, md)
    check_new_data(md, wd)
