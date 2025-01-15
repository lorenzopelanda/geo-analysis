import requests
import openeo
import tempfile
import rasterio
import geopandas as gpd
from shapely.geometry import box, Point, mapping
import osmnx as ox
from shapely.geometry import mapping
from data.BoundingBox import BoundingBox
class RasterDownloader:
    def __init__(self, client_id=None, client_secret=None, token_url=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self.access_token = None

    def get_token(self):
        if not self.client_id or not self.client_secret or not self.token_url:
            raise ValueError("Client ID, Client Secret, and Token URL must be provided for token-based authentication.")

        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }

        response = requests.post(self.token_url, data=data)
        if response.status_code == 200:
            self.access_token = response.json()['access_token']
        else:
            self.access_token = None

    def connect_to_openeo(self, use_oidc=False):
        connection = openeo.connect("https://openeo.dataspace.copernicus.eu")
        if use_oidc:
            connection.authenticate_oidc()
        else:
            if not self.access_token:
                self.get_token()
            connection.authenticate_oidc()
        return connection

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

    def get_isochrone_area(self, center_point, travel_time, travel_mode):
        G = ox.graph_from_point((center_point.y, center_point.x), dist=2000, network_type=travel_mode)
        center_node = ox.distance.nearest_nodes(G, center_point.x, center_point.y)
        subgraph = ox.truncate.truncate_graph_dist(G, center_node, travel_time * 60, weight='travel_time')
        nodes, edges = ox.graph_to_gdfs(subgraph)
        return nodes.unary_union.convex_hull

    def get_bounding_box(self, query, travel_time, travel_mode, is_address=True):
        coords = self.get_coordinates(query, is_address=is_address)
        center_point = Point(coords[1], coords[0])  # (longitude, latitude)
        bbox = BoundingBox()

        if travel_time > 0:
            area = self.get_isochrone_area(center_point, travel_time, travel_mode)
            return bbox.from_geojson(mapping(area))
        else:
            return bbox.from_center_radius(center_point.x, center_point.y, radius_km=10)

    def download_raster_area(self, query, travel_time, travel_mode, is_address=True, use_oidc=False):
        connection = self.connect_to_openeo(use_oidc=use_oidc)

        # Convert the bounding box to GeoJSON
        aoi_geom = self.get_bounding_box(query, is_address=is_address, travel_time=travel_time, travel_mode=travel_mode)

        # Convert the geometry to GeoJSON
        aoi_geojson = mapping(aoi_geom)

        # Perform the analysis directly on the remote data
        datacube = connection.load_collection(
            "ESA_WORLDCOVER_10M_2021_V2",
            spatial_extent=aoi_geojson,
            bands=["MAP"]
        )

        # Execute the process and get the result
        with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as tmpfile:
            datacube.download(tmpfile.name, format="GTiff")

            # Read the data into a data structure
            with rasterio.open(tmpfile.name) as dataset:
                data = dataset.read()

        print(f"Temporary file still exists at: {tmpfile.name}")
        return data
