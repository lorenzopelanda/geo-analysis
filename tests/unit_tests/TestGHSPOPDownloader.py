import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
from greento.data.ghspop.GHSPOPDownloader import GHSPOPDownloader
from greento.boundingbox.BoundingBox import BoundingBox
from shapely.geometry import box
import numpy as np
import numpy.testing as npt

class TestGHSPOPDownloader(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.mock_shapefile = "mock_shapefile.shp"
        self.downloader = GHSPOPDownloader(shapefile=self.mock_shapefile)

    @patch("greento.data.ghspop.GHSPOPDownloader.gpd.read_file")
    def test_load_shapefile(self, mock_read_file):
        mock_gdf = MagicMock()
        mock_gdf.crs = "EPSG:4326"
        mock_read_file.return_value = mock_gdf

        result = self.downloader._GHSPOPDownloader__load_shapefile()

        self.assertEqual(result, mock_gdf)
        mock_read_file.assert_called_once_with(self.mock_shapefile)

    @patch("greento.data.ghspop.GHSPOPDownloader.requests.get")
    def test_download_tile_failure(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = self.downloader._GHSPOPDownloader__download_tile("mock_tile_id")

        self.assertIsNone(result)
        mock_get.assert_called_once()

    @patch("greento.data.ghspop.GHSPOPDownloader.os.path.exists")
    @patch("greento.data.ghspop.GHSPOPDownloader.os.remove")
    @patch("greento.data.ghspop.GHSPOPDownloader.zipfile.ZipFile")
    def test_extract_tif_file(self, mock_zipfile, mock_remove, mock_exists):
        mock_zip = MagicMock()
        mock_zipfile.return_value.__enter__.return_value = mock_zip
        mock_zip.namelist.return_value = ["mock_file.tif"]
        
        mock_exists.return_value = True

        with patch("builtins.open", mock_open()):
            result = self.downloader._GHSPOPDownloader__extract_tif_file("mock_zip_path")

        self.assertEqual(result, "extracted_files/mock_file.tif")
        mock_zipfile.assert_called_once_with("mock_zip_path", "r")
        mock_zip.extract.assert_called_once_with("mock_file.tif", "extracted_files")

    @patch("greento.data.ghspop.GHSPOPDownloader.box")
    @patch("greento.data.ghspop.GHSPOPDownloader.gpd.GeoDataFrame")
    def test_get_tiles_for_bounds(self, mock_gdf, mock_box):
        bounds = BoundingBox(min_x=0, min_y=0, max_x=1, max_y=1)
        
        mock_bbox = MagicMock()
        mock_box.return_value = mock_bbox
        
        mock_bbox_gdf = MagicMock()
        mock_gdf.return_value = mock_bbox_gdf
        mock_bbox_gdf.geometry = [mock_bbox]
        
        mock_tiles_gdf = MagicMock()
        
        mock_tiles_gdf.intersects.return_value = [True, False]
        
        filtered_gdf = MagicMock()
        mock_tiles_gdf.__getitem__.return_value = filtered_gdf
        
        filtered_gdf.iterrows.return_value = [
            (0, MagicMock(tile_id="tile_1"))
        ]
        
        for i, row in filtered_gdf.iterrows():
            row.__getitem__.return_value = "tile_1"
        
        result = self.downloader._GHSPOPDownloader__get_tiles_for_bounds(bounds, mock_tiles_gdf)
        
        self.assertEqual(result, ["tile_1"])

    @patch("greento.data.ghspop.GHSPOPDownloader.os.path.exists")
    @patch("greento.data.ghspop.GHSPOPDownloader.rasterio.open")
    def test_process_single_tile(self, mock_rasterio_open, mock_exists):
        with patch.object(self.downloader, '_GHSPOPDownloader__download_tile') as mock_download_tile:
            with patch.object(self.downloader, '_GHSPOPDownloader__extract_tif_file') as mock_extract_tif:
                mock_download_tile.return_value = "mock_zip_path"
                mock_extract_tif.return_value = "mock_tif_path"
                mock_exists.return_value = True
                
                mock_dataset = MagicMock()
                mock_dataset.read.return_value = np.array([[1, 2], [3, 4]])
                mock_dataset.transform = "mock_transform"
                mock_dataset.crs = "mock_crs"
                mock_dataset.shape = (2, 2)
                mock_rasterio_open.return_value.__enter__.return_value = mock_dataset
                
                result = self.downloader._GHSPOPDownloader__process_single_tile("mock_tile_id")
                
                self.assertIsNotNone(result)
                npt.assert_array_equal(result[0], np.array([[1, 2], [3, 4]]))
                self.assertEqual(result[1], "mock_transform")
                self.assertEqual(result[2], "mock_crs")
                self.assertEqual(result[3], (2, 2))
                
                mock_download_tile.assert_called_once_with("mock_tile_id")
                mock_extract_tif.assert_called_once_with("mock_zip_path")
                mock_rasterio_open.assert_called_once_with("mock_tif_path")

if __name__ == "__main__":
    unittest.main()