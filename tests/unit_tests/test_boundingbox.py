import pytest
from greento.boundingbox import boundingbox
from shapely.geometry import Polygon

def test_from_coordinates():
    bbox = boundingbox()._boundingbox__from_coordinates(-10, -5, 10, 5)
    assert bbox.min_x == -10
    assert bbox.min_y == -5
    assert bbox.max_x == 10
    assert bbox.max_y == 5
    assert isinstance(bbox.polygon, Polygon)

def test_from_center_radius():
    bbox = boundingbox()._boundingbox__from_center_radius(0, 0, 10)
    assert pytest.approx(bbox.min_x, 0.01) == -0.09
    assert pytest.approx(bbox.min_y, 0.01) == -0.09
    assert pytest.approx(bbox.max_x, 0.01) == 0.09
    assert pytest.approx(bbox.max_y, 0.01) == 0.09
    assert isinstance(bbox.polygon, Polygon)

def test_from_geojson():
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
    assert bbox.min_x == -10
    assert bbox.min_y == -5
    assert bbox.max_x == 10
    assert bbox.max_y == 5
    assert isinstance(bbox.polygon, Polygon)

def test_to_geometry():
    bbox = boundingbox(-10, -5, 10, 5)
    geometry = bbox.to_geometry()
    assert isinstance(geometry, Polygon)
    assert geometry.bounds == (-10, -5, 10, 5)

def test_to_geojson():
    bbox = boundingbox(-10, -5, 10, 5)
    geojson = bbox.to_geojson()
    assert "type" in geojson
    assert "coordinates" in geojson

def test_transform_to_crs():
    bbox = boundingbox(-10, -5, 10, 5, crs="EPSG:4326")
    transformed_bbox = bbox.transform_to_crs("EPSG:3857")
    assert bbox.min_x != transformed_bbox.min_x
    assert bbox.min_y != transformed_bbox.min_y
    assert bbox.max_x != transformed_bbox.max_x
    assert bbox.max_y != transformed_bbox.max_y
    assert transformed_bbox.crs == "EPSG:3857"

def test_get_bounding_box_from_coordinates():
    bbox = boundingbox()
    result = bbox.get_bounding_box(
        query=None,
        method="from_coordinates",
        min_x=-10,
        min_y=-5,
        max_x=10,
        max_y=5
    )
    assert result.min_x == -10
    assert result.min_y == -5
    assert result.max_x == 10
    assert result.max_y == 5

def test_get_bounding_box_from_center_radius():
    bbox = boundingbox()
    result = bbox.get_bounding_box(
        query="New York",
        method="from_center_radius",
        radius_km=10,
        is_address=True
    )
    assert result is not None
    assert isinstance(result.polygon, Polygon)