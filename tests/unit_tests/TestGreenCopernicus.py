import unittest
import numpy as np
from greento.green.GreenCopernicus import GreenCopernicus

class TestGreenCopernicus(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.mock_copernicus = {
            "data": np.array([[10, 20, 30], [40, 50, 60], [10, 30, 40]]),
            "transform": "mock_transform",
            "crs": "EPSG:4326",
            "shape": (3, 3)
        }
        self.green_copernicus = GreenCopernicus(self.mock_copernicus)

    def test_get_green_default(self):
        """Test get_green with default green areas."""
        result = self.green_copernicus.get_green()
        expected_data = np.array([[1, 1, 1], [0, 0, 0], [1, 1, 0]])

        np.testing.assert_array_equal(result["data"], expected_data)
        self.assertEqual(result["transform"], "mock_transform")
        self.assertEqual(result["crs"], "EPSG:4326")
        self.assertEqual(result["shape"], (3, 3))

    def test_get_green_custom_areas(self):
        """Test get_green with custom green areas."""
        custom_green_areas = frozenset([40, 50])
        result = self.green_copernicus.get_green(green_areas=custom_green_areas)
        expected_data = np.array([[0, 0, 0], [1, 1, 0], [0, 0, 1]])

        np.testing.assert_array_equal(result["data"], expected_data)
        self.assertEqual(result["transform"], "mock_transform")
        self.assertEqual(result["crs"], "EPSG:4326")
        self.assertEqual(result["shape"], (3, 3))

    def test_get_green_empty_data(self):
        """Test get_green with an empty dataset."""
        empty_copernicus = {
            "data": np.array([]),
            "transform": "mock_transform",
            "crs": "EPSG:4326",
            "shape": (0, 0)
        }
        green_copernicus = GreenCopernicus(empty_copernicus)
        result = green_copernicus.get_green()

        np.testing.assert_array_equal(result["data"], np.array([]))
        self.assertEqual(result["transform"], "mock_transform")
        self.assertEqual(result["crs"], "EPSG:4326")
        self.assertEqual(result["shape"], (0, 0))

if __name__ == "__main__":
    unittest.main()