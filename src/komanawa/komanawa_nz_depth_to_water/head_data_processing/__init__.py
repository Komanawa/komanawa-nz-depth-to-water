"""
created matt_dumont and edited by P Durney
on: 15/06/23
"""

from komanawa.komanawa_nz_depth_to_water.head_data_processing import data_processing_functions
from komanawa.komanawa_nz_depth_to_water.head_data_processing import merge_rows
from komanawa.komanawa_nz_depth_to_water.head_data_processing.get_clean_akl_data_generic import get_auk_data
from komanawa.komanawa_nz_depth_to_water.head_data_processing.get_clean_bop_generic import get_bop_data
from komanawa.komanawa_nz_depth_to_water.head_data_processing.get_clean_ecan_gwl_data import get_ecan_data
from komanawa.komanawa_nz_depth_to_water.head_data_processing.get_clean_gisborne_data_generic import get_gdc_data
from komanawa.komanawa_nz_depth_to_water.head_data_processing.get_clean_hawkes_bay_data_generic import get_hbrc_data
from komanawa.komanawa_nz_depth_to_water.head_data_processing.get_clean_horizons_data_generic import get_hrc_data
from komanawa.komanawa_nz_depth_to_water.head_data_processing.get_clean_marlborough_data_generic import get_mdc_data
from komanawa.komanawa_nz_depth_to_water.head_data_processing.get_clean_northland_data_generic import get_nrc_data
from komanawa.komanawa_nz_depth_to_water.head_data_processing.get_clean_orc_data_generic import get_orc_data
from komanawa.komanawa_nz_depth_to_water.head_data_processing.get_clean_southland_data_generic import get_src_data
from komanawa.komanawa_nz_depth_to_water.head_data_processing.get_clean_taranaki_data_generic import get_trc_data
from komanawa.komanawa_nz_depth_to_water.head_data_processing.get_clean_tasman_data_generic import get_tdc_data
from komanawa.komanawa_nz_depth_to_water.head_data_processing.get_clean_waikato_data_generic import get_wrc_data
from komanawa.komanawa_nz_depth_to_water.head_data_processing.get_clean_wellington_data_generic import get_gwrc_data
from komanawa.komanawa_nz_depth_to_water.head_data_processing.get_clean_west_coast_data_generic import get_wcrc_data
from komanawa.komanawa_nz_depth_to_water.head_data_processing.nzgd_data import get_nzgd_data



#  todo FOR finalisation:
# confirm Horizons data is in correct units eg rl or dtw

# this has all the todos per councils, + some notes from our meetings the past few months
# V:\Shared drives\Z21009FUT_FutureCoasts\Data\gwl_data\GWL data notes
# this has notes from our code review, where we discuss putting everything into a certain format
# V:\Shared drives\Z21009FUT_FutureCoasts\Data\gwl_data\GWL data code review
# this is the example format we put together during the code review
# V:\Shared drives\Z21009FUT_FutureCoasts\Data\gwl_data\example format

