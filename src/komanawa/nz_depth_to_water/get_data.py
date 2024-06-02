"""
created matt_dumont 
on: 7/05/24
"""
from pathlib import Path
from copy import deepcopy
import numpy as np
import pandas as pd

md_convert_cols = dict(bottom_bottomscreen=3,
                       dist_mp_to_ground_level=3,
                       nztm_x=1,
                       nztm_y=1,
                       rl_elevation=3,
                       top_topscreen=3,
                       well_depth=3,
                       reading_count=1,
                       mean_dtw=3,
                       median_dtw=3,
                       std_dtw=3,
                       max_dtw=3,
                       min_dtw=3,
                       mean_gwl=3,
                       median_gwl=3,
                       std_gwl=3,
                       max_gwl=3,
                       min_gwl=3,
                       )
wld_convert_cols = dict(depth_to_water_cor=3, depth_to_water=3, gw_elevation=3)
int_mapper_cols = ('well_name', 'site_name', 'source', 'rl_source', 'ground_level_datum', 'rl_datum')


def _convert_to_intmapper(wl_data, metadata, ):
    mappers = {}
    for col in int_mapper_cols:
        temp = set()
        if col in wl_data.columns:
            temp.update(set(wl_data[col].unique()))
        if col in metadata.columns:
            temp.update(set(metadata[col].unique()))
        assert len(temp) <= 4294967295, f'{col} has too many unique values'
        invert_mapper = pd.Series({nm: i for i, nm in enumerate(temp)})
        mapper = pd.Series({i: nm for i, nm in enumerate(temp)})
        mappers[col] = mapper
        if col in wl_data.columns:
            wl_data[col] = invert_mapper.loc[wl_data[col]].astype(np.uint32).values
        if col in metadata.columns:
            metadata[col] = invert_mapper.loc[metadata[col]].astype(np.uint32).values
    return wl_data, metadata, mappers


def _convert_from_intmapper(wl_data, metadata, mappers):
    for col, mapper in mappers.items():
        if col in wl_data.columns:
            wl_data[col] = mapper.loc[wl_data[col]].values
        if col in metadata.columns:
            metadata[col] = mapper.loc[metadata[col]].values
    return wl_data, metadata


def _convert_from_raw_to_int(data, precision):
    """
    Convert the data to integers with the given precision.
    :param data: pd.series, the data to convert.
    :param precision: int, the number of decimal places to keep.
    :return: pd.DataFrame, the converted data.
    """
    out = deepcopy(data)
    out = (out * 10 ** precision).round()
    out[np.isnan(out)] = -9999999
    out[np.isinf(out) & (out < 0)] = -9899999
    out[np.isinf(out) & (out > 0)] = -9799999
    out = out.astype(np.int32)
    return out


def _convert_from_int_to_raw(data, precision):
    """
    Convert the data from integers to floats.
    :param data: pd.series, the data to convert.
    :param precision: int, the number of decimal places to keep.
    :return: pd.DataFrame, the converted data.
    """
    out = deepcopy(data)
    out = out.astype(np.float32)
    out[out == -9999999] = np.nan
    out[out == -9899999] = -np.inf
    out[out == -9799999] = np.inf
    out = out / 10 ** precision
    return out


def get_nz_depth_to_water():
    """
    load the depth to water data and metadata and return them as pandas DataFrames.

    :return: water_level_data, metadata
    """

    datadir = Path(__file__).parent.joinpath('data')
    assert datadir.exists(), f'{datadir} does not exist. should not get here'
    wl_paths = datadir.glob('depth_to_water_*.hdf')
    water_level_data = []
    for wl_path in wl_paths:
        water_level_data.append(pd.read_hdf(wl_path, key='depth_to_water'))
    water_level_data = pd.concat(water_level_data).reset_index(drop=True)
    metadata = pd.read_hdf(datadir.joinpath('metadata.hdf'), key='metadata')
    mappers = {}
    for col in int_mapper_cols:
        mapper_path = datadir.joinpath(f'int_mapper_{col}.hdf')
        mappers[col] = pd.read_hdf(mapper_path, key=col)

    # undo the integer mapping
    water_level_data, metadata = _convert_from_intmapper(water_level_data, metadata, mappers=mappers)

    # undo the integer conversion
    for col, precision in wld_convert_cols.items():
        water_level_data[col] = _convert_from_int_to_raw(water_level_data[col], precision)
    for col, precision in md_convert_cols.items():
        metadata[col] = _convert_from_int_to_raw(metadata[col], precision)
    return water_level_data, metadata


def export_dtw_to_csv(outdir):
    """
    Export the depth to water data to csv files.

    :return:
    """
    water_level_data, metadata = get_nz_depth_to_water()
    outdir = Path(outdir)
    outdir.mkdir(exist_ok=True)
    water_level_data.to_csv(outdir.joinpath('water_level_data.csv'))
    metadata.to_csv(outdir.joinpath('metadata.csv'))
    print(f'Exported data to {outdir}')
