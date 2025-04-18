import unittest
from unittest.mock import patch, MagicMock
from greento.data.copernicus.CopernicusDownloader import CopernicusDownloader
from shapely.geometry import box
import rasterio

class TestCopernicusDownloader(unittest.TestCase):

    @patch("greento.data.copernicus.CopernicusDownloader.requests.post")
    def test_get_token_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "mock_token"}
        mock_post.return_value = mock_response

        downloader = CopernicusDownloader(client_id="test_id", client_secret="test_secret", token_url="https://example.com/token")
        downloader._CopernicusDownloader__get_token()

        self.assertEqual(downloader.access_token, "mock_token")
        mock_post.assert_called_once_with(
            "https://example.com/token",
            data={"grant_type": "client_credentials", "client_id": "test_id", "client_secret": "test_secret"}
        )

    @patch("greento.data.copernicus.CopernicusDownloader.requests.post")
    def test_get_token_failure(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response

        downloader = CopernicusDownloader(client_id="test_id", client_secret="test_secret", token_url="https://example.com/token")
        downloader._CopernicusDownloader__get_token()

        self.assertIsNone(downloader.access_token)

    @patch("greento.data.copernicus.CopernicusDownloader.openeo.connect")
    def test_connect_to_openeo(self, mock_connect):
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection

        downloader = CopernicusDownloader(use_oidc=False)
        downloader.access_token = "mock_token"
        connection = downloader._CopernicusDownloader__connect_to_openeo()

        self.assertEqual(connection, mock_connection)
        mock_connect.assert_called_once_with("https://openeo.dataspace.copernicus.eu")

    @patch("greento.data.copernicus.CopernicusDownloader.CopernicusDownloader._CopernicusDownloader__get_token")
    @patch("greento.data.copernicus.CopernicusDownloader.openeo.connect")
    @patch("greento.data.copernicus.CopernicusDownloader.tempfile.NamedTemporaryFile")
    @patch("greento.data.copernicus.CopernicusDownloader.rasterio.open")
    def test_get_data(self, mock_rasterio_open, mock_tempfile, mock_connect, mock_get_token):
        mock_get_token.return_value = None

        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection

        mock_datacube = MagicMock()
        mock_connection.load_collection.return_value = mock_datacube

        mock_tempfile_instance = MagicMock()
        mock_tempfile.return_value.__enter__.return_value = mock_tempfile_instance

        mock_dataset = MagicMock()
        mock_dataset.read.return_value = [[1, 2], [3, 4]]
        mock_dataset.transform = "mock_transform"
        mock_dataset.crs = "mock_crs"
        mock_dataset.shape = (2, 2)
        mock_rasterio_open.return_value.__enter__.return_value = mock_dataset

        bounding_box = MagicMock()
        bounding_box.to_geojson.return_value = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]}

        downloader = CopernicusDownloader()
        result = downloader.get_data(bounding_box)

        self.assertEqual(result["data"], [[1, 2], [3, 4]])
        self.assertEqual(result["transform"], "mock_transform")
        self.assertEqual(result["crs"], "mock_crs")
        self.assertEqual(result["shape"], (2, 2))

        mock_connect.assert_called_once_with("https://openeo.dataspace.copernicus.eu")
        mock_connection.load_collection.assert_called_once_with(
            "ESA_WORLDCOVER_10M_2021_V2",
            spatial_extent={"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
            bands=["MAP"]
        )
        mock_tempfile.assert_called_once()
        mock_rasterio_open.assert_called_once_with(mock_tempfile_instance.name)

if __name__ == "__main__":
    unittest.main()