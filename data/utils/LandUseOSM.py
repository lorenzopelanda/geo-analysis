import json
from .GreenAreaExtractor import GreenAreaExtractor
class LandUseOSM(GreenAreaExtractor):
    def __init__(self, osm):
        super().__init__(osm=osm, copernicus=None)

    def get_land_use_percentages(self, bounding_box):
        nodes, edges = self.osm.get_data(bounding_box)
        if nodes is None or edges is None:
            return json.dumps({})
        land_use_types = nodes['natural'].value_counts().to_dict()
        total = sum(land_use_types.values())
        percentages = {key: round((count / total) * 100, 4) for key, count in land_use_types.items()}
        return json.dumps(percentages)