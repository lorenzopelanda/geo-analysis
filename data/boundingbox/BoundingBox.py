import json
import geopandas as gpd
import osmnx as ox
from shapely.geometry import box, Point, mapping, Polygon

class BoundingBox:
    def __init__(self, min_x=None, min_y=None, max_x=None, max_y=None, crs="EPSG:4326"):
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y
        self.polygon = None
        self.crs = crs

    def __from_coordinates(self, min_x, min_y, max_x, max_y):
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y
        self.polygon = self.to_geometry()
        return self

    def __from_center_radius(self, center_x, center_y, radius_km):
        if radius_km is None:
            radius_km = 10
        size_deg = radius_km / 111  # Convert km to degrees
        self.min_x = center_x - size_deg
        self.min_y = center_y - size_deg
        self.max_x = center_x + size_deg
        self.max_y = center_y + size_deg
        self.polygon = self.to_geometry()
        return self

    def __from_geojson(self, geojson):
        if isinstance(geojson, str):
            try:
                geojson = json.loads(geojson)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid GeoJSON string: {str(e)}")

        if not isinstance(geojson, dict):
            raise ValueError("GeoJSON must be either a valid JSON string or a dictionary")

        min_x, min_y, max_x, max_y = float('inf'), float('inf'), float('-inf'), float('-inf')

        def update_min_max(coords):
            nonlocal min_x, min_y, max_x, max_y
            for x, y in coords:
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)

        try:
            if geojson.get('type') == 'FeatureCollection':
                for feature in geojson['features']:
                    if feature['geometry']['type'] == 'Polygon':
                        for ring in feature['geometry']['coordinates']:
                            update_min_max(ring)
            elif geojson.get('type') == 'Feature':
                if geojson['geometry']['type'] == 'Polygon':
                    for ring in geojson['geometry']['coordinates']:
                        update_min_max(ring)
            elif geojson.get('type') == 'Polygon':
                for ring in geojson['coordinates']:
                    update_min_max(ring)
            else:
                raise ValueError(f"Unsupported GeoJSON type: {geojson.get('type')}")

        except KeyError as e:
            raise ValueError(f"Invalid GeoJSON structure: missing key {str(e)}")

        if min_x == float('inf') or min_y == float('inf') or max_x == float('-inf') or max_y == float('-inf'):
            raise ValueError("No valid coordinates found in GeoJSON")

        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y

        self.polygon = Polygon([
            (self.min_x, self.min_y),
            (self.max_x, self.min_y),
            (self.max_x, self.max_y),
            (self.min_x, self.max_y)
        ])

        return self

    def to_geometry(self):
        return box(self.min_x, self.min_y, self.max_x, self.max_y)

    def to_geojson(self):
        if self.polygon is None:
            self.polygon = self.to_geometry()
        return mapping(self.polygon)

    def get_bounding_box(self, query, method, is_address=True, **kwargs):
        if method == 'from_geojson':
            geojson = kwargs.get('geojson')
            return self.__from_geojson(geojson)

        if method == 'from_center_radius':
            coords = self.__get_coordinates(query, is_address=is_address)
            if coords is None:
                return None
            center_point = Point(coords[1], coords[0])
            radius_km = kwargs.get('radius_km', 10)
            return self.__from_center_radius(center_point.x, center_point.y, radius_km)

        elif method == 'from_coordinates':
            min_x = kwargs.get('min_x')
            min_y = kwargs.get('min_y')
            max_x = kwargs.get('max_x')
            max_y = kwargs.get('max_y')
            return self.__from_coordinates(min_x, min_y, max_x, max_y)

    def __get_coordinates(self, query, is_address=True):
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


    def __repr__(self):
        return f"BoundingBox({self.min_x}, {self.min_y}, {self.max_x}, {self.max_y})"