import unittest
from src.greento.boundingbox import boundingbox
from shapely.geometry import Polygon

class test_boundingbox(unittest.TestCase):
    def test_from_coordinates(self):
        bbox = boundingbox()._boundingbox__from_coordinates(-10, -5, 10, 5)
        self.assertEqual(bbox.min_x, -10)
        self.assertEqual(bbox.min_y, -5)
        self.assertEqual(bbox.max_x, 10)
        self.assertEqual(bbox.max_y, 5)
        self.assertIsInstance(bbox.polygon, Polygon)

    def test_from_center_radius(self):
        bbox = boundingbox()._boundingbox__from_center_radius(0, 0, 10)
        self.assertAlmostEqual(bbox.min_x, -0.09, places=2)
        self.assertAlmostEqual(bbox.min_y, -0.09, places=2)
        self.assertAlmostEqual(bbox.max_x, 0.09, places=2)
        self.assertAlmostEqual(bbox.max_y, 0.09, places=2)
        self.assertIsInstance(bbox.polygon, Polygon)

    def test_from_geojson(self):
        geojson = {
            "type": "Polygon",
            "coordinates": [
                [
                    [-10, -5],
                    [10, -5],
                    [10, 5],
                    [-10, 5],
                    [-10, -5]
                ]
            ]
        }
        bbox = boundingbox()._boundingbox__from_geojson(geojson)
        self.assertEqual(bbox.min_x, -10)
        self.assertEqual(bbox.min_y, -5)
        self.assertEqual(bbox.max_x, 10)
        self.assertEqual(bbox.max_y, 5)
        self.assertIsInstance(bbox.polygon, Polygon)

    def test_to_geometry(self):
        bbox = boundingbox(-10, -5, 10, 5)
        geometry = bbox.to_geometry()
        self.assertIsInstance(geometry, Polygon)
        self.assertEqual(geometry.bounds, (-10, -5, 10, 5))

    def test_to_geojson(self):
        bbox = boundingbox(-10, -5, 10, 5)
        geojson = bbox.to_geojson()
        self.assertIn("type", geojson)
        self.assertIn("coordinates", geojson)

    def test_transform_to_crs(self):
        bbox = boundingbox(-10, -5, 10, 5, crs="EPSG:4326")
        transformed_bbox = bbox.transform_to_crs("EPSG:3857")
        self.assertNotEqual(bbox.min_x, transformed_bbox.min_x)
        self.assertNotEqual(bbox.min_y, transformed_bbox.min_y)
        self.assertNotEqual(bbox.max_x, transformed_bbox.max_x)
        self.assertNotEqual(bbox.max_y, transformed_bbox.max_y)
        self.assertEqual(transformed_bbox.crs, "EPSG:3857")

    def test_get_bounding_box_from_coordinates(self):
        bbox = boundingbox()
        result = bbox.get_bounding_box(
            query=None,
            method="from_coordinates",
            min_x=-10,
            min_y=-5,
            max_x=10,
            max_y=5
        )
        self.assertEqual(result.min_x, -10)
        self.assertEqual(result.min_y, -5)
        self.assertEqual(result.max_x, 10)
        self.assertEqual(result.max_y, 5)

    def test_get_bounding_box_from_center_radius(self):
        bbox = boundingbox()
        result = bbox.get_bounding_box(
            query="New York",
            method="from_center_radius",
            radius_km=10,
            is_address=True
        )
        self.assertIsNotNone(result)
        self.assertIsInstance(result.polygon, Polygon)

if __name__ == "__main__":
    unittest.main()