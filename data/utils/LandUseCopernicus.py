import numpy as np
import json
from .GreenAreaExtractor import GreenAreaExtractor
class LandUseCopernicus(GreenAreaExtractor):
    def __init__(self, copernicus):
        super().__init__(osm=None, copernicus=copernicus)

    def get_land_use_percentages(self, bounding_box):
        data = self.copernicus.get_data(bounding_box)
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