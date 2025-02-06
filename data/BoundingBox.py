import json
import geopandas as gpd
import osmnx as ox
from shapely.geometry import box, Point, mapping
import pyproj
from pyproj import CRS, Transformer, exceptions

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

    def to_geojson(self):
        return mapping(self.to_geometry())

    def get_coordinates(self, query, is_address=True):
        if is_address:
            # Geocoding for address
            gdf = gpd.tools.geocode(query, provider="nominatim", user_agent="geoData")
            if not gdf.empty:
                point = gdf.geometry.iloc[0]
                return point.y, point.x
            else:
                return None
        else:
            # Center of municipality
            gdf = ox.geocode_to_gdf(query, which_result=1)
            if not gdf.empty:
                gdf_projected = gdf.to_crs(epsg=3857)
                center_projected = gdf_projected.geometry.centroid.iloc[0]
                center = gpd.GeoSeries([center_projected], crs="EPSG:3857").to_crs(epsg=4326).iloc[0]
                return center.y, center.x
            else:
                return None

    def get_bounding_box(self, query, method, is_address=True, **kwargs):
        coords = self.get_coordinates(query, is_address=is_address)
        center_point = Point(coords[1], coords[0])  # (longitude, latitude)

        if method == 'from_center_radius':
            radius_km = kwargs.get('radius_km', 10)
            return self.from_center_radius(center_point.x, center_point.y, radius_km)
        elif method == 'from_coordinates':
            min_x = kwargs.get('min_x')
            min_y = kwargs.get('min_y')
            max_x = kwargs.get('max_x')
            max_y = kwargs.get('max_y')
            return self.from_coordinates(min_x, min_y, max_x, max_y)
        elif method == 'from_geojson':
            geojson = kwargs.get('geojson')
            return self.from_geojson(geojson)

    def transform_to_esri54009(self):
        crs_esri_54009 = pyproj.CRS.from_string("ESRI:54009")

        transformer = Transformer.from_crs(CRS.from_epsg(4326), crs_esri_54009, always_xy=True)

        min_x, min_y = transformer.transform(self.min_x, self.min_y)
        max_x, max_y = transformer.transform(self.max_x, self.max_y)

        return BoundingBox(min_x, min_y, max_x, max_y)


    def __repr__(self):
        return f"BoundingBox({self.min_x}, {self.min_y}, {self.max_x}, {self.max_y})"