import requests
import openeo
import tempfile
import rasterio
import logging
from tqdm import tqdm
from typing import Dict, Optional, Any
from openeo.rest.connection import Connection
from greento.boundingbox import boundingbox
from greento.data.interface import interface


class copernicus(interface):
    """
    A class to download data from the Copernicus Open Access Hub using OpenEO.

    Parameters
    ----------
    client_id : str, optional
        The client ID for authentication.
    client_secret : str, optional
        The client secret for authentication.
    token_url : str, optional
        The URL to obtain the access token.
    use_oidc : bool, optional
        Whether to use OpenID Connect for authentication (default is False).

    Attributes
    ----------
    client_id : str
        The client ID for authentication.
    client_secret : str
        The client secret for authentication.
    token_url : str
        The URL to obtain the access token.
    access_token : str
        The access token for authentication.
    use_oidc : bool
        Whether to use OpenID Connect for authentication.

    Methods
    -------
    __get_token()
        Obtains an access token using client credentials.
    __connect_to_openeo()
        Connects to the OpenEO backend.
    get_data(bounding_box)
        Downloads data for the specified bounding box.
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        token_url: Optional[str] = None,
        use_oidc: bool = False,
    ) -> None:
        """
        Initializes the CopernicusDownloader with optional authentication parameters.

        Parameters
        ----------
        client_id : str, optional
            The client ID for authentication.
        client_secret : str, optional
            The client secret for authentication.
        token_url : str, optional
            The URL to obtain the access token.
        use_oidc : bool, optional
            Whether to use OpenID Connect for authentication (default is False).

        Returns
        -------
        None
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self.access_token = None
        self.use_oidc = use_oidc

    def __get_token(self) -> None:
        """
        Obtains an access token using client credentials.

        Raises
        ------
        ValueError
            If client ID, client secret, or token URL is not provided.

        Returns
        -------
        None
        """
        if not self.client_id or not self.client_secret or not self.token_url:
            logger = logging.getLogger(__name__)
            logger.warning(
                "Could not download: Client ID, Client Secret, and Token URL must be provided for token-based authentication."
            )
            return

        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        response = requests.post(self.token_url, data=data)
        if response.status_code == 200:
            self.access_token = response.json()["access_token"]
        else:
            self.access_token = None

    def __connect_to_openeo(self) -> Connection:
        """
        Connects to the OpenEO backend.

        Returns
        -------
        openeo.Connection
            The connection to the OpenEO backend.
        """
        connection = openeo.connect("https://openeo.dataspace.copernicus.eu")
        if self.use_oidc:
            with tqdm(disable=True):
                connection.authenticate_oidc()
        else:
            if not self.access_token:
                self.__get_token()
            with tqdm(disable=True):
                connection.authenticate_oidc()
        return connection

    def get_data(self, bounding_box: "boundingbox") -> Dict[str, Any]:
        """
        Downloads data for the specified bounding box.

        Parameters
        ----------
        bounding_box : BoundingBox
            The bounding box for which to download data.

        Returns
        -------
        dict
            A dictionary containing the downloaded data, transform, CRS, and shape.

            Keys:
            - 'data': The raster data.
            - 'transform': The affine transform of the raster.
            - 'crs': The coordinate reference system of the raster.
            - 'shape': The shape of the raster.
        """
        with tqdm(total=100, desc="Downloading Copernicus data", leave=False) as pbar:
            connection = self.__connect_to_openeo()
            pbar.update(20)

            aoi_geojson = bounding_box.to_geojson()
            pbar.update(10)

            datacube = connection.load_collection(
                "ESA_WORLDCOVER_10M_2021_V2", spatial_extent=aoi_geojson, bands=["MAP"]
            )
            pbar.update(30)

            with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as tmpfile:
                datacube.download(tmpfile.name, format="GTiff")
                pbar.update(30)

                with rasterio.open(tmpfile.name) as dataset:
                    data = dataset.read(1)
                    copernicus_transform = dataset.transform
                    copernicus_crs = dataset.crs
                    copernicus_shape = dataset.shape
                pbar.update(10)
                pbar.set_description("Copernicus data downloaded")
                pbar.close()

        return {
            "data": data,
            "transform": copernicus_transform,
            "crs": copernicus_crs,
            "shape": copernicus_shape,
        }
