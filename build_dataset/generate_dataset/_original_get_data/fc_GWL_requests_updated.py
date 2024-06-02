import json
import numpy as np
import pandas as pd
from tethysts import Tethys
try:
    from komanawa.kslcore import KslEnv
except ImportError:
    from build_dataset.generate_dataset.dummy_packages import KslEnv

if __name__ == '__main__':
    outdir = KslEnv.unbacked.joinpath('Z21007_FutureCoasts/Data/tethys_gwl_data')
    outdir.mkdir(exist_ok=True, parents=True)
    ts = Tethys()
    datasets = ts.datasets
    parameters = np.unique([d['parameter'] for d in datasets])
    features = np.unique([d['feature'] for d in datasets])
    owners = np.unique([d['owner'] for d in datasets])
    # keynote debug to here to see the name of the owners and parameters
    product_codes = np.unique([d['product_code'] for d in datasets])
    org_datasets = [d for d in datasets if
                    (d['parameter'] in ['groundwater_depth', 'water_level']) and
                    (d['feature'] == 'groundwater') and
                    (d['product_code'] == 'quality_controlled_data') and
                    (d['frequency_interval'] != '1H')
                    ]
    print(len(org_datasets))
    for d in org_datasets:
        owner = d['owner']
        p = d['parameter']
        did = d['dataset_id']
        freq = d['frequency_interval']

        use_outdir = outdir.joinpath(f'{owner}_{p}_{freq}_{did}')
        if use_outdir.exists():
            continue
        data_dir = use_outdir.joinpath('data')
        use_outdir.mkdir(exist_ok=True)
        data_dir.mkdir(exist_ok=True)
        with use_outdir.joinpath('dataset_info.json').open('w') as f:
            json.dump(d, f)
        print(f'{owner}_{p}_{freq}_{did}')
        print(d)
        print('-----' * 10)
        all_stations = ts.get_stations(dataset_id=did)
        stations = [s['station_id'] for s in all_stations]

        # export station data
        # change from date & to date as required
        outdata = pd.DataFrame()
        outdata.index.name = 'tethys_station_id'
        for fs in all_stations:
            try:
                site_name = fs['properties']['alt_name']['data']
            except KeyError:
                site_name = fs['ref']
            site_name = str(site_name).replace('/', '_')
            idx = fs['station_id']
            outdata.loc[idx, 'from_date'] = fs['time_range']['from_date']
            outdata.loc[idx, 'to_date'] = fs['time_range']['to_date']
            outdata.loc[idx, 'num_samp'] = fs['dimensions']['time']
            outdata.loc[idx, 'lat'] = fs['geometry']['coordinates'][1]
            outdata.loc[idx, 'lon'] = fs['geometry']['coordinates'][0]
            outdata.loc[idx, 'site_name'] = site_name
            outdata.loc[idx, 'altitude'] = fs.get('altitude', np.nan)
        for s, fs in zip(stations, all_stations):
            try:
                temp = ts.get_results(
                    dataset_id=did,
                    station_ids=s,
                    squeeze_dims=True
                )
                t = temp.to_dataframe().drop(columns=['geometry', 'height', 'modified_date', 'station_id',
                                                      ])
                outdata.loc[s, 'download'] = True

                try:
                    site_name = fs['properties']['alt_name']['data']
                except KeyError:
                    site_name = fs['ref']
                site_name = site_name.replace('/', '_')

                outpath = data_dir.joinpath(f'{s}_{site_name}_data.csv')
                with open(outpath, 'w') as f:
                    f.write(str(fs) + '\n')
                t.to_csv(outpath, mode='a')
                pass
            except Exception as e:
                outdata.loc[s, 'download'] = False
                outdata.loc[s, 'error'] = str(e)
                continue

        outdata.to_csv(use_outdir.joinpath(f'0_all_stations.csv'))
