"""
usage:

    python export_to_csv.py [outdir]

outdir: str, optional, the directory to save the csv files to. If not provided, the user's Downloads directory is used.

created matt_dumont
on: 6/2/24
"""
from komanawa.nz_depth_to_water.get_data import export_dtw_to_csv
from pathlib import Path
import sys

if __name__ == '__main__':
    if len(sys.argv) == 1:
        outdir = None
    else:
        outdir = sys.argv[1]
    if outdir is None:
        outdir = Path.home().joinpath('Downloads', 'nz_depth_to_water')
    export_dtw_to_csv(outdir)
