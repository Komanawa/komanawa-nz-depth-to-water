"""
created matt_dumont 
on: 7/15/24
"""
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt


class DensityGrid():
    shape = (1476, 1003)
    grid_space = 1000  # km scale
    ulx = 1089955.1968999996
    uly = 6223863.661699999
    data_path = Path(__file__).parent.joinpath('data', 'model_grid.npz')
    distlims = (1000, 5000, 10000, 20000)
    npoints = (1, 10)

    def __init__(self):
        pass

    def export_density_to_tif(self, array, path):
        from osgeo import gdal, osr
        array = array.copy()
        path = str(path)
        null_val = -999999

        if array.shape != (self.shape):
            raise ValueError('array must match model 2d grid shape')
        nans = self.get_nan_layer()
        array[nans] = null_val
        output_raster = gdal.GetDriverByName('GTiff').Create(path, array.shape[1], array.shape[0], 1,
                                                             gdal.GDT_Float32)  # Open the file
        geotransform = (self.ulx, self.grid_space, 0, self.uly, 0, -self.grid_space)
        output_raster.SetGeoTransform(geotransform)  # Specify its coordinates
        srs = osr.SpatialReference()  # Establish its coordinate encoding
        srs.ImportFromEPSG(2193)  # set the georefernce to NZTM
        output_raster.SetProjection(srs.ExportToWkt())  # Exports the coordinate system
        # to the file
        band = output_raster.GetRasterBand(1)
        band.WriteArray(array)  # Writes my array to the raster
        band.FlushCache()
        band.SetNoDataValue(null_val)

    def get_nan_layer(self):
        t = np.load(self.data_path)
        t = t['ibound']
        t = ~t.astype(bool)
        return t

    def get_xy(self):
        t = np.load(self.data_path)
        return t['mx'], t['my']

    def plot_density(self, array, island, vmin, vmax, cbarlab, cmap='magma_r', log=False):
        import cartopy.crs as ccrs
        import cartopy.io.img_tiles as cimgt
        array = array.copy()
        if island == 'both':
            zoom_level = 7
            ymin, ymax, xmin, xmax = -46.7, -34.3, 166.4, 178.6
        elif island == 'n':
            zoom_level = 8
            ymin, ymax, xmin, xmax = -41.7, -34.3, 172.6, 178.6
        elif island == 's':
            zoom_level = 8
            ymin, ymax, xmin, xmax = -46.7, -40.5, 166.4, 174.25
        else:
            raise ValueError('island must be one of n, s, or both')

        request = cimgt.OSM()
        fig, (ax) = plt.subplots(nrows=1, figsize=(8.3 * 0.9, 11.4 * 0.9),
                                 subplot_kw={'projection': request.crs},
                                 )

        ax.set_extent([xmin, xmax, ymin, ymax])
        ax.add_image(request, zoom_level)
        transform = ccrs.PlateCarree()
        x, y = self.get_xy()
        nans = self.get_nan_layer()
        array[nans] = np.nan

        # this needs to be pcolormesh... contourf can't handle nans...
        use_x = np.concatenate([x - 500, x[:, [-1]] + 500], axis=1)
        use_x = np.concatenate([use_x, use_x[[-1]]], axis=0)
        use_y = np.concatenate([y + 500, y[[-1]] - 500], axis=0)
        use_y = np.concatenate([use_y, use_y[:, [0]]], axis=1)
        import pyproj
        trans = pyproj.Transformer.from_crs('EPSG:2193', 'EPSG:4326', always_xy=True)
        use_shape = use_x.shape
        use_x, use_y = trans.transform(use_x.flatten(), use_y.flatten())
        use_x = use_x.reshape(use_shape)
        use_y = use_y.reshape(use_shape)
        edgecolors = 'face'
        linewidth = 0
        if log:
            non_zero_array = array.copy()
            non_zero_array[array == 0] = 0.1
            zero_array = array.copy()
            zero_array[array != 0] = np.nan
            from matplotlib.colors import LogNorm

            temp = ax.pcolormesh(use_x, use_y, non_zero_array,
                                 transform=transform,
                                 cmap=cmap, norm=LogNorm(vmin, vmax),
                                 alpha=0.5, edgecolors=edgecolors, linewidth=linewidth, antialiased=True
                                 )

        else:
            temp = ax.pcolormesh(use_x, use_y, array,
                                 transform=transform,
                                 cmap=cmap, vmin=vmin, vmax=vmax,
                                 alpha=0.5, edgecolors=edgecolors, linewidth=linewidth, antialiased=True
                                 )

        fig.colorbar(temp, ax=ax, orientation='horizontal', fraction=0.05, pad=0.05,
                     label=cbarlab)
        fig.tight_layout()
        return fig, ax
