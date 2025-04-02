import unittest
from unittest.mock import patch, MagicMock
import numpy as np
import json
import rasterio
from rasterio.transform import Affine
from greento.utils.raster.RasterUtils import RasterUtils

class TestRasterUtils(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.mock_copernicus = {
            'data': np.array([[10, 20, 30], [40, 50, 60], [10, 30, 40]]),
            'transform': Affine(1.0, 0.0, 0.0, 0.0, -1.0, 0.0),
            'crs': 'EPSG:4326',
            'shape': (3, 3)
        }
        self.raster_utils = RasterUtils(self.mock_copernicus)

    def test_filter_with_osm_success(self):
        """Test filter_with_osm with matching raster shapes."""
        copernicus_green = {
            'data': np.array([[1, 1, 0], [0, 1, 1], [1, 0, 1]]),
            'transform': MagicMock(),
            'crs': 'EPSG:4326',
            'shape': (3, 3)
        }
        osm_green = {
            'data': np.array([[1, 0, 1], [1, 1, 0], [1, 1, 1]]),
            'transform': MagicMock(),
            'crs': 'EPSG:4326',
            'shape': (3, 3)
        }

        result = self.raster_utils.filter_with_osm(copernicus_green, osm_green)
        expected_data = np.array([[1, 0, 0], [0, 1, 0], [1, 0, 1]])

        np.testing.assert_array_equal(result['data'], expected_data)
        self.assertEqual(result['transform'], copernicus_green['transform'])
        self.assertEqual(result['crs'], copernicus_green['crs'])
        self.assertEqual(result['shape'], copernicus_green['shape'])

    def test_filter_with_osm_shape_mismatch(self):
        """Test filter_with_osm with mismatched raster shapes."""
        copernicus_green = {
            'data': np.array([[1, 1, 0], [0, 1, 1]]), 
            'transform': MagicMock(),
            'crs': 'EPSG:4326',
            'shape': (2, 3)
        }
        osm_green = {
            'data': np.array([[1, 0], [1, 1]]),
            'transform': MagicMock(),
            'crs': 'EPSG:4326',
            'shape': (2, 2)
        }

        with self.assertRaises(ValueError) as context:
            self.raster_utils.filter_with_osm(copernicus_green, osm_green)
        self.assertIn("Raster shapes do not match", str(context.exception))

    def test_get_land_use_percentages(self):
        """Test get_land_use_percentages with valid data."""
        self.mock_copernicus['data'] = np.array([
            [10, 10, 20],
            [30, 30, 40],
            [50, 50, 10]
        ])
        self.raster_utils = RasterUtils(self.mock_copernicus)

        result = self.raster_utils.get_land_use_percentages()
        result_dict = json.loads(result)

        expected_percentages = {
            "Forest and trees": 33.3333, 
            "Shrubs": 11.1111,          
            "Grassland": 22.2222,        
            "Cropland": 11.1111,        
            "Buildings": 22.2222        
        }


        for key, value in expected_percentages.items():
            self.assertAlmostEqual(result_dict[key], value, places=4)

    @patch("greento.utils.raster.RasterUtils.tqdm")
    @patch("greento.utils.raster.RasterUtils.reproject")
    @patch("greento.utils.raster.RasterUtils.calculate_default_transform")
    def test_raster_to_crs(self, mock_calculate_transform, mock_reproject, mock_tqdm):
        """Test raster_to_crs with valid data."""
        mock_transform = rasterio.transform.from_origin(0, 0, 1, 1)  
        mock_calculate_transform.return_value = (mock_transform, 3, 3) 
        mock_reproject.side_effect = lambda **kwargs: kwargs['destination'].fill(1)

        result = self.raster_utils.raster_to_crs("EPSG:3857")

        self.assertEqual(result['crs'], "EPSG:3857")
        self.assertEqual(result['data'].shape, (1, 3, 3))  
        self.assertTrue(np.all(result['data'] == 1))

    def test_raster_to_crs_invalid_shape(self):
        """Test raster_to_crs with invalid shape."""
        self.raster_utils.copernicus['shape'] = (3, 3, 3, 3)

        with self.assertRaises(ValueError) as context:
            self.raster_utils.raster_to_crs("EPSG:3857")
        self.assertIn("Shape of the data incorrect", str(context.exception))


if __name__ == "__main__":
    unittest.main()