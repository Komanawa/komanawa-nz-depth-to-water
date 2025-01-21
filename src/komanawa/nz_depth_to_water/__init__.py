"""
NZ Depth to Water access module

"""

from komanawa.nz_depth_to_water.version import __version__
from komanawa.nz_depth_to_water.get_data import get_nz_depth_to_water, get_nc_dataset, get_metdata_keys, get_water_level_keys, get_metadata_string, nz_depth_to_water_dump, acceptable_sources, export_dtw_to_csv, get_npoint_in_radius, get_distance_to_nearest, copy_geotifs
