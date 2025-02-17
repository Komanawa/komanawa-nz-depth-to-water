import tempfile
import unittest
import netCDF4 as nc
import numpy as np
import pandas as pd
from pathlib import Path

from komanawa.nz_depth_to_water.get_data import get_nz_depth_to_water, get_water_level_keys, get_metdata_keys, \
    get_nc_dataset, get_metadata_string, get_npoint_in_radius, get_distance_to_nearest, export_dtw_to_csv, \
    nz_depth_to_water_dump, copy_geotifs, _get_nc_path, _make_metadata_table_from_nc


class TestKomanawaNzDepthToWater(unittest.TestCase):
    def test_get_keys(self):
        wl_keys = get_water_level_keys()
        meta_keys = get_metdata_keys()
        with nc.Dataset(_get_nc_path(), 'r') as ds:
            ds_keys = list(ds.variables.keys())
        self.assertSetEqual(set(wl_keys + meta_keys), set(ds_keys))

    def test_get_metadata_string(self):
        with nc.Dataset(_get_nc_path(), 'r') as ds:
            for key in get_metdata_keys():
                self.assertEqual(get_metadata_string(key), ds[key].__str__())
            self.assertEqual(get_metadata_string(None), ds.__str__())
        print(get_metadata_string(None))

    def test_nz_depth_to_water_dump(self):
        print(nz_depth_to_water_dump())
        assert len(nz_depth_to_water_dump()) > 1000

    def test_get_ncdataset(self):
        assert get_nc_dataset().exists()
        with tempfile.TemporaryDirectory() as tdir:
            tf = Path(tdir).joinpath('test.nc')
            savepath = get_nc_dataset(tf)
        assert not savepath.exists()

    def test_get_npoin_in_radius(self):
        for d in [1, 5, 10, 20]:
            data, mx, my = get_npoint_in_radius(d * 1000)
            assert np.isfinite(data).mean() > 0.10, f'{np.isfinite(data).mean()}'
            assert np.isfinite(mx).all()
            assert np.isfinite(my).all()

    def test_get_distance_to_nearest(self):
        for d in [1, 10]:
            data, mx, my = get_distance_to_nearest(d)
            assert np.isfinite(data).mean() > 0.10, f'{np.isfinite(data).mean()}'
            assert np.isfinite(mx).all()
            assert np.isfinite(my).all()

    def test_copy_geotifs(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            copy_geotifs(td)
            self.assertEqual(len(list(td.glob('*.tif'))), 6)

    def test_export_dtw_to_csv(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            export_dtw_to_csv(td)
            with nc.Dataset(_get_nc_path(), 'r') as ds:
                nsites = ds.dimensions['site'].size
                nreadings = ds.dimensions['reading'].size
                t = pd.read_csv(td.joinpath('metadata.csv'))
                self.assertEqual(len(t), nsites)
                t = pd.read_csv(td.joinpath('water_level_data.csv'))
                self.assertEqual(len(t), nreadings)

    def test_make_metadata_table_from_nc(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td).joinpath('test.rst')
            _make_metadata_table_from_nc(td)

    def test_get_nz_depth_to_water_full_parts(self):
        part_meta = []
        part_wl = []
        acceptable_sources = (
            'auk', 'bop', 'gdc', 'hbrc', 'hrc', 'mdc', 'nrc', 'ncc', 'orc', 'src', 'trc', 'tdc', 'wrc', 'gwrc', 'wcrc',
            'tcc',
            'nzgd',
            'ecan')
        for ac in acceptable_sources:
            print('reading', ac)
            m, w = get_nz_depth_to_water(ac)
            assert w.duplicated().sum() == 0, w[w.duplicated(keep=False)].to_string()
            assert m.reset_index().duplicated().sum() == 0, f'{ac}, {m[m.reset_index().duplicated(keep=False)].to_string()}'
            part_meta.append(m)
            assert (m['source'] == ac).all(), ac
            part_wl.append(w)
            wl_set = set(w['wl_site_name'])
            meta_set = set(m.index.astype(str).values)
            assert wl_set.issubset(meta_set), f'{ac}: {wl_set.symmetric_difference(meta_set)}'
        part_meta = pd.concat(part_meta)
        part_wl = pd.concat(part_wl)
        meta, wl = get_nz_depth_to_water()
        assert wl.duplicated().sum() == 0, wl[wl.duplicated(keep=False)]
        assert meta.reset_index().duplicated().sum() == 0, meta[meta.reset_index().duplicated(keep=False)]
        meta = meta.sort_index()
        part_meta = part_meta.sort_index()
        wl = wl.set_index(['wl_site_name', 'wl_date']).sort_index()
        part_wl = part_wl.set_index(['wl_site_name', 'wl_date']).sort_index()
        pd.testing.assert_frame_equal(meta, part_meta)
        pd.testing.assert_frame_equal(wl, part_wl)

    def test_get_nz_depth_to_water(self):

        meta, wl = get_nz_depth_to_water()
        meta = meta.sort_index()
        wl['wl_date'] = pd.to_datetime(wl['wl_date']).dt.date
        wl = wl.set_index(['wl_site_name', 'wl_date']).sort_index()

        meta_test_data = pd.read_csv(Path(__file__).parent.joinpath(
            'metadata_spot_check.csv')).set_index('site_name').sort_index()
        meta_test_data = meta_test_data.drop(columns=['rl_datum', 'well_name', 'ground_level_datum'])
        wl_test_data = pd.read_csv(Path(__file__).parent.joinpath(
            'wl_data_spot_check.csv'))
        wl_test_data = wl_test_data.rename(columns={'site_name': 'wl_site_name',
                                                    'date': 'wl_date',
                                                    'gw_elevation': 'wl_gw_elevation',
                                                    'depth_to_water': 'wl_depth_to_water',
                                                    'depth_to_water_cor': 'wl_depth_to_water_cor',
                                                    'dtw_flag': 'wl_dtw_flag',
                                                    'water_elev_flag': 'wl_water_elev_flag'
                                                    })
        wl_test_data = wl_test_data.drop(columns='Unnamed: 0')
        wl_test_data['wl_date'] = pd.to_datetime(wl_test_data['wl_date']).dt.date
        wl_test_data = wl_test_data.set_index(['wl_site_name', 'wl_date']).sort_index()
        self.assertSetEqual(set(meta.columns), set(meta_test_data.columns))
        self.assertSetEqual(set(wl.columns), set(wl_test_data.columns))

        # clean metadata
        no_change = ['rl_source', 'source']
        to_int = ['nztm_x', 'nztm_y', 'reading_count']
        columns = ['mean_gwl', 'median_gwl', 'std_gwl', 'max_gwl', 'min_gwl', 'well_depth',
       'bottom_bottomscreen', 'dist_mp_to_ground_level', 'rl_elevation',
       'top_topscreen', 'mean_dtw', 'median_dtw', 'std_dtw', 'max_dtw',
       'min_dtw']
        to_dt = ['start_date', 'end_date']
        meta_test_data.loc[meta_test_data['reading_count'].isna(), 'reading_count'] = 0
        for col in to_int:
            meta_test_data[col] = meta_test_data[col].astype(int)
        for col in columns:
            meta_test_data[col] = np.floor((pd.to_numeric(meta_test_data[col]) * 10)) / 10

        for col in to_dt:
            meta_test_data[col] = pd.to_datetime(meta_test_data[col])

        for k in ['start_date', 'end_date']:
            pd.testing.assert_series_equal(pd.to_datetime(meta.loc[meta_test_data.index, k]).dt.date,
                                           pd.to_datetime(meta_test_data[k]).dt.date,
                                           check_datetimelike_compat=True)

        meta_test_data = meta_test_data.drop(columns=['start_date', 'end_date'])

        pd.testing.assert_frame_equal(meta.loc[meta_test_data.index, meta_test_data.columns], meta_test_data,
                                      atol=0.11, check_datetimelike_compat=True) # to address rounding errors

        # clean water level data
        got_data = wl.loc[wl_test_data.index, wl_test_data.columns]
        for k in ['wl_gw_elevation', 'wl_depth_to_water', 'wl_depth_to_water_cor']:
            wl_test_data[k] = wl_test_data[k].round(1)
            t = np.isclose(wl_test_data[k], got_data[k], atol=0.11).mean()
            assert t > 0.99, f'{k}, {t=}'
            t = (~np.isclose(wl_test_data[k], got_data[k], atol=0.41))
            assert t.sum()==1, f'{k}, {t.sum()}'
            assert wl_test_data[t].index[0][0] =='M35/1384_ecan'  # one really weird outlier...


        for k, mapper in zip(['wl_dtw_flag', 'wl_water_elev_flag'], [dtw_flag, gwl_flag]):
            wl_test_data[k] = wl_test_data[k].astype(int)
            frac_same = (wl_test_data[k]== got_data[k]).mean()
            assert frac_same>0.90, f'{k} {frac_same}'


def dtw_flag(inverse=False):
    flags = {
        #(int: str)
        0: 'no_data',
        1: 'logger',
        2: 'manual',
        3: 'static_oneoff',
        4: 'calculated from gw_elevation',
        5: 'aquifer test',
        6: 'other'
    }

    assert len(set(flags.values())) == len(flags.values()), 'flags must be unique'
    if inverse:
        flags = {v: k for k, v in flags.items()}
    return flags

def gwl_flag(inverse=False):
    flags = {
        #(int: str)
        0: 'no_data',
        1: 'logger',
        2: 'manual',
        3: 'static_oneoff',
        4: 'aquifer test',
        5: 'other'
    }

    assert len(set(flags.values())) == len(flags.values()), 'flags must be unique'
    if inverse:
        flags = {v: k for k, v in flags.items()}
    return flags


if __name__ == '__main__':
    unittest.main()
