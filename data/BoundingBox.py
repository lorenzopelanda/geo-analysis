import json
from shapely.geometry import box, Point, mapping

class BoundingBox:
    def __init__(self, min_x=None, min_y=None, max_x=None, max_y=None):
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y

    def from_coordinates(self, min_x, min_y, max_x, max_y):
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y
        return self.to_geometry()

    def from_center_radius(self, center_x, center_y, radius_km):
        if radius_km is None:
            radius_km = 10
        size_deg = radius_km / 111  # Convert km to degrees
        self.min_x = center_x - size_deg
        self.min_y = center_y - size_deg
        self.max_x = center_x + size_deg
        self.max_y = center_y + size_deg
        return self.to_geometry()

    def from_geojson(self, geojson):
        geom = json.loads(geojson)
        bbox = box(*geom['bbox'])
        self.min_x, self.min_y, self.max_x, self.max_y = bbox.bounds
        return bbox

    def to_geometry(self):
        return box(self.min_x, self.min_y, self.max_x, self.max_y)

    def __repr__(self):
        return f"BoundingBox({self.min_x}, {self.min_y}, {self.max_x}, {self.max_y})"