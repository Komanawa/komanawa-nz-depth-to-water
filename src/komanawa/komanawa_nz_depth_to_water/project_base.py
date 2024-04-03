"""
Template created by matt_dumont
on: 22/03/22
"""
from pathlib import Path
try:
    from komanawa.kslcore import KslEnv
except ImportError:
    from komanawa.komanawa_nz_depth_to_water.dummy_packages import KslEnv

project_name = 'Future_Coasts'
proj_root = Path(__file__).parent  # base of git repo
project_dir = KslEnv.shared_drive('Z21009FUT_FutureCoasts')
unbacked_dir = KslEnv.unbacked.joinpath(project_name)
unbacked_dir.mkdir(exist_ok=True)

# also consider adding key directories e.g. my groundwater directories
groundwater_data = project_dir.joinpath('Data', 'gwl_data')
amandine_data = project_dir.joinpath('Data', 'ChCh', 'Amandine data', 'ForZeb_May2023')
gis_data = project_dir.joinpath('GIS')
des_resample_dir = project_dir.joinpath('Data', 'des_resample')
# data_dir = project_dir.joinpath("data")
# results_dir = project_dir.joinpath("results")
