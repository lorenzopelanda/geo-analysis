import numpy as np
import json

class LandUseAnalyzer:

    def __init__(self, raster_data):
        if isinstance(raster_data, list):
            raster_data = np.array(raster_data)

        if raster_data.ndim == 3: 
            raster_data = raster_data[0, :, :]

        self.raster_data = raster_data
        self.labels = {
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
        self.values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100]


    def __analyze(self):
        data = self.raster_data
        unique, counts = np.unique(data, return_counts=True)
        land_use_types = dict(zip(unique, counts))
        return land_use_types

    def get_land_use_percentages(self):
        analysis = self.__analyze()
        total = sum(analysis.values())
        percentages = {self.labels.get(land_use, land_use): round((count / total) * 100, 4) for land_use, count in
                       analysis.items() if land_use in self.values}

        return json.dumps(percentages)
