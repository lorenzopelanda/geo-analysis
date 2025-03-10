import requests
import openeo
import tempfile
import rasterio
from data.utils.UtilsInterface import DownloaderInterface, GreenInterface

class CopernicusDownloader(DownloaderInterface, GreenInterface):
    def __init__(self, client_id=None, client_secret=None, token_url=None, use_oidc=False):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self.access_token = None
        self.use_oidc = use_oidc

    def __get_token(self):
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

    def __connect_to_openeo(self):
        connection = openeo.connect("https://openeo.dataspace.copernicus.eu")
        if self.use_oidc:
            connection.authenticate_oidc()
        else:
            if not self.access_token:
                self.__get_token()
            connection.authenticate_oidc()
        return connection

    def get_data(self, bounding_box):
        connection = self.__connect_to_openeo()

        # Convert the geometry to GeoJSON
        aoi_geojson = bounding_box.to_geojson()

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
                data = dataset.read(1)
                copernicus_transform = dataset.transform
                copernicus_crs = dataset.crs
                copernicus_shape = dataset.shape

        return {
            "data": data,
            "transform": copernicus_transform,
            "crs": copernicus_crs,
            "shape": copernicus_shape
        }


