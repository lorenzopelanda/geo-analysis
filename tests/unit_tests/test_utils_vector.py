import unittest
from unittest.mock import patch, MagicMock
import numpy as np
import geopandas as gpd
import json
import pandas as pd
from shapely.geometry import Point, LineString
from rasterio.transform import Affine
from src.greento.utils.vector import vector

class test_utils_vector(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.mock_nodes = gpd.GeoDataFrame({
            'id': [1, 2, 3],
            'natural': ['forest', 'tree', 'grass'],
            'geometry': [Point(0, 0), Point(1, 1), Point(2, 2)]
        }, crs="EPSG:4326")

        self.mock_edges = gpd.GeoDataFrame({
            'id': [1, 2],
            'geometry': [LineString([(0, 0), (1, 1)]), LineString([(1, 1), (2, 2)])]
        }, crs="EPSG:4326")

        self.valid_ref_raster = {
        'transform': Affine.identity(),
        'crs': "EPSG:4326",
        'shape': (3, 3),
        'data': np.zeros((3, 3))
        }

        self.vector_utils = vector((self.mock_nodes, self.mock_edges))

    def test_get_land_use_percentages(self):
        """Test get_land_use_percentages with valid data."""
        result = self.vector_utils.get_land_use_percentages()
        expected_percentages = {
            "forest": 33.3333,
            "tree": 33.3333,
            "grass": 33.3333
        }

        result_dict = json.loads(result)

        for key, value in expected_percentages.items():
            self.assertAlmostEqual(result_dict[key], value, places=4)

    def test_get_land_use_percentages_empty(self):
        """Test get_land_use_percentages with empty data."""
        empty_nodes = gpd.GeoDataFrame(columns=['id', 'natural', 'geometry'], crs="EPSG:4326")
        empty_edges = gpd.GeoDataFrame(columns=['id', 'geometry'], crs="EPSG:4326")
        vector_utils = vector((empty_nodes, empty_edges))

        result = vector_utils.get_land_use_percentages()
        self.assertEqual(result, "{}")  

    def test_to_raster_success(self):
        """Test to_raster with valid data."""
        reference_raster = {
            'data': np.zeros((3, 3), dtype=np.uint8),
            'transform': Affine.identity(),
            'crs': "EPSG:4326",
            'shape': (3, 3)
        }

        result = self.vector_utils.to_raster(reference_raster)

        self.assertEqual(result['data'].shape, (3, 3))
        self.assertEqual(result['transform'], reference_raster['transform'])
        self.assertEqual(result['crs'], reference_raster['crs'])
        self.assertEqual(result['shape'], reference_raster['shape'])
        self.assertTrue(np.any(result['data'] > 0)) 

    def test_to_raster_invalid_nodes(self):
        """Test with non-GeoDataFrame nodes"""
        invalid_nodes = pd.DataFrame(columns=['id'])  
        vector_utils = vector((invalid_nodes, self.mock_edges))
        
        with self.assertRaises(ValueError) as ctx:
            vector_utils.to_raster(self.valid_ref_raster)
        self.assertIn("must be a GeoDataFrame", str(ctx.exception))  


    def test_to_raster_invalid_edges(self):
        """Test with non-GeoDataFrame edges"""
        invalid_edges = pd.DataFrame(columns=['id'])  
        vector_utils = vector((self.mock_nodes, invalid_edges))
        
        with self.assertRaises(ValueError) as ctx:
            vector_utils.to_raster(self.valid_ref_raster)
        self.assertIn("must be a GeoDataFrame", str(ctx.exception))



if __name__ == "__main__":
    unittest.main()