import numpy as np
from greento.green.GreenInterface import Interface

class GreenCopernicus(Interface):
    def __init__(self, copernicus):
        self.copernicus = copernicus
    def get_green_area(self, **kwargs):
        if kwargs is None:
            green_areas = frozenset([10,20, 30])
        else:
            green_areas = kwargs.get('green_areas', frozenset([10, 20, 30]))

        data = self.copernicus['data']
        transform = self.copernicus['transform']
        copernicus_crs = self.copernicus['crs']
        copernicus_shape = self.copernicus['shape']

        green_mask = np.isin(data, list(green_areas))
        raster = np.zeros_like(data, dtype=np.uint8)
        raster[green_mask] = 1

        result = {
            "data": raster,
            "transform": transform,
            "crs": copernicus_crs,
            "shape": copernicus_shape
        }
        return result