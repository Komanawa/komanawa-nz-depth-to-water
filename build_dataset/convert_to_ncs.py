"""
created matt_dumont 
on: 11/30/24
"""

import netCDF4 as nc
import numpy as np
import pandas as pd
from pathlib import Path
from build_dataset.generate_dataset.head_data_processing.merge_rows import merge_rows_if_possible
from generate_dataset.head_data_processing.flag_mappers import dtw_flag, gwl_flag
from generate_dataset.project_base import proj_root
from komanawa.nz_depth_to_water.get_data_old import get_nz_depth_to_water

base_date = pd.Timestamp('1899-01-01 00:00:00')
time_metadata = {
    'long_name': 'time',
    'units': f'days since {base_date.isoformat()}',
    'missing_value': 0,
    'origin': base_date.isoformat(),
}

complib = 'zlib'
complevel = 9
max_precision = 1


def convert_from_hdf_to_nc(savepath):
    water_level_data, metadata = get_nz_depth_to_water()
    water_level_data['site_name'] = water_level_data['site_name'].str.replace(' ', '')
    metadata['site_name'] = metadata['site_name'].str.replace(' ', '')
    metadata = metadata.set_index('site_name')
    bad_site = metadata.index[~np.isfinite(metadata.nztm_x)]
    metadata = metadata.drop(bad_site)
    duplicated_data = metadata[metadata.index.duplicated(False)]
    data2 = merge_rows_if_possible(duplicated_data.reset_index(), 'site_name', precision={'nztm_x': 1, 'nztm_y': 1})
    data2 = data2[data2.nztm_y > 0]
    assert data2.site_name.is_unique, 'site_name is not unique'
    metadata = metadata[~metadata.index.duplicated(False)]
    metadata = pd.concat([metadata, data2.set_index('site_name')])
    metadata = metadata.sort_index()
    # 28 sites have no rl_elevation - gets null values from 8m dem...
    idx = ~np.isfinite(metadata.rl_elevation)
    metadata = metadata[~idx]
    water_level_data = water_level_data[water_level_data.site_name.isin(metadata.index)]

    water_level_data = water_level_data[water_level_data.site_name.isin(metadata.index)]
    metadata.loc[metadata.reading_count.isna(), 'reading_count'] = 0
    metadata['source'] = metadata['source'].str.replace(' ', '_')
    metadata['rl_source'] = metadata['rl_source'].str.replace(' ', '_')
    water_level_data = water_level_data.drop(columns=[
        'well_name',
        'source',
    ]
    )
    print('wl_data', water_level_data.shape)
    water_level_data['date'] = water_level_data['date'].dt.round('D')
    for k in ['depth_to_water_cor', 'depth_to_water', 'gw_elevation']:
        water_level_data[k] = water_level_data[k].round(max_precision)

    water_level_data = water_level_data.drop_duplicates(['site_name', 'date'])
    print('wl_data rm dups', water_level_data.shape)

    check_dataset(water_level_data, metadata)

    with nc.Dataset(savepath, 'w') as ds:
        make_nc_file(ds, water_level_data, metadata)



def check_dataset(water_level_data, metadata):
    assert metadata.index.is_unique, 'site_name is not unique'
    assert set(metadata.index).issuperset(water_level_data.site_name), 'site_name is not subset of water_level_data'
    metadata_finite_keys = ['nztm_x', 'nztm_y', 'rl_elevation', 'source']
    for key in metadata_finite_keys:
        if key == 'source':
            t = ~pd.notna(metadata[key])
            print(set(metadata[key].unique()))
        else:
            t = (~np.isfinite(metadata[key].astype(float)))
        assert t.sum() == 0, f'{key} has {t.sum()} non-finite values'


    wl_finite_keys = ['site_name', 'depth_to_water_cor',
                      'depth_to_water', 'gw_elevation', 'dtw_flag',
                      'water_elev_flag']
    for key in wl_finite_keys:
        if key == 'site_name':
            assert pd.notna(water_level_data[key]).all(), f'{key} has missing values'
        else:
            t = (~np.isfinite(water_level_data[key].astype(float)))
            assert t.sum() == 0, f'{key} has {t.sum()} non-finite values'

    t = ((water_level_data.date < '1901') & (water_level_data.date > '1899')).sum()
    # keynote  date has 1640 values in 1900... this is suspect
    t = (water_level_data.date < '1899-12-29')
    assert t.sum() == 0, f'date has {t.sum()} values before 1900'


def make_nc_file(ds, wld, metadata):
    assert isinstance(ds, nc.Dataset)

    ds.history = f'created by matt_dumont on {pd.Timestamp.now()}'
    ds.source = str(Path(__file__).relative_to(Path.home()))
    from komanawa.nz_depth_to_water.version import __version__ as version
    ds.format = 'NetCDF-4'
    ds.title = f'New Zealand Groundwater Depth to Water Level Data version: {version}'
    ds.institution = 'Komanawa Solutions Ltd. (https://komanawa.com)'
    ds.contact = 'Matt Dumont (matt@komanawa.com)'
    ds.description = ('This dataset contains groundwater depth to water level data for New Zealand. '
                      'The data is sourced from various providers and has been processed to provide a consistent '
                      'format. The data is provided in a NetCDF format for ease of use and to provide a consistent '
                      'format for use in various applications. The data is provided as is and no warranty is given '
                      'as to its accuracy or completeness. The data is provided under a modified MIT license, '
                      'see (www.https://github.com/Komanawa-Solutions-Ltd/komanawa-nz-depth-to-water) '
                      'for more information.')
    ds.reference = ('Durney P, Charlesworth E, Dumont M. 2024 Developing a National Groundwater Level Dataset, '
                    'New Zealand Journal of Hydrology (accepted)')
    ds.additional_documentation = 'www.https://github.com/Komanawa-Solutions-Ltd/komanawa-nz-depth-to-water'
    ds.funding = ('This work was made possible by Future Coasts Aotearoa (FCA) Funding from the Ministry of '
                  'Business Innovation and Employment (MBIE), managed by the National Institute of Water and '
                  'Atmospheric Research (NIWA), contract C01X2107.')
    ds.license = 'Modified MIT'  # todo add final license...
    ds.datum = 'NZVD2016 (New Zealand Vertical Datum 2016) for all elevation data'
    ds.units = f'meters for all elevation data, days since {base_date.isoformat()} for time data'
    ds.maximum_precision = 10 ** -max_precision

    # create dimensions
    ds.createDimension('site', len(metadata))
    ds.createDimension('reading', len(wld))
    make_nc_metadata_vars(ds, metadata)
    make_nc_wld_vars(ds, wld)


def make_nc_wld_vars(ds, wld):
    assert isinstance(ds, nc.Dataset)

    flag_vars = {
        'wl_site_name': dict(
            df_key='site_name', long_name='site name',
            description='name of the site, the flag values and meanings are enumerate(ds["site_name"][:])',
            mapper={nm: i for i, nm in enumerate(ds['site_name'][:])},
            dtype=np.uint32,
            units='None',
        ),

        'wl_dtw_flag': dict(df_key='dtw_flag', long_name='depth to water quality flag',
                            flag_values=list(dtw_flag().keys()),
                            flag_meanings=' '.join([e.replace(' ', '_') for e in dtw_flag().values()]),
                            mapper=dtw_flag(inverse=True),
                            units='None',
                            ),
        'wl_water_elev_flag': dict(df_key='water_elev_flag', long_name='water elevation quality flag',
                                   flag_values=list(gwl_flag().keys()),
                                   flag_meanings=' '.join([e.replace(' ', '_') for e in gwl_flag().values()]),
                                   mapper=gwl_flag(inverse=True),
                                   units='None',
                                   ),
    }
    for key, md in flag_vars.items():
        mapper = md.pop('mapper')
        org_key = md.pop('df_key')
        usedype = md.pop('dtype', np.uint8)
        assert max(mapper.values()) < np.iinfo(usedype).max, f'{key} has too many unique values: {max(mapper.values())}'
        ds.createVariable(key, usedype, ('reading',), zlib=True, complevel=complevel)
        if key == 'wl_site_name':
            ds[key][:] = [mapper[k] for k in wld[org_key].str.replace(' ', '').values]
        else:
            ds[key][:] = wld[org_key].astype(int)
        ds[key].setncatts(md)

    floal_vars = {
        'wl_depth_to_water_cor': dict(
            df_key='depth_to_water_cor', long_name='depth to water corrected', units='m',
            description='Depth to water from from ground surface e.g. corrected for collar height if available.',
            scale_factor=10 ** -max_precision,
            add_offset=0,
            missing_value=np.iinfo(np.int16).min,
        ),
        'wl_depth_to_water': dict(
            df_key='depth_to_water', long_name='depth to water', units='m',
            description='The depth to water reading at the site on the date provided to either ground level or '
                        'measuring point. Provided by the data provider, otherwise calculated if a groundwater '
                        'elevation was provided.',
            scale_factor=10 ** -max_precision,
            add_offset=0,
            missing_value=np.iinfo(np.int16).min,
        ),
        'wl_gw_elevation': dict(
            df_key='gw_elevation', long_name='ground water elevation', units='m',
            description='The groundwater elevation at the site on the date provided. Provided by the data provider,'
                        ' otherwise calculated if a groundwater depth reading',
            scale_factor=10 ** -max_precision,
            add_offset=0,
            datum='NZVD2016',
            missing_value=np.iinfo(np.int16).min,
        ),
    }
    for key, md in floal_vars.items():
        org_key = md.pop('df_key')
        data = wld[org_key].values / md['scale_factor']
        assert np.nanmin(data) > np.iinfo(np.int16).min, f'{key} has too small values'
        assert np.nanmax(data) < np.iinfo(np.int16).max, f'{key} has too large values'
        data[np.isnan(data)] = md['missing_value']
        ds.createVariable(key, np.int16, ('reading',), zlib=True, complevel=complevel)
        ds[key].set_auto_scale(False)
        ds[key][:] = data
        ds[key].setncatts(md)

    key = 'wl_date'
    org_key = 'date'
    md = time_metadata.copy()
    md['long_name'] = 'water level sampling date'
    md['description'] = ('Note there are significant numbers of observations in 1900, '
                         'this is likely a placeholder date, but we have not converted to NAN as it is unclear')

    data = (pd.to_datetime(wld[org_key]) - base_date).dt.days.values
    assert np.nanmin(data) > 0, f'{key} has negative values'
    data[np.isnan(data)] = 0
    assert data.max() <= np.iinfo(np.uint16).max, f'{key} has too large values'
    assert data.min() >= 0, f'{key} has negative values'
    ds.createVariable(key, np.uint16, ('reading',), zlib=True, complevel=complevel, fill_value=0)
    ds[key][:] = data
    ds[key].setncatts(md)


def make_nc_metadata_vars(ds, metadata):
    assert isinstance(ds, nc.Dataset)
    metadata = metadata.sort_values('site_name')

    # create variables for metadata
    str_vars = {'site_name': dict(
        long_name='name of the site',
        description='A unique identifier for each well, combining the well name and the source provider, '
                    'where the well name is the name provided by the data provider and the source provider is the '
                    'name of the data provider. For example, a well named "well1" from the source "source1" would '
                    'have a site name of "well1_source1".',
        units='None',
    ),

    }
    for key, md in str_vars.items():
        assert key not in ds.variables, f'{key} already exists'
        ds.createVariable(key, str, ('site',))
        ds[key][:] = metadata.reset_index()[key].values
        ds[key].setncatts(md)

    flag_vars = {
        'rl_source': dict(long_name='source of reference level data (if not supplied)',
                          flag_values=1 + np.arange(len(metadata['rl_source'].unique())),
                          flag_meanings=' '.join(metadata['rl_source'].unique()),
                          description='reference level was filled with the best avalible DEM source. A values like '
                                      '"canterbury/selwyn_2023" means the reference level was filled with LIDAR from '
                                      'the canterbury/selwyn survey in 2023 see: https://github.com/linz/elevation. '
                                      'A value of "8m dem" means the reference elevation was filled with https://data.'
                                      'linz.govt.nz/layer/51768-nz-8m-digital-elevation-model-2012/',
                          missing_value=0,
                          units='None',
                          ),
        'source': dict(long_name='source of data', flag_values=np.arange(len(metadata['source'].unique())) + 1,
                       flag_meanings=' '.join([e.replace(' ', '_') for e in metadata['source'].unique()]),
                       missing_value=0, units='None', ),

    }
    for key, md in flag_vars.items():
        fvs = md['flag_values']
        assert max(fvs) < np.iinfo(np.uint8).max, f'{key} has too many unique values: {max(fvs)}'
        fms = md['flag_meanings'].split(' ')
        mapper = {fm: fv for fv, fm in zip(fvs, fms)}
        ds.createVariable(key, np.uint8, ('site',), zlib=True, complevel=complevel, fill_value=0)
        ds[key][:] = [mapper[k] for k in metadata[key].values]
        ds[key].setncatts(md)

    int_vars = {
        'nztm_x': dict(long_name='x coordinate', units='m', epsg=2193),
        'nztm_y': dict(long_name='y coordinate', units='m', epsg=2193),
        'reading_count': dict(long_name='number of readings', units='count'),

    }
    for key, md in int_vars.items():
        assert metadata[key].min() >= 0, f'{key} has negative values'
        assert metadata[key].max() < np.iinfo(np.uint32).max, f'{key} has too many unique values'
        assert metadata[key].isna().sum() == 0, f'{key} has missing values'
        ds.createVariable(key, np.uint32, ('site',), zlib=True, complevel=complevel)
        ds[key][:] = metadata[key].values.astype(np.uint32)
        ds[key].setncatts(md)

    def make_gwl_meta(key):
        out = dict(long_name=f'{key.split("_")[0]} ground water level', units='m', datum='NZVD2016',
                   description='calculated from this dataset for ease of use',
                   scale_factor=10 ** -max_precision,
                   add_offset=0,
                   missing_value=np.iinfo(np.int16).min,
                   )
        return out

    elv_float_vars = {e: make_gwl_meta(e) for e in [
        'mean_gwl',
        'median_gwl',
        'std_gwl',
        'max_gwl',
        'min_gwl',

    ]}
    for key, md in elv_float_vars.items():
        data = metadata[key].astype(float).values / md['scale_factor']
        assert np.nanmin(data) > np.iinfo(np.int16).min, f'{key} has too small values'
        assert np.nanmax(data) < np.iinfo(np.int16).max, f'{key} has too large values'
        data[np.isnan(data)] = np.iinfo(np.int16).min
        ds.createVariable(key, np.int16, ('site',), zlib=True, complevel=complevel)
        ds[key].set_auto_scale(False)
        ds[key][:] = data
        ds[key].setncatts(md)

    other_float_vars = {
        'well_depth': dict(
            long_name='well depth', units='m',
            description='The depth of the well, if known, as provided by the data provider. There is not clarity on '
                        'what this value represents, it may be the depth of the well screen, or the depth of the '
                        'well casing, or the depth of the well itself and it may be from the ground surface, the '
                        'measurement point, or similar',
            scale_factor=10 ** -max_precision,
            add_offset=0,
            missing_value=np.iinfo(np.int32).min,
            dtype=np.int32,
        ),
        'bottom_bottomscreen': dict(
            long_name='bottom of bottom screen', units='m',
            description='The depth of the end of the bottom screen, if known. If there is only one screen in the '
                        'well, the end of screen depth will be recorded in bottom_topscreen. If there is more than '
                        'one screen in the well, this value is the depth at which the last screen ends. '
                        'It is unclear if this value is from the ground surface, the measurement point, or similar.',
            scale_factor=10 ** -max_precision,
            add_offset=0,
            missing_value=np.iinfo(np.int32).min,
            dtype=np.int32,
        ),
        'dist_mp_to_ground_level': dict(
            long_name='distance from measurement point to ground level', units='m',
            description='The distance from the measuring point to the ground surface, if known. If it is 0, the '
                        'measuring point is at the ground surface.',
            scale_factor=10 ** -max_precision,
            add_offset=0,
            missing_value=np.iinfo(np.int16).min,
        ),
        'rl_elevation': dict(
            long_name='reference level elevation', units='m',
            description='The elevation of the reference level, if known.',
            datum='NZVD2016',
            scale_factor=10 ** -max_precision,
            add_offset=0,
            missing_value=np.iinfo(np.int16).min,
        ),
        'top_topscreen': dict(
            long_name='top of top screen', units='m',
            description='The depth of the top of the top screen, if known. If there is only one screen in the well, '
                        'the top of screen depth will be recorded in top_topscreen. If there is more than one screen in '
                        'the well, this value is the depth at which the first screen starts. It is unclear if this value '
                        'is from the ground surface, the measurement point, or similar.',
            scale_factor=10 ** -max_precision,
            add_offset=0,
            missing_value=np.iinfo(np.int32).min,
            dtype=np.int32,
        ), }

    for key, md in other_float_vars.items():
        data = metadata[key].astype(float).values
        data = data / md['scale_factor']
        use_dtype = md.pop('dtype', np.int16)
        assert np.nanmin(data) > np.iinfo(use_dtype).min, f'{key} has too small values'
        assert np.nanmax(data) < np.iinfo(
            use_dtype).max, f'{key} has too large values ({(data > np.iinfo(np.int16).max - 2).sum()}), {np.nanmax(data)}'
        data[np.isnan(data)] = np.iinfo(use_dtype).min
        ds.createVariable(key, use_dtype, ('site',), zlib=True, complevel=complevel)
        ds[key].set_auto_scale(False)
        ds[key][:] = data
        ds[key].setncatts(md)

    def make_dtw_meta(key):
        out = dict(long_name=f'{key.split("_")[0]} depth to ground water level', units='m',
                   description='calculated from this dataset for ease of use',
                   convention='positive values (+) are below the ground surface, negative values (-) are above the ground surface (artesian)',
                   # todo +- convention for dtw, check with PD
                   scale_factor=10 ** -max_precision,
                   add_offset=0,
                   missing_value=np.iinfo(np.int16).min,

                   )
        return out

    dtw_float_vars = {e: make_dtw_meta(e) for e in [
        'mean_dtw',
        'median_dtw',
        'std_dtw',
        'max_dtw',
        'min_dtw',
    ]}
    for key, md in dtw_float_vars.items():
        data = metadata[key].astype(float).values / md['scale_factor']
        assert np.nanmin(data) > np.iinfo(np.int16).min, f'{key} has too small values'
        assert np.nanmax(data) < np.iinfo(np.int16).max, f'{key} has too large values'
        data[np.isnan(data)] = np.iinfo(np.int16).min
        var = ds.createVariable(key, np.int16, ('site',), zlib=True, complevel=complevel)
        var.set_auto_scale(False)

        ds[key][:] = data.astype(np.int16)
        ds[key].setncatts(md)

    kill_vars = [
        'ground_level_datum',
        'rl_datum',
        'well_name',
    ]
    for key in kill_vars:
        assert key not in ds.variables, f'{key} already exists'

    sd_md = time_metadata.copy()
    sd_md['long_name'] = 'start date'
    sd_md['description'] = 'start date of the reading calculated from this dataset for ease of use'
    ed_md = time_metadata.copy()
    ed_md['long_name'] = 'end date'
    ed_md['description'] = 'end date of the reading calculated from this dataset for ease of use'
    time_vars = {
        'start_date': sd_md,
        'end_date': ed_md, }
    for key, md in time_vars.items():
        assert not any(pd.to_datetime(metadata[key]) < base_date), f'{key} has negative values'

        data = (pd.to_datetime(metadata[key]) - base_date).dt.days.values
        assert np.nanmin(data) > 0, f'{key} has negative values'
        data[np.isnan(data)] = 0
        assert data.max() <= np.iinfo(np.uint16).max, f'{key} has too large values'
        assert data.min() >= 0, f'{key} has negative values'
        ds.createVariable(key, np.uint16, ('site',), zlib=True, complevel=complevel, fill_value=0)
        ds[key][:] = data
        ds[key].setncatts(md)


if (__name__ == '__main__'):
    # todo move into repo!!!
    convert_from_hdf_to_nc(Path.home().joinpath('Downloads', 'test_nz_dtw.nc'))
    from komanawa.nz_depth_to_water.get_data import _make_metadata_table_from_nc

    _make_metadata_table_from_nc(proj_root.parents[1].joinpath('docs_build/metadata.rst'))
