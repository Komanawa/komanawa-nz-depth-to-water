"""
created matt_dumont 
on: 2/11/23
"""
import pandas as pd


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

def add_flags_to_hdf(path):
    flag_funcs = [
        gwl_flag,
        dtw_flag

    ]
    for func in flag_funcs:
        t = pd.Series(func())
        t.to_hdf(path, key=func.__name__, append=True, complevel=9, complib='zlib')

if __name__ == '__main__':
     val = gwl_flag(True)['no_data']
     # todo compressing data example:
     #lake_hds.to_hdf(historical_data_savepath, key='lake', complib='zlib', complevel=9)
