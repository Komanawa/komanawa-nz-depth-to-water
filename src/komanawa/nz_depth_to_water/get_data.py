"""
created matt_dumont 
on: 11/30/24
"""
import tempfile
from copy import deepcopy

import numpy as np
import pandas as pd
from pathlib import Path
import shutil
from komanawa.nz_depth_to_water.density_grid import DensityGrid
import netCDF4 as nc


def _get_nc_path(_skiptest=False) -> Path:
    datapath = Path(__file__).parent.joinpath('data', 'nz_depth_to_water.nc')
    if not _skiptest:
        assert datapath.exists(), f'{datapath} does not exist. should not get here'
    return datapath


def get_nc_dataset(to_path=None, rewrite=False) -> Path:
    """
    Get the netcdf dataset for the depth to water data for New Zealand.

    :param to_path: str, optional, the path to save the dataset to. if None then saves to temp directory and returns the dataset path. This behavior prevents overwriting the original data.
    :return: nc.Dataset
    """
    path = _get_nc_path()
    if to_path is None:
        to_path = Path(tempfile.mkdtemp()).joinpath(path.name)
    to_path = Path(to_path)

    if to_path.exists() and not rewrite:
        return to_path
    else:
        to_path.unlink(missing_ok=True)
        shutil.copy(path, to_path)
    return to_path


_meta_keys = ('site_name',
              'rl_source', 'source', 'nztm_x', 'nztm_y', 'reading_count', 'mean_gwl', 'median_gwl', 'std_gwl',
              'max_gwl',
              'min_gwl',
              'well_depth', 'bottom_bottomscreen', 'dist_mp_to_ground_level', 'rl_elevation', 'top_topscreen',
              'mean_dtw',
              'median_dtw', 'std_dtw', 'max_dtw', 'min_dtw', 'start_date', 'end_date')
_wl_keys = (
    'wl_site_name', 'wl_date', 'wl_gw_elevation', 'wl_depth_to_water', 'wl_depth_to_water_cor', 'wl_water_elev_flag',
    'wl_dtw_flag',

)


def _make_metadata_table_from_nc(savepath):
    outstr = []
    t0 = 'Water Level Data column meanings/metadata'
    t2 = 'Metadata column meanings/metadata'
    for t, keys in zip((t0, t2), (_wl_keys, _meta_keys)):
        outstr.append(t)
        outstr.append('=' * len(t))
        outstr.append('')
        outstr.append('')
        with nc.Dataset(_get_nc_path(), 'r') as ds:
            for k in keys:
                outstr.append(f'* {k}')
                for attr in ds[k].ncattrs():
                    if attr == 'flag_values':
                        outstr.append(f'    * {attr}:')
                        flag_meanings = ds[k].flag_meanings.split(' ')
                        flag_values = ds[k].flag_values
                        assert len(flag_meanings) == len(
                            flag_values), f'{k} flag values and meanings are not the same length'
                        for i, v in enumerate(ds[k].flag_values):
                            outstr.append(f'        * {v}: {flag_meanings[i]}')

                    elif attr == 'flag_meanings':
                        pass
                    else:
                        outstr.append(f'    * {attr}: {ds[k].getncattr(attr)}')
                outstr.append('')
        outstr.append('')
        outstr.append('')

    outstr = '\n'.join(outstr)
    with open(savepath, 'w') as f:
        f.write(outstr)


def get_metdata_keys() -> list:
    """
    Get the metadata keys for the depth to water data for New Zealand.

    :return: list, the metadata keys.
    """
    return list(_meta_keys)


def get_water_level_keys() -> list:
    """
    Get the water level keys for the depth to water data for New Zealand.

    :return: list, the water level keys.
    """
    return list(_wl_keys)


def get_metadata_string(key) -> str:
    """
    Get the metadata string for a key.

    :param key: str, the key to get the metadata string for. or None (dataset metadata)
    :return: str, the metadata string.
    """
    with nc.Dataset(get_nc_dataset(), 'r') as ds:
        if key is not None:
            assert key in ds.variables, f'{key} not in {ds.variables.keys()}'
            return ds[key].__str__()
        else:
            return ds.__str__()


def nz_depth_to_water_dump() -> str:
    """
    Get the metadata string for the depth to water data for New Zealand. equivalent to ncDump

    :return: str, the metadata string.
    """
    out_str = []
    with nc.Dataset(get_nc_dataset(), 'r') as ds:
        out_str.append(ds.__str__())
        for d in ds.dimensions.keys():
            out_str.append(ds.dimensions[d].__str__())
        for key in ds.variables.keys():
            out_str.append(ds[key].__str__())
    return '\n\n'.join(out_str)

acceptable_sources = (
    'auk', 'bop', 'gdc', 'hbrc', 'hrc', 'mdc', 'nrc', 'ncc', 'orc', 'src', 'trc', 'tdc', 'wrc', 'gwrc', 'wcrc',
    'nzgd', 'tcc', 'ecan')

def get_nz_depth_to_water(source=None, convert_wl_dtw_flag=False, wl_water_elev_flag=False) -> (
        pd.DataFrame, pd.DataFrame):
    """
    Get the depth to water data for New Zealand.

    acceptable_sources = (None, 'auk', 'bop', 'gdc', 'hbrc', 'hrc', 'mdc', 'nrc', 'ncc', 'orc', 'src', 'trc', 'tdc', 'wc', 'gwrc', 'wcrc', 'nzgd', 'ecan')

    :param source: None (get all data), str (get data from a specific source)
    :return: metadata: pd.DataFrame, water_level_data: pd.DataFrame
    """
    with (nc.Dataset(_get_nc_path(), 'r') as ds):
        if source is not None:
            assert source in acceptable_sources, f'{source} not in {acceptable_sources}'
            source_mapper = {v: k for k, v in zip(ds['source'].flag_values, ds['source'].flag_meanings.split(' '))}
            meta_index = np.where(ds.variables['source'][:] == source_mapper[source])[0]
            assert len(meta_index) == len(set(meta_index)), 'duplicate meta index'
            reading_index = np.where(np.isin(ds['wl_site_name'][:], meta_index))[0]
            assert len(reading_index) == len(set(reading_index)), 'duplicate reading index'
        else:
            meta_index = np.arange(ds.dimensions['site'].size)
            reading_index = np.arange(ds.dimensions['reading'].size)
        outmetadata = pd.DataFrame(index=meta_index, columns=_meta_keys)
        out_water_level_data = pd.DataFrame(index=reading_index, columns=_wl_keys)
        for keyset, outdf, use_index in zip((_meta_keys, _wl_keys), (outmetadata, out_water_level_data),
                                            (meta_index, reading_index)):
            pass

            for k in keyset:
                if k == 'wl_site_name':
                    all_sites = np.array(ds['site_name'][:])
                    outdf[k] = all_sites[np.array(ds['wl_site_name'][use_index]).astype(int)]
                elif hasattr(ds[k], 'flag_values'):
                    skip_possible_convert = (
                            (k == 'wl_dtw_flag' and not convert_wl_dtw_flag)
                            or (k == 'wl_water_elev_flag' and not wl_water_elev_flag))
                    if skip_possible_convert:
                        td = np.array(ds[k][use_index])
                    else:
                        mapper = {k: v for k, v in zip(ds[k].flag_values, ds[k].flag_meanings.split(' '))}
                        td = [mapper[v] for v in ds[k][use_index]]
                    outdf[k] = td

                elif 'days since' in ds[k].units:
                    temp = np.array(ds[k][use_index]).astype(float)
                    temp[np.isclose(temp, ds[k].missing_value)] = np.nan
                    idx = np.isfinite(temp)
                    out = np.full(temp.shape, pd.NaT)
                    out[idx] = pd.to_datetime(ds[k].origin) + pd.to_timedelta(deepcopy(temp[idx]), unit='D')
                    outdf[k] = out
                else:
                    ds[k].set_auto_scale(False)
                    outdf[k] = np.array(ds[k][use_index])
                    if k in ['nztm_x', 'nztm_y', 'reading_count']:
                        outdf[k] = outdf[k].astype(int)
                    elif k not in ['site_name']:
                        outdf.loc[np.isclose(outdf[k], ds[k].missing_value), k] = np.nan
                        outdf[k] *= ds[k].scale_factor + ds[k].add_offset
    outmetadata['site_name'] = outmetadata['site_name'].astype(str)
    outmetadata = outmetadata.set_index('site_name',drop=True)
    return outmetadata, out_water_level_data,


def export_dtw_to_csv(outdir, source=None):
    """
    Export the depth to water data to csv files.

    :param outdir: str, the directory to save the csv files to.
    :param source: None (get all data), str (get data from a specific source) see get_nz_depth_to_water for acceptable sources.
    :return:
    """
    print(f'Preparing to export data to csvs in {outdir}')
    metadata, water_level_data = get_nz_depth_to_water(source)
    outdir = Path(outdir)
    outdir.mkdir(exist_ok=True)
    water_level_data.to_csv(outdir.joinpath('water_level_data.csv'))
    metadata.to_csv(outdir.joinpath('metadata.csv'))
    print(f'Exported data to {outdir}')


def get_npoint_in_radius(distlim) -> (np.ndarray, np.ndarray, np.ndarray):
    """
    Get the number of points within [1000 | 5000 | 10,000 | 20,000] m of each point in the model grid.

    :param distlim: int, the distance limit in meters.
    :return: ndatapoints, mx, my (np.ndarray, np.ndarray, np.ndarray) gridded output
    """

    dg = DensityGrid()
    assert distlim in dg.distlims, f'{distlim} not in {dg.distlims}'
    nans = dg.get_nan_layer()
    mx, my = dg.get_xy()
    data = np.load(dg.data_path.parent.joinpath(f'npoins_nearest_{distlim}.npy'))
    data[nans] = np.nan
    return data, mx, my


def get_distance_to_nearest(npoints) -> (np.ndarray, np.ndarray, np.ndarray):
    """
    Get the distance to the nearest [1|10] points for each point in the model grid.

    :param npoints: int, the number of points to consider.
    :return: distance(m), mx, my (np.ndarray, np.ndarray, np.ndarray) gridded output
    """
    dg = DensityGrid()
    assert npoints in dg.npoints, f'{npoints} not in {dg.npoints}'
    nans = dg.get_nan_layer()
    mx, my = dg.get_xy()
    data = np.load(dg.data_path.parent.joinpath(f'distance_m_to_nearest_{npoints}_data.npy'))
    data[nans] = np.nan
    return data, mx, my


def copy_geotifs(outdir):
    """
    copy the geotifs of distance to nearest [1|10] points and number of points within [1|5|10|20] km to the outdir.

    :param outdir: directory to copy the geotifs to.
    :return:
    """
    outdir = Path(outdir)
    outdir.mkdir(exist_ok=True)
    datadir = Path(__file__).parent.joinpath('data')
    tifs = datadir.glob('*.tif')
    for tif in tifs:
        shutil.copy(tif, outdir.joinpath(tif.name))
    print(f'Copied geotifs to {outdir}')


if __name__ == '__main__':
     meta, wld = get_nz_depth_to_water('gwrc')
     pass
