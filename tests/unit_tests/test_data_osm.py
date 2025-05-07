import pytest
from unittest.mock import patch, MagicMock
import geopandas as gpd
from shapely.geometry import Point, Polygon
from greento.data.osm import osm
from greento.boundingbox import boundingbox

@pytest.fixture
def osm_downloader():
    """Fixture per creare un'istanza di osm."""
    return osm()

@pytest.fixture
def bounding_box():
    """Fixture per creare un bounding box."""
    return boundingbox(min_x=0, min_y=0, max_x=1, max_y=1)

@patch("greento.data.osm.ox.features_from_polygon")
def test_get_data_success(mock_features_from_polygon, osm_downloader, bounding_box):
    """Test get_data con dati OSM validi."""
    mock_features = gpd.GeoDataFrame({
        'geometry': [Point(0, 0), Point(1, 1), Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])],
        'attribute': ['natural', 'landuse', 'building']
    }, crs="EPSG:4326")
    mock_features_from_polygon.return_value = mock_features

    nodes, edges = osm_downloader.get_data(bounding_box)

    assert not nodes.empty
    assert not edges.empty
    assert len(nodes) == 2
    assert len(edges) == 1
    mock_features_from_polygon.assert_called_once()

@patch("greento.data.osm.ox.features_from_polygon")
def test_get_data_empty(mock_features_from_polygon, osm_downloader, bounding_box):
    """Test get_data con dati OSM vuoti."""
    mock_features = gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
    mock_features_from_polygon.return_value = mock_features

    nodes, edges = osm_downloader.get_data(bounding_box)

    assert nodes.empty
    assert edges.empty
    mock_features_from_polygon.assert_called_once()

@patch("greento.data.osm.ox.features_from_polygon")
def test_get_data_exception(mock_features_from_polygon, osm_downloader, bounding_box):
    """Test get_data quando si verifica un'eccezione."""
    mock_features_from_polygon.side_effect = Exception("Mocked exception")

    with pytest.raises(ValueError, match="Error during OSM data download"):
        osm_downloader.get_data(bounding_box)

    mock_features_from_polygon.assert_called_once()