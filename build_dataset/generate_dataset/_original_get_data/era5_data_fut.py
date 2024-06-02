"""
created matt_dumont 
on: 14/02/24
"""
"""
created matt_dumont 
on: 12/09/22
"""
import json
import geopandas as gpd
import pandas as pd
from tethysts import Tethys
import numpy as np
from pathlib import Path

if __name__ == '__main__':
    outdir = Path().home().joinpath('Downloads/era5_data')
    outdir.mkdir(exist_ok=True)
    ts = Tethys()
    datasets = ts.datasets
    my_dataset = [d for d in datasets if True
                  and (d['feature'] == 'atmosphere')
                  # and (d['owner'] == 'MET Norway')
                  and (d['method'] == 'simulation')
                  and (d['product_code'] == 'reanalysis-era5-land')
                  and (d['parameter'] in ['potential_et', 'reference_et', 'precipitation'])
                  ]
    for d in my_dataset:
        print(d)

    print(np.unique([e['owner'] for e in my_dataset]))
    print(np.unique([e['product_code'] for e in my_dataset]))
    ds_ids = [e['dataset_id'] for e in my_dataset]
    ps = [e['parameter'] for e in my_dataset]
    stations = []
    for did, p in zip(ds_ids, ps):
        temp = ts.get_stations(did)
        for e in temp:
            e['dataset_id'] = did
            e['parameter'] = p
        stations.extend([e for e in temp if e['time_range']['from_date'] < '1990-01-01'])
    use_stations = {}
    for s in stations:
        sid = s['station_id']
        if sid in use_stations:
            continue
        use_stations[sid] = s

    print(len(use_stations), 'stations')
    print(s)

    # overview data
    outdata = pd.DataFrame(index=use_stations.keys())
    outdata.index.name = 'station_id'
    for s, v in use_stations.items():
        outdata.loc[s, 'from_date'] = v['time_range']['from_date']
        outdata.loc[s, 'to_date'] = v['time_range']['to_date']
        outdata.loc[s, 'lat'] = v['geometry']['coordinates'][1]
        outdata.loc[s, 'lon'] = v['geometry']['coordinates'][0]
    outdata.to_csv(outdir.joinpath('era5_stations.csv'))

    for dsid, p in zip(ds_ids, ps):
        print(p)
        for i, s in enumerate(use_stations):
            if i % 50 == 0:
                print(i, 'of', len(use_stations), f'for {p}')
            temp = ts.get_results(
                dataset_id=dsid,
                station_ids=s,
                from_date='1950-01-01',
                to_date='2023-12-31',
                squeeze_dims=True
            )

            if p == 'precipitation':
                test = temp.resample(time='1D').sum()
            else:
                test = temp.resample(time='1D').mean()
            test.to_netcdf(outdir.joinpath(f'era5_{p}_{s}.nc'))
