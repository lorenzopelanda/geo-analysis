import geopandas as gpd
from shapely.geometry import box, Point, mapping
import osmnx as ox
import openeo
import requests

# Function to create a bounding box of approximately 10 km x 10 km
def create_bounding_box(center_point, size_km=10):
    size_deg = size_km / 111  # from km to degrees
    minx = center_point.x - size_deg / 2
    miny = center_point.y - size_deg / 2
    maxx = center_point.x + size_deg / 2
    maxy = center_point.y + size_deg / 2
    return box(minx, miny, maxx, maxy)

def get_coordinates(query, is_address=True):
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

# Get the interested area based on the time travel and time mode
def get_isochrone_area(center_point, travel_time, travel_mode):
    G = ox.graph_from_point((center_point.y, center_point.x), dist=2000, network_type=travel_mode)
    center_node = ox.distance.nearest_nodes(G, center_point.x, center_point.y)
    subgraph = ox.truncate.truncate_graph_dist(G, center_node, travel_time * 60, weight='travel_time')
    nodes, edges = ox.graph_to_gdfs(subgraph)
    return nodes.unary_union.convex_hull

def get_bounding_box(query, travel_time, travel_mode, is_address=True, ):
    coords = get_coordinates(query, is_address=is_address)
    center_point = Point(coords[1], coords[0])  # (longitude, latitude)

    if travel_time > 0:
        area = get_isochrone_area(center_point, travel_time, travel_mode)
        return area
    
    # Create a bounding box of 10km x 10km if no travel time is specified
    else:
        bounding_box = create_bounding_box(center_point, size_km=10)
        return bounding_box


def get_raster_area(query, travel_time, travel_mode, is_address=True, ):
    # Authentication with Copernicus
    client_id = "sh-a24a739d-d123-419b-a409-81a190c436c2"
    client_secret = "dcUnE32uBB1gLvlxyi3qOeUPdGGpNMRs"
    token_url = 'https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token'

    data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret
    }

    response = requests.post(token_url, data=data)
    if response.status_code == 200:
        access_token = response.json()['access_token']
    else:
        access_token = None

    # Connection to Copernicus OpenEO
    if access_token:
        connection = openeo.connect("https://openeo.dataspace.copernicus.eu")
        connection.authenticate_oidc()

        # Convert the bounding box to GeoJSON
        aoi_geojson = mapping(get_bounding_box(query, is_address=is_address, travel_time=travel_time, travel_mode=travel_mode))

        # Perform the analysis directly on the remote data
        datacube = connection.load_collection(
            "ESA_WORLDCOVER_10M_2021_V2",
            spatial_extent=aoi_geojson,
            bands=["MAP"]
        )

        # Download the results as a GeoTIFF file
        output_path = "area.tif"
        datacube.download(output_path, format="GTiff")
        
