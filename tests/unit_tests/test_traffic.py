import unittest
from unittest.mock import patch, MagicMock
import geopandas as gpd
from shapely.geometry import Polygon, Point, LineString
from src.greento.traffic import traffic
from src.greento.boundingbox import boundingbox

class test_traffic(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.bounding_box = boundingbox(min_x=0, min_y=0, max_x=1, max_y=1)
        self.traffic = traffic(self.bounding_box)

    @patch("src.greento.traffic.ox.graph_from_polygon")
    @patch("src.greento.traffic.ox.graph_to_gdfs")
    @patch("src.greento.traffic.gpd.clip")
    def test_get_traffic_area_success(self, mock_clip, mock_graph_to_gdfs, mock_graph_from_polygon):
        """Test get_traffic_area with valid data."""
        mock_graph = MagicMock()
        mock_graph_from_polygon.return_value = mock_graph

        mock_nodes = gpd.GeoDataFrame({
            'geometry': [Point(0, 0), Point(1, 1)],
            'attribute': ['node1', 'node2']
        }, crs="EPSG:4326")

        mock_edges = gpd.GeoDataFrame({
            'geometry': [LineString([(0, 0), (1, 1)])],
            'attribute': ['edge1']
        }, crs="EPSG:4326")

        mock_graph_to_gdfs.return_value = (mock_nodes, mock_edges)
        mock_clip.side_effect = lambda gdf, bbox: gdf  

        result_nodes, result_edges = self.traffic.get_traffic_area(network_type="drive")

        self.assertFalse(result_nodes.empty)
        self.assertFalse(result_edges.empty)
        self.assertEqual(len(result_nodes), 2)
        self.assertEqual(len(result_edges), 1)
        mock_graph_from_polygon.assert_called_once()
        mock_graph_to_gdfs.assert_called_once()
        mock_clip.assert_called()

    @patch("src.greento.traffic.ox.graph_from_polygon")
    def test_get_traffic_area_no_graph(self, mock_graph_from_polygon):
        """Test get_traffic_area when graph creation fails."""
        mock_graph_from_polygon.return_value = None

        result = self.traffic.get_traffic_area(network_type="drive")

        self.assertIsNone(result)
        mock_graph_from_polygon.assert_called_once()

    @patch("src.greento.traffic.ox.graph_from_polygon")
    @patch("src.greento.traffic.ox.graph_to_gdfs")
    def test_get_traffic_area_empty_data(self, mock_graph_to_gdfs, mock_graph_from_polygon):
        """Test get_traffic_area when nodes or edges are empty."""
        mock_graph = MagicMock()
        mock_graph_from_polygon.return_value = mock_graph

        mock_nodes = gpd.GeoDataFrame(columns=['geometry'], crs="EPSG:4326")
        mock_edges = gpd.GeoDataFrame(columns=['geometry'], crs="EPSG:4326")

        mock_graph_to_gdfs.return_value = (mock_nodes, mock_edges)
        result = self.traffic.get_traffic_area(network_type="drive")

        self.assertIsNone(result)
        mock_graph_from_polygon.assert_called_once()
        mock_graph_to_gdfs.assert_called_once()

    @patch("src.greento.traffic.ox.graph_from_polygon")
    def test_get_traffic_area_invalid_network_type(self, mock_graph_from_polygon):
        """Test get_traffic_area with an invalid network type."""
        mock_graph_from_polygon.side_effect = ValueError("Invalid network type")

        with self.assertRaises(ValueError) as context:
            self.traffic.get_traffic_area(network_type="invalid_type")
        self.assertIn("Invalid network type", str(context.exception))
        mock_graph_from_polygon.assert_called_once()


if __name__ == "__main__":
    unittest.main()