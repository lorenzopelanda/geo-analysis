import json
import geopandas as gpd
import osmnx as ox
import pyproj
from pyproj import Transformer
from tqdm import tqdm
from shapely.geometry import box, Point, mapping, Polygon

class BoundingBox:
    """
    A class to represent a geographical bounding box.

    Attributes:
    ----------
    min_x : float
        Minimum x-coordinate (longitude).
    min_y : float
        Minimum y-coordinate (latitude).
    max_x : float
        Maximum x-coordinate (longitude).
    max_y : float
        Maximum y-coordinate (latitude).
    polygon : shapely.geometry.Polygon
        Polygon representation of the bounding box.
    crs : str
        Coordinate reference system (default is "EPSG:4326").

    Methods:
    -------
    __from_coordinates(min_x, min_y, max_x, max_y):
        Creates a bounding box from given coordinates.
    __from_center_radius(center_x, center_y, radius_km):
        Creates a bounding box from a center point and radius.
    __from_geojson(geojson):
        Creates a bounding box from a GeoJSON object.
    to_geometry():
        Converts the bounding box to a Shapely geometry.
    to_geojson():
        Converts the bounding box to a GeoJSON format.
    transform_to_crs(dst_crs):
        Transforms the bounding box to a specified CRS.
    get_bounding_box(query, method, is_address=True, **kwargs):
        Creates a bounding box using the specified method.
    __get_coordinates(query, is_address=True):
        Gets coordinates by geocoding an address or finding the center of a municipality.
    __repr__():
        Returns a string representation of the bounding box.
    """

    def __init__(self, min_x=None, min_y=None, max_x=None, max_y=None, crs="EPSG:4326"):
        """
        Initializes the BoundingBox with optional coordinates and CRS.

        Args:
            min_x (float, optional): Minimum x-coordinate (longitude). Defaults to None.
            min_y (float, optional): Minimum y-coordinate (latitude). Defaults to None.
            max_x (float, optional): Maximum x-coordinate (longitude). Defaults to None.
            max_y (float, optional): Maximum y-coordinate (latitude). Defaults to None.
            crs (str, optional): Coordinate reference system. Defaults to "EPSG:4326".

        Returns:
            None
        """
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y
        self.polygon = None
        self.crs = crs

    def __from_coordinates(self, min_x, min_y, max_x, max_y):
        """
        Creates a bounding box from given coordinates.

        Args:
            min_x (float): Minimum x-coordinate (longitude).
            min_y (float): Minimum y-coordinate (latitude).
            max_x (float): Maximum x-coordinate (longitude).
            max_y (float): Maximum y-coordinate (latitude).

        Returns:
            BoundingBox: The bounding box object.
        """
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y
        self.polygon = self.to_geometry()
        return self

    def __from_center_radius(self, center_x, center_y, radius_km):
        """
        Creates a bounding box from a center point and radius.

        Args:
            center_x (float): Center x-coordinate (longitude).
            center_y (float): Center y-coordinate (latitude).
            radius_km (float): Radius in kilometers.

        Returns:
            BoundingBox: The bounding box object.
        """
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
        """
        Creates a bounding box from a GeoJSON object.

        Args:
            geojson (str or dict): GeoJSON string or dictionary.

        Returns:
            BoundingBox: The bounding box object.

        Raises:
            ValueError: If the GeoJSON is invalid or unsupported.
        """
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
        """
        Converts the bounding box to a Shapely geometry.

        Returns:
            shapely.geometry.Polygon: The polygon representation of the bounding box.
        """
        return box(self.min_x, self.min_y, self.max_x, self.max_y)

    def to_geojson(self):
        """
        Converts the bounding box to a GeoJSON format.

        Returns:
            dict: The GeoJSON representation of the bounding box.
        """
        if self.polygon is None:
            self.polygon = self.to_geometry()
        return mapping(self.polygon)

    def transform_to_crs(self, dst_crs):
        """
        Transforms the bounding box to a specified CRS.

        Args:
            dst_crs (str): The destination coordinate reference system.

        Returns:
            BoundingBox: The transformed bounding box object.
        """
        with tqdm(total=100, desc="Transforming bounding box", leave=False) as pbar:
            if self.polygon is None:
                self.polygon = self.to_geometry()
            pbar.update(20)
            crs_src = pyproj.CRS.from_string(self.crs)
            crs_dest = pyproj.CRS.from_string(dst_crs)
            transformer = Transformer.from_crs(crs_src, crs_dest, always_xy=True)
            min_x, min_y = transformer.transform(self.min_x, self.min_y)
            max_x, max_y = transformer.transform(self.max_x, self.max_y)
            pbar.update(60)

            result = BoundingBox(min_x=min_x, min_y=min_y, max_x=max_x, max_y=max_y, crs=dst_crs)
            result.polygon = result.to_geometry()
            pbar.update(20)
            pbar.set_description("Bounding box transformed")
            pbar.close()
        return result

    def get_bounding_box(self, query, method, is_address=True, **kwargs):
        """
        Creates a bounding box using the specified method.

        Args:
            query (str): The query string (address or municipality name).
            method (str): The method to create the bounding box ('from_geojson', 'from_center_radius', 'from_coordinates').
            is_address (bool, optional): Whether the query is an address (default is True).
            **kwargs: Additional arguments for the specified method.

        Returns:
            BoundingBox: The created bounding box object.
        """
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
        """
        Gets coordinates by geocoding an address or finding the center of a municipality.

        Args:
            query (str): The query string (address or municipality name).
            is_address (bool, optional): Whether the query is an address (default is True).

        Returns:
            tuple: The coordinates (latitude, longitude) or None if not found.
        """
        if is_address:
            gdf = gpd.tools.geocode(query, provider="nominatim", user_agent="geoData")
            if not gdf.empty:
                point = gdf.geometry.iloc[0]
                return point.y, point.x
            else:
                return None
        else:
            gdf = ox.geocode_to_gdf(query, which_result=1)
            if not gdf.empty:
                gdf_projected = gdf.to_crs(epsg=3857)
                center_projected = gdf_projected.geometry.centroid.iloc[0]
                center = gpd.GeoSeries([center_projected], crs="EPSG:3857").to_crs(epsg=4326).iloc[0]
                return center.y, center.x
            else:
                return None


    def __repr__(self):
        """
        Returns a string representation of the bounding box.

        Returns:
            str: The string representation of the bounding box.
        """
        return f"BoundingBox({self.min_x}, {self.min_y}, {self.max_x}, {self.max_y})"