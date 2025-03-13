import numpy as np
import json
from .UtilsInterface import UtilsInterface
class LandUtilsCopernicus(UtilsInterface):
    def __init__(self, copernicus, osm_green):
        self.copernicus = copernicus
        self.osm_green = osm_green

    def get_land_use_percentages(self):
        data = self.copernicus
        labels = {
            10: "Forest and trees",
            20: "Shrubs",
            30: "Grassland",
            40: "Cropland",
            50: "Buildings",
            60: "Sparse vegetation",
            70: "Snow and Ice",
            80: "Permanent water bodies",
            90: "Herbaceous wetland",
            95: "Mangroves",
            100: "Moss and lichen"
        }
        values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100]
        unique, counts = np.unique(data, return_counts=True)
        land_use_types = dict(zip(unique, counts))
        total = sum(land_use_types.values())
        percentages = {labels.get(land_use, land_use): round((count / total) * 100, 4) for land_use, count in
                       land_use_types.items() if land_use in values}

        return json.dumps(percentages)

    def _filter_copernicus_with_osm(self, copernicus_green):
        copernicus_data = copernicus_green['data']
        osm_data = self.osm_green['data']

        if copernicus_data.shape != osm_data.shape:
            raise ValueError("Raster shapes do not match")

        # Select only the pixels that are green in both rasters
        filtered_data = np.where((osm_data == 1) & (copernicus_data == 1), 1, 0)

        filtered_raster = {
            'data': filtered_data,
            'transform': copernicus_green['transform'],
            'crs': copernicus_green['crs'],
            'shape':copernicus_green['shape']
        }

        return filtered_raster

    def get_green_area(self, **kwargs):
        if kwargs is None:
            green_areas = frozenset([10, 20, 30, 60, 95, 100])
        else:
            green_areas = kwargs.get('green_areas', frozenset([10, 20, 30, 60, 95, 100]))

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
        filtered_data = self._filter_copernicus_with_osm(result)
        return filtered_data