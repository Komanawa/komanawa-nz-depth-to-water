"""
This provides a dummy class to be imported into public repos (copy this file to the public repo)
created matt_dumont
on: 4/04/24
"""
import warnings
from pathlib import Path
import numpy as np

warnings.warn("using dummy packages for paths or lidar access. this may affect results")


class KslEnvrionment(object):
    """
    KslEnv is class to simplify the location of remote drives across multiple platforms, users, and computers. This is a dummy class so that all the path object point to pathlib.Path.home().
    """
    home = Path.home()
    my_drive = Path.home()
    large_archive = Path.home()
    large_working = Path.home()
    tempdrive = Path.home()
    unbacked = Path.home()

    def __init__(self):
        self._unbacked_base = Path.home()

    def shared_drive(self, name):
        """
        get a shared drive

        :param name: name of the shared drive (e.g. TEMP)
        :return:
        """
        return Path.home().joinpath(name)


KslEnv = KslEnvrionment()


def get_best_elv(x: np.ndarray, y: np.ndarray, fill_with_8m_dem=True, verbose=False):
    """
        get the most recent elevation from lidar or, optionally 8m dem where there is no lidar data for a set of nztm x, y points

        :param x: nztm x
        :param y: nztm y
        :param fill_with_8m_dem: bool, if True, fill with 8m dem if no lidar data
        :param verbose: bool, if True, print progress
        :return:

        * elv: np.ndarray elevation,
        * elv_source: np.ndarray index of source (integer),
        * paths_metadata: pd.Dataframe of source index to source name
    """
    warnings.warn("This using a dummy version of get_best_elv, only nans returned.  "
                  "If you want to actually use the values you will need to implement a "
                  "function to read in data from the LINZ lidar store")
    return np.full(x.shape, np.nan)
