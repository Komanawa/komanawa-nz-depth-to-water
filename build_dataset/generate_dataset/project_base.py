"""
Template created by matt_dumont
on: 22/03/22
"""
from pathlib import Path
try:
    from komanawa.kslcore import KslEnv
except ImportError:
    from build_dataset.generate_dataset.dummy_packages import KslEnv

project_name = 'Future_Coasts'
proj_root = Path(__file__).parent  # base of git repo
project_dir = KslEnv.shared_drive('Z21009FUT_FutureCoasts')
unbacked_dir = KslEnv.unbacked.joinpath(project_name)
unbacked_dir.mkdir(exist_ok=True)

# also consider adding key directories e.g. my groundwater directories
groundwater_data = project_dir.joinpath('Data', 'gwl_data')
gis_data = project_dir.joinpath('GIS')

