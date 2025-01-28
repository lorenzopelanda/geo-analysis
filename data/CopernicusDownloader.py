import requests
import openeo
import tempfile
import rasterio
from shapely.geometry import mapping

class CopernicusDownloader:
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

    def download_raster_area(self, bounding_box, use_oidc=False):
        connection = self.connect_to_openeo(use_oidc=use_oidc)

        # Convert the geometry to GeoJSON
        aoi_geojson = mapping(bounding_box)

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
                copernicus_transform = dataset.transform
                copernicus_crs = dataset.crs
                copernicus_shape = dataset.shape

        return data, copernicus_transform, copernicus_crs, copernicus_shape
