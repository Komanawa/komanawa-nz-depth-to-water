"""
created matt_dumont 
on: 22/06/23
"""


def get_final_ecan_data():

    # get clenaed datasets
    clean_metadata = _get_clean_metadata()
    clean_gwl = _get_clean_gwl()

    # add summary stats to metadata

    # export
    return clean_metadata, clean_gwl

def _get_clean_metadata():
    _get_raw_metadata()
    # cleaning

    raise NotImplementedError

def _get_clean_gwl():
    _get_raw_gwl()
    # cleaning
    raise NotImplementedError

def _get_raw_gwl():

    raise NotImplementedError

def _get_raw_metadata():

    raise NotImplementedError

