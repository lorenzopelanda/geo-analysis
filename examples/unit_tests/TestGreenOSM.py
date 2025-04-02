import unittest
import geopandas as gpd
from shapely.geometry import Point, LineString
from greento.green.GreenOSM import GreenOSM

class TestGreenOSM(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""

        self.mock_nodes = gpd.GeoDataFrame({
            'id': [1, 2, 3],
            'natural': ['wood', 'tree', 'rock'],
            'geometry': [Point(0, 0), Point(1, 1), Point(2, 2)]
        }, crs="EPSG:4326")

        self.mock_edges = gpd.GeoDataFrame({
            'id': [1, 2],
            'landuse': ['forest', 'industrial'],
            'geometry': [LineString([(0, 0), (1, 1)]), LineString([(1, 1), (2, 2)])]
        }, crs="EPSG:4326")

        self.green_osm = GreenOSM((self.mock_nodes, self.mock_edges))

    def test_get_green_default(self):
        """Test get_green with default green tags."""
        result_nodes, result_edges = self.green_osm.get_green()

        expected_nodes = gpd.GeoDataFrame({
            'id': [1, 2],
            'natural': ['wood', 'tree'],
            'geometry': [Point(0, 0), Point(1, 1)]
        }, crs="EPSG:4326")

        expected_edges = gpd.GeoDataFrame({
            'id': [1],
            'landuse': ['forest'],
            'geometry': [LineString([(0, 0), (1, 1)])]
        }, crs="EPSG:4326")

        self.assertTrue(result_nodes.equals(expected_nodes))
        self.assertTrue(result_edges.equals(expected_edges))

    def test_get_green_custom_tags(self):
        """Test get_green with custom green tags."""
        custom_tags = {
            'natural': ['rock'],
            'landuse': ['industrial']
        }
        result_nodes, result_edges = self.green_osm.get_green(green_tags=custom_tags)

        expected_nodes = gpd.GeoDataFrame({
            'id': [3],
            'natural': ['rock'],
            'geometry': [Point(2, 2)]
        }, crs="EPSG:4326")

        expected_edges = gpd.GeoDataFrame({
            'id': [2],
            'landuse': ['industrial'],
            'geometry': [LineString([(1, 1), (2, 2)])]
        }, crs="EPSG:4326")

        result_nodes = result_nodes.sort_values(by="id").reset_index(drop=True)
        expected_nodes = expected_nodes.sort_values(by="id").reset_index(drop=True)
        result_edges = result_edges.sort_values(by="id").reset_index(drop=True)
        expected_edges = expected_edges.sort_values(by="id").reset_index(drop=True)

        self.assertTrue(result_nodes.equals(expected_nodes))
        self.assertTrue(result_edges.equals(expected_edges))

    def test_get_green_empty_data(self):
        """Test get_green with empty GeoDataFrames."""
        empty_osm = (gpd.GeoDataFrame(geometry=[]), gpd.GeoDataFrame(geometry=[]))
        green_osm = GreenOSM(empty_osm)
        result_nodes, result_edges = green_osm.get_green()

        self.assertTrue(result_nodes.empty)
        self.assertTrue(result_edges.empty)

if __name__ == "__main__":
    unittest.main()