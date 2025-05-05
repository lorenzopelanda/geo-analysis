import unittest
from unittest.mock import patch, MagicMock
import geopandas as gpd
from shapely.geometry import Point, Polygon
from greento.data.osm import osm
from greento.boundingbox import boundingbox

class Testosm(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.bounding_box = boundingbox(min_x=0, min_y=0, max_x=1, max_y=1)
        self.osm_downloader = osm()

    @patch("greento.data.osm.ox.features_from_polygon")
    def test_get_data_success(self, mock_features_from_polygon):
        """Test get_data with valid OSM data."""
        mock_features = gpd.GeoDataFrame({
            'geometry': [Point(0, 0), Point(1, 1), Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])],
            'attribute': ['natural', 'landuse', 'building']
        }, crs="EPSG:4326")
        mock_features_from_polygon.return_value = mock_features

        nodes, edges = self.osm_downloader.get_data(self.bounding_box)

        self.assertFalse(nodes.empty)
        self.assertFalse(edges.empty)
        self.assertEqual(len(nodes), 2) 
        self.assertEqual(len(edges), 1)  
        mock_features_from_polygon.assert_called_once()

    @patch("greento.data.osm.ox.features_from_polygon")
    def test_get_data_empty(self, mock_features_from_polygon):
        """Test get_data with no OSM data."""
        mock_features = gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
        mock_features_from_polygon.return_value = mock_features

        nodes, edges = self.osm_downloader.get_data(self.bounding_box)

        self.assertTrue(nodes.empty)
        self.assertTrue(edges.empty)
        mock_features_from_polygon.assert_called_once()

    @patch("greento.data.osm.ox.features_from_polygon")
    def test_get_data_exception(self, mock_features_from_polygon):
        """Test get_data when an exception occurs."""
        mock_features_from_polygon.side_effect = Exception("Mocked exception")

        with self.assertRaises(ValueError) as context:
            self.osm_downloader.get_data(self.bounding_box)

        self.assertIn("Error during OSM data download", str(context.exception))
        mock_features_from_polygon.assert_called_once()

if __name__ == "__main__":
    unittest.main()